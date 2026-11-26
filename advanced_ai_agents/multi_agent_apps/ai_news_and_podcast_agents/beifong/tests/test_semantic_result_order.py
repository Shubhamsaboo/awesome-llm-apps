import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
agent = types.ModuleType("agno.agent")
agent.Agent = object
openai = types.ModuleType("openai")
openai.OpenAI = object
keys = types.ModuleType("utils.load_api_keys")
keys.load_api_key = lambda *args: None
with patch.dict(sys.modules, {"agno.agent": agent, "openai": openai, "faiss": types.ModuleType("faiss"),
                              "utils.load_api_keys": keys}):
    spec = importlib.util.spec_from_file_location("embedding_search_under_test", ROOT / "tools/embedding_search.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


class SemanticResultOrderTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.db = str(Path(self.directory.name) / "articles.db")
        with sqlite3.connect(self.db) as conn:
            conn.executescript("""
                CREATE TABLE crawled_articles (id INTEGER PRIMARY KEY, title TEXT, url TEXT, published_date TEXT,
                    summary TEXT, source_id INTEGER, feed_id INTEGER, content TEXT);
                INSERT INTO crawled_articles VALUES
                    (10, 'Second', 'https://example.test/10', '2026-11-26', 'B', 1, 1, 'B'),
                    (20, 'Third', 'https://example.test/20', '2026-11-26', 'C', 1, 1, 'C'),
                    (30, 'Best', 'https://example.test/30', '2026-11-26', 'A', 1, 1, 'A');
            """)

    def search(self, ids):
        index = types.SimpleNamespace(search=lambda *args: (
            np.array([[0.1, 0.2, 0.3]], dtype=np.float32), np.array([[0, 1, 2]])
        ))
        with patch.multiple(module,
            get_tracking_db_path=lambda: self.db,
            get_faiss_db_path=lambda: (self.db, self.db),
            generate_query_embedding=lambda prompt: ([1.0, 0.0], None),
            load_faiss_index=lambda path: (index, None),
            load_id_mapping=lambda path: (ids, None),
            get_source_names=lambda ids: {},
        ):
            response = module.embedding_search(None, "news")
        return json.loads(response.split("results: ", 1)[1])

    def test_database_order_does_not_replace_similarity_order(self):
        results = self.search([30, 10, 20])
        self.assertEqual([item["id"] for item in results], [30, 10, 20])
        self.assertGreater(results[0]["similarity"], results[1]["similarity"])
        self.assertGreater(results[1]["similarity"], results[2]["similarity"])

    def test_removed_articles_do_not_displace_surviving_matches(self):
        results = self.search([30, 999, 10])
        self.assertEqual([item["id"] for item in results], [30, 10])

    def test_duplicate_index_entries_produce_one_article(self):
        results = self.search([30, 30, 10])
        self.assertEqual([item["id"] for item in results], [30, 10])


if __name__ == "__main__":
    unittest.main()
