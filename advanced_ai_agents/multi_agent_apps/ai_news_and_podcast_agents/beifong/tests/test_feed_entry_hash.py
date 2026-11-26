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


class FeedEntryHashTests(unittest.TestCase):
    def test_replacement_article_with_same_title_and_date_changes_hash(self):
        first = parser.parse_feed_entries([{"id": "urn:1", "title": "Update", "published": "2026-11-26"}])
        replacement = parser.parse_feed_entries([{"id": "urn:2", "title": "Update", "published": "2026-11-26"}])
        self.assertNotEqual(parser.get_hash(first), parser.get_hash(replacement))

    def test_field_boundaries_do_not_collide(self):
        first = [{"entry_id": "same", "title": "abc", "published_date": "def"}]
        second = [{"entry_id": "same", "title": "ab", "published_date": "cdef"}]
        self.assertNotEqual(parser.get_hash(first), parser.get_hash(second))

    def test_same_parsed_entries_have_stable_hash(self):
        entries = [{"entry_id": "urn:é", "title": "更新", "published_date": "2026-11-26"}]
        self.assertEqual(parser.get_hash(entries), parser.get_hash([dict(entries[0])]))
        self.assertEqual(parser.get_hash([]), parser.get_hash([]))


if __name__ == "__main__":
    unittest.main()
