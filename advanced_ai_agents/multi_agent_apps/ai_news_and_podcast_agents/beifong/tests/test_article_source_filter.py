import importlib.util
from pathlib import Path
import sqlite3
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
database_module = types.ModuleType("services.db_service")
database_module.tracking_db = database_module.sources_db = None
with patch.dict(sys.modules, {"services.db_service": database_module}):
    spec = importlib.util.spec_from_file_location("article_service_under_test", ROOT / "services/article_service.py")
    service_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(service_module)


class SQLiteDatabase:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row

    async def execute_query(self, query, params=(), fetch=False, fetch_one=False):
        cursor = self.conn.execute(query, params)
        if fetch_one:
            row = cursor.fetchone()
            return dict(row) if row else None
        return [dict(row) for row in cursor.fetchall()]


class ArticleServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.sources = SQLiteDatabase()
        self.tracking = SQLiteDatabase()
        self.addCleanup(self.sources.conn.close)
        self.addCleanup(self.tracking.conn.close)
        self.sources.conn.executescript("""
            CREATE TABLE sources (id INTEGER PRIMARY KEY, name TEXT);
            CREATE TABLE source_feeds (id INTEGER PRIMARY KEY, source_id INTEGER);
            INSERT INTO sources VALUES (1, 'Daily'), (2, 'Empty source');
            INSERT INTO source_feeds VALUES (10, 1);
        """)
        self.tracking.conn.executescript("""
            CREATE TABLE crawled_articles (id INTEGER PRIMARY KEY, title TEXT, url TEXT,
                published_date TEXT, summary TEXT, feed_id INTEGER, processed INTEGER, ai_status TEXT);
            CREATE TABLE article_categories (article_id INTEGER, category_name TEXT);
            INSERT INTO crawled_articles VALUES
                (1, 'Morning', 'https://example.test/1', '2026-11-26T00:00:00', 'Summary', 10, 1, 'success'),
                (2, 'Evening', 'https://example.test/2', '2026-11-26T23:59:59', 'Summary', 10, 1, 'success'),
                (3, 'Next day', 'https://example.test/3', '2026-11-27T00:00:00', 'Summary', 20, 1, 'success');
        """)
        self.service = service_module.ArticleService()
        self.patch = patch.multiple(service_module, sources_db=self.sources, tracking_db=self.tracking)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    async def test_unknown_source_has_no_articles(self):
        result = await self.service.get_articles(source="Missing")
        self.assertEqual(result.total, 0)
        self.assertEqual(result.items, [])
        self.assertEqual(result.total_pages, 0)
        self.assertFalse(result.has_next)

    async def test_source_without_feeds_has_no_articles(self):
        result = await self.service.get_articles(source="Empty source")
        self.assertEqual(result.total, 0)
        self.assertEqual(result.items, [])

    async def test_known_source_and_omitted_filter_keep_existing_behavior(self):
        result = await self.service.get_articles(source="Daily", per_page=1)
        self.assertEqual(result.total, 2)
        self.assertEqual([item.id for item in result.items], [2])
        self.assertTrue(result.has_next)
        all_articles = await self.service.get_articles()
        self.assertEqual(all_articles.total, 3)


if __name__ == "__main__":
    unittest.main()
