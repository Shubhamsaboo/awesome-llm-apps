import json
import sqlite3
import tempfile
import traceback
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from x_twitter_scraper import XTwitterScraperError
from x_twitter_scraper.types.shared.content_disclosure import Advertising, ContentDisclosure
from x_twitter_scraper.types.shared.search_tweet import SearchTweet
from x_twitter_scraper.types.shared.tweet_media import TweetMedia
from x_twitter_scraper.types.shared.user_profile import UserProfile

import processors.x_scraper_processor as processor
import tools.social.x_scraper as browser_scraper
from processors.x_scraper_processor import get_x_backend, get_xquik_max_pages
from tools.social.xquik_scraper import crawl_xquik_timeline, xquik_tweet_to_post


def tweet(post_id, text="A post", paid=False):
    return SimpleNamespace(
        id=post_id,
        text=text,
        url=None,
        created_at="2026-08-18T08:00:00Z",
        reply_count=2,
        retweet_count=3,
        like_count=5,
        bookmark_count=7,
        view_count=11,
        author=SimpleNamespace(
            username="researcher",
            name="Researcher",
            profile_picture="https://pbs.twimg.com/profile.jpg",
        ),
        media=[
            SimpleNamespace(
                type="photo",
                media_url="https://pbs.twimg.com/media/photo.jpg",
            ),
            SimpleNamespace(
                type="video",
                media_url="https://pbs.twimg.com/media/video.jpg",
            ),
        ],
        content_disclosure=SimpleNamespace(advertising=SimpleNamespace(is_paid_promotion=paid)),
    )


class FakeXResource:
    def __init__(self, responses=None, error=None):
        self.responses = list(responses or [])
        self.error = error
        self.calls = []

    def get_home_timeline(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.responses.pop(0)


class FakeClient:
    def __init__(self, resource):
        self.x = resource
        self.closed = False

    def close(self):
        self.closed = True


class XquikScraperTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "posts.db"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_maps_typed_tweet_to_existing_post_schema(self):
        typed_tweet = SearchTweet(
            id="123",
            text="Thanks @alice and @alice for the update",
            bookmarkCount=7,
            likeCount=5,
            quoteCount=0,
            replyCount=2,
            retweetCount=3,
            viewCount=11,
            author=UserProfile(
                id="user-1",
                username="researcher",
                name="Researcher",
                profilePicture="https://pbs.twimg.com/profile.jpg",
            ),
            media=[
                TweetMedia(
                    type="photo",
                    mediaUrl="https://pbs.twimg.com/media/photo.jpg",
                    url="https://x.com/researcher/status/123/photo/1",
                ),
                TweetMedia(
                    type="video",
                    mediaUrl="https://pbs.twimg.com/media/video.jpg",
                    url="https://x.com/researcher/status/123/video/1",
                ),
            ],
            contentDisclosure=ContentDisclosure(advertising=Advertising(isPaidPromotion=True)),
        )
        post = xquik_tweet_to_post(typed_tweet)

        self.assertEqual(post["post_id"], "123")
        self.assertEqual(post["post_url"], "https://x.com/researcher/status/123")
        self.assertEqual(post["user_handle"], "@researcher")
        self.assertEqual(post["post_mentions"], "@alice")
        self.assertEqual(post["engagement_view_count"], 11)
        self.assertEqual(
            post["media"],
            [
                {"type": "image", "url": "https://pbs.twimg.com/media/photo.jpg"},
                {"type": "video", "url": "https://pbs.twimg.com/media/video.jpg"},
            ],
        )
        self.assertTrue(post["is_ad"])

    def test_maps_incomplete_dictionary_without_fabricating_author_or_media(self):
        post = xquik_tweet_to_post(
            {
                "id": "124",
                "text": "No author metadata",
                "author": {},
                "media": [{"type": "photo"}],
            }
        )

        self.assertEqual(post["post_url"], "https://x.com/i/web/status/124")
        self.assertIsNone(post["user_handle"])
        self.assertEqual(post["media"], [])
        self.assertFalse(post["is_ad"])

    def test_paginates_deduplicates_stores_and_analyzes_tweets(self):
        first = tweet("101", text="First @source")
        duplicate = tweet("101", text="First @source")
        second = tweet("102", text="Second")
        promoted = tweet("999", paid=True)
        resource = FakeXResource(
            responses=[
                SimpleNamespace(
                    tweets=[first, promoted],
                    has_next_page=True,
                    next_cursor="cursor-2",
                ),
                SimpleNamespace(
                    tweets=[duplicate, second],
                    has_next_page=False,
                    next_cursor="",
                ),
            ]
        )

        def analyze(posts):
            return [
                {
                    "post_id": post["post_id"],
                    "sentiment": "neutral",
                    "categories": ["news"],
                    "tags": ["source"],
                    "reasoning": "Test analysis",
                }
                for post in posts
            ]

        post_count = crawl_xquik_timeline(
            db_file=self.db_path,
            api_key="test-key",
            max_pages=2,
            client=FakeClient(resource),
            analyze_posts=analyze,
        )

        self.assertEqual(post_count, 2)
        self.assertEqual(resource.calls, [{}, {"cursor": "cursor-2"}])
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM posts ORDER BY post_id").fetchall()
        self.assertEqual([row["post_id"] for row in rows], ["101", "102"])
        self.assertEqual(rows[0]["sentiment"], "neutral")
        self.assertEqual(json.loads(rows[0]["categories"]), ["news"])
        self.assertEqual(json.loads(rows[0]["media"])[0]["type"], "image")
        self.assertEqual(rows[0]["engagement_like_count"], 5)

    def test_browser_backend_uses_shared_deduplicating_ingestion(self):
        class FakeArticle:
            def query_selector(self, _selector):
                return None

            def evaluate(self, _script):
                return "<article>post</article>"

        class FakePage:
            def __init__(self):
                self.visited = None

            def goto(self, url):
                self.visited = url

            def query_selector_all(self, _selector):
                return [FakeArticle()]

            def evaluate(self, _script):
                return None

        page = FakePage()

        @contextmanager
        def browser_context():
            yield None, page

        def analyze(posts):
            return [
                {
                    "post_id": post["post_id"],
                    "sentiment": "neutral",
                    "categories": [],
                    "tags": [],
                    "reasoning": "Test analysis",
                }
                for post in posts
            ]

        with (
            mock.patch.object(browser_scraper, "create_browser_context", return_value=browser_context()),
            mock.patch.object(browser_scraper, "x_post_extractor", return_value=xquik_tweet_to_post(tweet("105"))),
            mock.patch.object(browser_scraper, "MAX_SCROLLS", 2),
            mock.patch.object(browser_scraper.time, "sleep"),
        ):
            post_count = browser_scraper.crawl_x_profile(
                "researcher",
                db_file=self.db_path,
                analyze_posts=analyze,
            )

        self.assertEqual(page.visited, "https://x.com/researcher")
        self.assertEqual(post_count, 1)
        with sqlite3.connect(self.db_path) as conn:
            stored_count = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
        self.assertEqual(stored_count, 1)

    def test_requires_credentials_and_bounds_paid_pagination(self):
        with mock.patch.dict("os.environ", {}, clear=True), self.assertRaisesRegex(ValueError, "XQUIK_API_KEY"):
            crawl_xquik_timeline(
                db_file=self.db_path,
                api_key="",
                client=FakeClient(FakeXResource()),
            )
        with self.assertRaisesRegex(ValueError, "between 1 and 5"):
            crawl_xquik_timeline(
                db_file=self.db_path,
                api_key="test-key",
                max_pages=6,
                client=FakeClient(FakeXResource()),
            )

    def test_validates_backend_configuration(self):
        self.assertEqual(get_x_backend({}), "browser")
        self.assertEqual(get_x_backend({"X_SOCIAL_BACKEND": " XQUIK "}), "xquik")
        self.assertEqual(get_xquik_max_pages({}), 1)
        self.assertEqual(get_xquik_max_pages({"XQUIK_MAX_PAGES": "5"}), 5)
        with self.assertRaisesRegex(ValueError, "browser or xquik"):
            get_x_backend({"X_SOCIAL_BACKEND": "other"})
        with self.assertRaisesRegex(ValueError, "must be an integer"):
            get_xquik_max_pages({"XQUIK_MAX_PAGES": "many"})

    def test_closes_sdk_client_and_retries_failed_analysis(self):
        resource = FakeXResource(
            responses=[
                SimpleNamespace(
                    tweets=[tweet("103")],
                    has_next_page=False,
                    next_cursor="",
                )
            ]
        )
        created_client = FakeClient(resource)

        def client_factory(api_key):
            self.assertEqual(api_key, "test-key")
            return created_client

        def failed_analysis(_posts):
            raise RuntimeError("analysis unavailable")

        with self.assertRaisesRegex(RuntimeError, "will be retried"):
            crawl_xquik_timeline(
                db_file=self.db_path,
                api_key="test-key",
                client_factory=client_factory,
                analyze_posts=failed_analysis,
            )

        self.assertTrue(created_client.closed)
        with sqlite3.connect(self.db_path) as conn:
            self.assertIsNone(conn.execute("SELECT sentiment FROM posts WHERE post_id = '103'").fetchone()[0])

        retry_resource = FakeXResource(
            responses=[
                SimpleNamespace(
                    tweets=[tweet("103")],
                    has_next_page=False,
                    next_cursor="",
                )
            ]
        )
        crawl_xquik_timeline(
            db_file=self.db_path,
            api_key="test-key",
            client=FakeClient(retry_resource),
            analyze_posts=lambda posts: [
                {
                    "post_id": post["post_id"],
                    "sentiment": "neutral",
                    "categories": [],
                    "tags": [],
                    "reasoning": "Recovered",
                }
                for post in posts
            ],
        )
        with sqlite3.connect(self.db_path) as conn:
            self.assertEqual(
                conn.execute("SELECT sentiment FROM posts WHERE post_id = '103'").fetchone()[0],
                "neutral",
            )

    def test_closes_owned_sdk_client_when_database_initialization_fails(self):
        created_client = FakeClient(FakeXResource())

        with (
            mock.patch(
                "tools.social.xquik_scraper.create_connection",
                side_effect=sqlite3.OperationalError("database unavailable"),
            ),
            self.assertRaisesRegex(sqlite3.OperationalError, "database unavailable"),
        ):
            crawl_xquik_timeline(
                db_file=self.db_path,
                api_key="test-key",
                client_factory=lambda api_key: created_client,
                analyze_posts=lambda posts: [],
            )

        self.assertTrue(created_client.closed)

    def test_rejects_repeated_pagination_cursor(self):
        resource = FakeXResource(
            responses=[
                SimpleNamespace(tweets=[], has_next_page=True, next_cursor="repeat"),
                SimpleNamespace(tweets=[], has_next_page=True, next_cursor="repeat"),
            ]
        )

        with self.assertRaisesRegex(RuntimeError, "invalid pagination cursor"):
            crawl_xquik_timeline(
                db_file=self.db_path,
                api_key="test-key",
                max_pages=2,
                client=FakeClient(resource),
                analyze_posts=lambda posts: [],
            )

    def test_processor_selects_xquik_backend(self):
        with (
            mock.patch.dict(
                "os.environ",
                {"X_SOCIAL_BACKEND": "xquik", "XQUIK_MAX_PAGES": "2"},
                clear=True,
            ),
            mock.patch.object(processor, "get_social_media_db_path", return_value="posts.db"),
            mock.patch.object(processor, "crawl_xquik_timeline", return_value=3) as crawl,
            mock.patch("builtins.print"),
        ):
            processor.main()

        crawl.assert_called_once_with(db_file="posts.db", max_pages=2)

    def test_redacts_upstream_error_details(self):
        resource = FakeXResource(error=XTwitterScraperError("upstream leaked test-key"))

        with self.assertRaisesRegex(RuntimeError, "Check the API key") as raised:
            crawl_xquik_timeline(
                db_file=self.db_path,
                api_key="test-key",
                client=FakeClient(resource),
                analyze_posts=lambda posts: [],
            )

        self.assertNotIn("test-key", str(raised.exception))
        self.assertNotIn("test-key", "".join(traceback.format_exception(raised.exception)))

    def test_preserves_non_sdk_client_errors(self):
        resource = FakeXResource(error=ValueError("invalid injected client"))

        with self.assertRaisesRegex(ValueError, "invalid injected client"):
            crawl_xquik_timeline(
                db_file=self.db_path,
                api_key="test-key",
                client=FakeClient(resource),
                analyze_posts=lambda posts: [],
            )


if __name__ == "__main__":
    unittest.main()
