"""Run from beifong with: python -m unittest tests.test_feed_and_article_correctness."""

import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import faiss
import feedparser
import numpy as np

from db.feeds import store_feed_entries
from services import article_service
from tools import embedding_search
from utils.rss_feed_parser import get_hash, parse_feed_entries


class FeedTests(unittest.TestCase):
    def test_atom_content_can_be_stored_in_sqlite(self):
        feed = feedparser.parse('''
            <feed xmlns="http://www.w3.org/2005/Atom">
              <title>News</title><id>urn:news</id><updated>2026-01-01T00:00:00Z</updated>
              <entry><id>urn:article:1</id><title>Article</title>
                <updated>2026-01-01T00:00:00Z</updated>
                <content type="text">Article body</content>
              </entry>
            </feed>''')
        entries = parse_feed_entries(feed.entries)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "feed.db"
            with sqlite3.connect(path) as db:
                db.execute('''CREATE TABLE feed_entries (
                    feed_id, source_id, entry_id, title, link, published_date, content TEXT, summary
                )''')
            self.assertEqual(store_feed_entries(path, 1, 1, entries), 1)
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute("SELECT content FROM feed_entries").fetchone(), ("Article body",))

    def test_content_parts_and_rss_fallback(self):
        for entry, expected in [
            ({"content": [{"value": "One"}, {"value": "Two"}]}, "One\nTwo"),
            ({"description": "RSS body"}, "RSS body"),
            ({"content": [], "description": "Fallback"}, "Fallback"),
        ]:
            with self.subTest(entry=entry):
                self.assertEqual(parse_feed_entries([entry])[0]["content"], expected)

    def test_fingerprint_tracks_parsed_entry_ids(self):
        entry = {"id": "first", "title": "Same title", "published": "2026-01-01"}
        before = parse_feed_entries([entry])
        after = parse_feed_entries([dict(entry, id="second")])
        self.assertNotEqual(get_hash(before), get_hash(after))
        self.assertEqual(get_hash(before), get_hash(parse_feed_entries([entry])))

    def test_fingerprint_preserves_field_boundaries(self):
        self.assertNotEqual(
            get_hash([{"entry_id": "same", "title": "a", "published_date": "bc"}]),
            get_hash([{"entry_id": "same", "title": "ab", "published_date": "c"}]),
        )


class ArticleTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.sources = self.directory / "sources.db"
        self.tracking = self.directory / "tracking.db"
        with sqlite3.connect(self.sources) as db:
            db.executescript('''
                CREATE TABLE sources (id INTEGER PRIMARY KEY, name TEXT);
                CREATE TABLE source_feeds (id INTEGER PRIMARY KEY, source_id INTEGER);
                INSERT INTO sources VALUES (1, 'News'), (2, 'Empty');
                INSERT INTO source_feeds VALUES (10, 1);
            ''')
        with sqlite3.connect(self.tracking) as db:
            db.executescript('''
                CREATE TABLE crawled_articles (
                    id INTEGER PRIMARY KEY, title TEXT, url TEXT, published_date TEXT,
                    summary TEXT, feed_id INTEGER, processed INTEGER, ai_status TEXT,
                    content TEXT, source_id INTEGER
                );
                CREATE TABLE article_categories (article_id INTEGER, category_name TEXT);
            ''')
            db.executemany(
                "INSERT INTO crawled_articles VALUES (?, ?, ?, ?, '', 10, 1, 'success', '', 1)",
                [(i, f"Article {i}", f"https://example.com/{i}", date) for i, date in enumerate([
                    "2026-01-01T00:00:00", "2026-01-01T12:00:00",
                    "2026-01-01T23:59:59", "2026-01-02T00:00:00",
                ], 1)],
            )
        self.enterContext(patch.object(article_service.sources_db, "db_path", str(self.sources)))
        self.enterContext(patch.object(article_service.tracking_db, "db_path", str(self.tracking)))
        self.service = article_service.ArticleService()

    async def test_unmatched_source_filters_stay_empty(self):
        for source in ("Unknown", "Empty"):
            with self.subTest(source=source):
                result = await self.service.get_articles(source=source, per_page=1)
                self.assertEqual((result.items, result.total, result.total_pages, result.has_next), ([], 0, 0, False))
        self.assertEqual((await self.service.get_articles(source="News")).total, 4)
        self.assertEqual((await self.service.get_articles()).total, 4)

    async def test_date_only_end_includes_the_whole_day(self):
        result = await self.service.get_articles(date_from="2026-01-01", date_to="2026-01-01", per_page=2)
        self.assertEqual([item.id for item in result.items], [3, 2])
        self.assertEqual((result.total, result.total_pages, result.has_next), (3, 2, True))
        page = await self.service.get_articles(date_to="2026-01-01", page=2, per_page=2)
        self.assertEqual([item.id for item in page.items], [1])

    async def test_timestamp_end_retains_its_exact_cutoff(self):
        result = await self.service.get_articles(date_to="2026-01-01T12:00:00")
        self.assertEqual([item.id for item in result.items], [2, 1])
        self.assertEqual(result.total, 2)

    def test_semantic_results_keep_vector_order(self):
        index = faiss.IndexFlatL2(2)
        index.add(np.array([[0.99, 0.1], [1, 0], [1, 0], [1, 0]], dtype=np.float32))
        index_path, mapping_path = self.directory / "index.faiss", self.directory / "ids.npy"
        faiss.write_index(index, str(index_path))
        np.save(mapping_path, np.array([1, 2, 2, 99]))
        with (
            patch.object(embedding_search, "get_tracking_db_path", return_value=str(self.tracking)),
            patch.object(embedding_search, "get_sources_db_path", return_value=str(self.sources)),
            patch.object(embedding_search, "get_faiss_db_path", return_value=(str(index_path), str(mapping_path))),
            patch.object(embedding_search, "generate_query_embedding", return_value=([1.0, 0.0], None)),
        ):
            output = embedding_search.embedding_search(None, "news")
        results = json.loads(output.split("results: ", 1)[1])
        self.assertEqual([item["id"] for item in results], [2, 1])
        self.assertGreater(results[0]["similarity"], results[1]["similarity"])
        self.assertEqual(results[0]["source_name"], "News")


if __name__ == "__main__":
    unittest.main()
