"""Exercise the research workflow without making paid model requests."""

import ast
import asyncio
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, MagicMock


class ResearchExecutionTests(unittest.IsolatedAsyncioTestCase):
    async def run_workflow(self, queries):
        source = Path(__file__).with_name("research_agent.py")
        tree = ast.parse(source.read_text())
        workflow = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef)
                        and node.name == "run_research")
        ui = MagicMock()
        ui.session_state = SimpleNamespace(conversation_id="test")
        plan = SimpleNamespace(topic="ocean energy", search_queries=queries,
                               focus_areas=["feasibility"])
        planning = SimpleNamespace(final_output=plan,
                                   to_input_list=lambda: [{"role": "user", "content": "ocean energy"}])
        editor_inputs = []
        searches = []

        async def run(agent, prompt):
            if agent == "planner":
                return planning
            if agent == "researcher":
                await asyncio.sleep(0)
                searches.append(prompt)
                return SimpleNamespace(final_output=f"Evidence for {prompt}")
            editor_inputs.append(prompt)
            return SimpleNamespace(final_output=SimpleNamespace(report="Completed report"))

        namespace = {
            "st": ui, "tab1": MagicMock(), "trace": lambda *a, **k: nullcontext(),
            "Runner": SimpleNamespace(run=run), "triage_agent": "planner",
            "research_agent": "researcher", "editor_agent": "editor",
            # Skip the old idle polling while preserving real concurrent execution.
            "asyncio": SimpleNamespace(gather=asyncio.gather, sleep=AsyncMock()),
        }
        exec(compile(ast.Module(body=[workflow], type_ignores=[]), str(source), "exec"), namespace)
        await namespace["run_research"]("ocean energy")
        return searches, editor_inputs, ui.session_state

    async def test_editor_receives_results_from_every_planned_search(self):
        queries = ["tidal energy cost", "wave energy reliability"]
        searches, editor_inputs, state = await self.run_workflow(queries)
        self.assertCountEqual(searches, queries)
        self.assertEqual(len(editor_inputs), 1)
        findings = "\n".join(item["content"] for item in editor_inputs[0])
        for query in queries:
            self.assertIn(f"Evidence for {query}", findings)
        self.assertTrue(state.research_done)
        self.assertEqual(state.report_result.report, "Completed report")

    async def test_empty_plan_still_researches_original_topic(self):
        searches, editor_inputs, _ = await self.run_workflow([])
        self.assertEqual(searches, ["ocean energy"])
        self.assertIn("Evidence for ocean energy", editor_inputs[0][-1]["content"])


if __name__ == "__main__":
    unittest.main()
