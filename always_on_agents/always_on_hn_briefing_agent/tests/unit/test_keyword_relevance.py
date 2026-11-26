import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "hn_scout_keyword_test", Path(__file__).resolve().parents[2] / "scout.py"
)
scout = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = scout
spec.loader.exec_module(scout)


class KeywordRelevanceTests(unittest.TestCase):
    def test_unrelated_substrings_do_not_enter_the_brief(self):
        stories = [
            scout.Story("Decoding a reagent label", "https://example.com/1", "hn:1", 500, 100, 1, ""),
            scout.Story("MCP tools for agents", "https://example.com/2", "hn:2", 20, 5, 2, ""),
        ]
        with patch.object(scout, "fetch_hn_front_page", return_value=stories):
            assert scout.curate_stories(live=True) == [stories[1]]


    def test_plural_and_punctuated_keywords_keep_their_signal(self):
        assert scout._keyword_hits("LLMs, tools, frameworks and workflows") == {
            "llm", "tool", "framework", "workflow"
        }
        assert scout._keyword_hits("An agent and multiple agents") == {"agent"}


if __name__ == "__main__":
    unittest.main()
