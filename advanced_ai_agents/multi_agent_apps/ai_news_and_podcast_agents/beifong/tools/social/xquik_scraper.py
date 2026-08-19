import os
import re
from contextlib import ExitStack

from x_twitter_scraper import XTwitterScraper, XTwitterScraperError

from tools.social.db import create_connection, setup_database
from tools.social.x_ingestion import PostIngestor

MAX_TIMELINE_PAGES = 5


def _attribute(value, name, default=None):
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _is_paid_promotion(tweet):
    disclosure = _attribute(tweet, "content_disclosure")
    advertising = _attribute(disclosure, "advertising") if disclosure else None
    return bool(_attribute(advertising, "is_paid_promotion", False))


def _media_items(tweet):
    items = []
    for media in _attribute(tweet, "media", None) or []:
        media_type = _attribute(media, "type")
        media_url = _attribute(media, "media_url")
        if not media_type or not media_url:
            continue
        items.append(
            {
                "type": "image" if media_type == "photo" else "video",
                "url": media_url,
            }
        )
    return items


def xquik_tweet_to_post(tweet):
    post_id = str(_attribute(tweet, "id", "")).strip()
    text = _attribute(tweet, "text", "") or ""
    author = _attribute(tweet, "author")
    username = (_attribute(author, "username", "") or "").lstrip("@")
    post_url = _attribute(tweet, "url")
    if not post_url and post_id:
        post_url = f"https://x.com/{username}/status/{post_id}" if username else f"https://x.com/i/web/status/{post_id}"

    mentions = list(dict.fromkeys(re.findall(r"@[A-Za-z0-9_]{1,15}", text)))
    media = _media_items(tweet)
    return {
        "platform": "x.com",
        "post_id": post_id,
        "post_url": post_url,
        "post_text": text,
        "post_timestamp": _attribute(tweet, "created_at"),
        "post_mentions": ",".join(mentions) if mentions else None,
        "user_display_name": _attribute(author, "name"),
        "user_handle": f"@{username}" if username else None,
        "user_profile_pic_url": _attribute(author, "profile_picture"),
        "engagement_reply_count": _attribute(tweet, "reply_count", 0),
        "engagement_retweet_count": _attribute(tweet, "retweet_count", 0),
        "engagement_like_count": _attribute(tweet, "like_count", 0),
        "engagement_bookmark_count": _attribute(tweet, "bookmark_count", 0),
        "engagement_view_count": _attribute(tweet, "view_count", 0),
        "media": media,
        "media_count": len(media),
        "is_ad": _is_paid_promotion(tweet),
    }


def crawl_xquik_timeline(
    db_file="x_posts.db",
    api_key=None,
    max_pages=1,
    client=None,
    client_factory=XTwitterScraper,
    analyze_posts=None,
):
    if not 1 <= max_pages <= MAX_TIMELINE_PAGES:
        raise ValueError(f"max_pages must be between 1 and {MAX_TIMELINE_PAGES}")

    resolved_api_key = api_key or os.environ.get("XQUIK_API_KEY")
    if not resolved_api_key:
        raise ValueError("XQUIK_API_KEY is required when X_SOCIAL_BACKEND=xquik")

    owns_client = client is None
    if owns_client:
        client = client_factory(api_key=resolved_api_key)

    with ExitStack() as resources:
        if owns_client:
            resources.callback(client.close)
        conn = create_connection(db_file)
        resources.callback(conn.close)
        setup_database(conn)
        ingestor = PostIngestor(conn, analyze_posts=analyze_posts)
        resources.callback(ingestor.flush)
        cursor = None
        seen_cursors = set()

        for _ in range(max_pages):
            request = {"cursor": cursor} if cursor else {}
            try:
                response = client.x.get_home_timeline(**request)
            except XTwitterScraperError:
                raise RuntimeError("Xquik timeline request failed. Check the API key, connected X account, and service status.") from None

            tweets = _attribute(response, "tweets")
            if not isinstance(tweets, list):
                raise TypeError("Xquik timeline response did not contain a tweet list.")
            for tweet in tweets:
                ingestor.add(xquik_tweet_to_post(tweet))

            if not _attribute(response, "has_next_page", False):
                break
            next_cursor = _attribute(response, "next_cursor")
            if not isinstance(next_cursor, str) or not next_cursor or next_cursor in seen_cursors:
                raise RuntimeError("Xquik timeline response returned an invalid pagination cursor.")
            seen_cursors.add(next_cursor)
            cursor = next_cursor

        return ingestor.post_count
