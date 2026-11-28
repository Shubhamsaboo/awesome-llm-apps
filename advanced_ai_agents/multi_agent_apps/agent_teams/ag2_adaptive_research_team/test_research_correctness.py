"""Offline regressions for local retrieval and structured agent replies."""

import unittest
from unittest.mock import patch

import router
from tools import Chunk, Document, build_local_index, search_local


class ResearchCorrectnessTests(unittest.TestCase):
    def test_non_ascii_documents_are_retrievable(self):
        for query, text in (
            ("Москва", "Москва — столица России."),
            ("Αθήνα", "Αθήνα είναι η πρωτεύουσα της Ελλάδας."),
        ):
            with self.subTest(query=query):
                index = build_local_index([Document("cities.txt", text)])
                self.assertEqual(search_local(query, index), index)

    def test_casefold_matches_german_words(self):
        chunk = Chunk("roads.txt", 1, "Die Straße ist offen.")
        self.assertEqual(search_local("STRASSE", [chunk]), [chunk])

    def test_accented_words_do_not_match_truncated_ascii_fragments(self):
        truncated = Chunk("wrong.txt", 1, "caf")
        correct = Chunk("right.txt", 1, "Un café ouvert")
        self.assertEqual(search_local("café", [truncated, correct]), [correct])

    def test_ascii_ranking_and_punctuation_are_preserved(self):
        first = Chunk("one.txt", 1, "local retrieval")
        second = Chunk("two.txt", 1, "local files")
        self.assertEqual(search_local("LOCAL_retrieval!", [second, first]), [first, second])
        self.assertEqual(search_local("???", [first, second]), [])

    def test_trailing_object_does_not_discard_the_first_answer(self):
        text = '{"route":"web","confidence":0.9}\nMetadata: {"note":"extra"}'
        self.assertEqual(router._extract_json(text), {"route": "web", "confidence": 0.9})

    def test_prose_braces_do_not_swallow_the_result(self):
        text = (
            'Use {source} notation.\n```json\n'
            '{"evidence":[{"source":"paper","summary":"finding"}]}\n```'
        )
        self.assertEqual(
            router._extract_json(text),
            {"evidence": [{"source": "paper", "summary": "finding"}]},
        )

    def test_nested_objects_and_braces_in_strings_are_preserved(self):
        text = '{"draft_answer":"Use {x}","evidence":[{"source":"A"}]}'
        self.assertEqual(
            router._extract_json(text),
            {"draft_answer": "Use {x}", "evidence": [{"source": "A"}]},
        )
        self.assertEqual(router._extract_json("No JSON here"), {})
        self.assertEqual(router._extract_json("{broken"), {})

    def test_pipeline_preserves_route_evidence_and_verdict(self):
        replies = [
            '{"route":"web"} metadata {"ignored":true}',
            '{"evidence":[{"source":"https://example.test"}],'
            '"draft_answer":"Found"} extra {"ignored":true}',
            '{"verdict":"sufficient"} extra {"ignored":true}',
            "Final answer",
        ]
        agents = {name: name for name in ("triage", "web", "local", "verifier", "synthesizer")}
        with (
            patch.object(router, "build_agents", return_value=agents),
            patch.object(router, "run_agent", side_effect=replies),
            patch.object(router, "run_searxng", return_value=[]) as web_search,
        ):
            result = router.run_pipeline(
                "Question", [Chunk("local.txt", 1, "Unrelated notes")],
                "unused", "unused", True, "http://unused",
            )

        self.assertEqual(result["route"], "web")
        self.assertEqual(result["evidence"], [{"source": "https://example.test"}])
        self.assertEqual(result["verifier"], {"verdict": "sufficient"})
        self.assertEqual(result["final_answer"], "Final answer")
        web_search.assert_called_once_with("Question", base_url="http://unused", max_results=5)


if __name__ == "__main__":
    unittest.main()
