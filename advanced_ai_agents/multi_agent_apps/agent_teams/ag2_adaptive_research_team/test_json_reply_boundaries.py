import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
agents = types.ModuleType("agents")
agents.build_agents = lambda **kwargs: None
agents.run_agent = lambda *args: None
tools = types.ModuleType("tools")
tools.Chunk = object
tools.run_searxng = lambda *args, **kwargs: []
tools.search_local = lambda *args, **kwargs: []
with patch.dict(sys.modules, {"agents": agents, "tools": tools}):
    spec = importlib.util.spec_from_file_location("router_under_test", ROOT / "router.py")
    router = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(router)


class JsonReplyBoundaryTests(unittest.TestCase):
    def test_trailing_object_does_not_discard_the_first_answer(self):
        text = '{"route":"web","confidence":0.9}\nAdditional metadata: {"note":"extra"}'
        self.assertEqual(router._extract_json(text), {"route": "web", "confidence": 0.9})

    def test_non_json_braces_in_prose_do_not_swallow_the_result(self):
        text = 'Use {source} notation.\n```json\n{"evidence":[{"source":"paper","summary":"finding"}]}\n```'
        self.assertEqual(router._extract_json(text), {"evidence": [{"source": "paper", "summary": "finding"}]})

    def test_nested_objects_and_braces_in_strings_are_preserved(self):
        text = '{"draft_answer":"Use {x}","evidence":[{"source":"A"}]}'
        self.assertEqual(router._extract_json(text), {"draft_answer": "Use {x}", "evidence": [{"source": "A"}]})
        self.assertEqual(router._extract_json("No JSON here"), {})
        self.assertEqual(router._extract_json("{broken"), {})

    def test_pipeline_keeps_route_and_evidence_from_complete_objects(self):
        replies = [
            '{"route":"web"} metadata {"ignored":true}',
            '{"evidence":[{"source":"https://example.test"}],"draft_answer":"Found"} extra {"ignored":true}',
            '{"verdict":"sufficient"} extra {"ignored":true}',
            'Final answer',
        ]
        with patch.object(router, "build_agents", return_value={key:key for key in ["triage","web","local","verifier","synthesizer"]}), \
             patch.object(router, "run_agent", side_effect=replies):
            result = router.run_pipeline("Question", [], "unused", "unused", True, "http://unused")
        self.assertEqual(result["route"], "web")
        self.assertEqual(result["evidence"], [{"source": "https://example.test"}])
        self.assertEqual(result["verifier"], {"verdict": "sufficient"})


if __name__ == "__main__":
    unittest.main()
