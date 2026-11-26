import importlib.util
from pathlib import Path
import sqlite3
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# No network fetch is involved: these fixtures use feedparser's parsed entry shape.
with patch.dict(sys.modules, {"feedparser": types.ModuleType("feedparser")}):
    spec = importlib.util.spec_from_file_location("rss_parser_under_test", ROOT / "utils/rss_feed_parser.py")
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)

from db.feeds import store_feed_entries


class FeedContentStorageTests(unittest.TestCase):
    def test_atom_content_round_trips_through_sqlite(self):
        entries = parser.parse_feed_entries([{
            "id": "urn:article:1", "title": "A new release", "link": "https://example.test/1",
            "published": "2026-11-26T10:00:00Z",
            "content": [{"type": "text/html", "value": "<p>Release notes</p>"},
                        {"type": "text/plain", "value": "A second part"}],
        }])
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "feeds.db")
            with sqlite3.connect(path) as conn:
                conn.execute("CREATE TABLE feed_entries (feed_id, source_id, entry_id, title, link, published_date, content, summary)")
            self.assertEqual(store_feed_entries(path, 2, 3, entries), 1)
            with sqlite3.connect(path) as conn:
                self.assertEqual(conn.execute("SELECT content FROM feed_entries").fetchone()[0],
                                 "<p>Release notes</p>\nA second part")

    def test_rss_description_and_empty_content_fallback(self):
        entries = parser.parse_feed_entries([
            {"description": "RSS body"},
            {"content": [], "description": "Fallback"},
            {"content": [{"value": None}, {}], "description": "Fallback"},
            {"content": "Existing text"},
        ])
        self.assertEqual([entry["content"] for entry in entries],
                         ["RSS body", "Fallback", "Fallback", "Existing text"])


if __name__ == "__main__":
    unittest.main()
