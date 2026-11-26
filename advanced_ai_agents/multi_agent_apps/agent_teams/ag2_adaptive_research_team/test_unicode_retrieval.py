import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
experimental = types.ModuleType("autogen.tools.experimental")
experimental.SearxngSearchTool = object
with patch.dict(sys.modules, {"autogen.tools.experimental": experimental}):
    spec = importlib.util.spec_from_file_location("ag2_tools_under_test", ROOT / "tools.py")
    tools_module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = tools_module
    spec.loader.exec_module(tools_module)


class UnicodeRetrievalTests(unittest.TestCase):
    def test_cyrillic_document_is_retrievable(self):
        document = tools_module.Document("cities.txt", "Москва — столица России.")
        index = tools_module.build_local_index([document])
        self.assertEqual(tools_module.search_local("Москва", index), index)

    def test_casefold_matches_german_words(self):
        chunk = tools_module.Chunk("roads.txt", 1, "Die Straße ist offen.")
        self.assertEqual(tools_module.search_local("STRASSE", [chunk]), [chunk])

    def test_accented_words_do_not_match_truncated_ascii_fragments(self):
        truncated = tools_module.Chunk("wrong.txt", 1, "caf")
        correct = tools_module.Chunk("right.txt", 1, "Un café ouvert")
        self.assertEqual(tools_module.search_local("café", [truncated, correct]), [correct])

    def test_ascii_ranking_and_punctuation_are_preserved(self):
        first = tools_module.Chunk("one.txt", 1, "local retrieval")
        second = tools_module.Chunk("two.txt", 1, "local files")
        self.assertEqual(tools_module.search_local("LOCAL_retrieval!", [second, first]), [first, second])
        self.assertEqual(tools_module.search_local("???", [first, second]), [])


if __name__ == "__main__":
    unittest.main()
