"""Independent team/RCA UI paths, using fake model calls and a temporary trace store."""

import asyncio
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "optimizer"))

import rca_scorer
import skill_paths
import telemetry
from rca_scorer import RcaScorer, generation_cases
from routing_scorer import RoutingScorer
from skill_optimizer import SkillOptimizer, split_holdout
from streamlit.testing.v1 import AppTest

with open(skill_paths.RCA_GOLDEN) as f:
    RCA_GOLDEN = json.load(f)
with open(skill_paths.ROUTING_GOLDEN) as f:
    ROUTING_GOLDEN = json.load(f)
with open(skill_paths.RCA_RUBRIC) as f:
    RUBRIC = json.load(f)


def _detail(quality=80.0):
    return {
        "quality": quality,
        "correctness": "correct",
        "correctness_reason": "Matches the documented cause.",
        "checks": [{"id": "evidence", "question": "Enough evidence?", "passed": quality == 100}],
        "per_dimension": [],
        "grounding": {"score": 90.0, "hard_fail": False, "fabricated": [], "checks": []},
    }


MISROUTE = {"name": "n", "expected_team": "frontend", "predicted_team": "devops",
            "agent_reasoning": "r"}


class GenerationTargets(unittest.TestCase):
    def test_calibration_sample_and_target_are_separate(self):
        cases = generation_cases(RCA_GOLDEN)
        original = next(c for c in RCA_GOLDEN["cases"] if c["id"] == "aws-wrong-conclusion")
        generated = next(c for c in cases if c["id"] == original["id"])
        self.assertEqual(original["expected_correctness"], "wrong")
        self.assertEqual(generated["expected_correctness"], "correct")
        self.assertEqual(len(cases), len(RCA_GOLDEN["cases"]))
        for case in cases:
            self.assertNotIn("rca", case)
            self.assertNotIn("human_quality", case)
            self.assertIn(case["expected_correctness"], {"correct", "insufficient_evidence"})
        ticket = next(c for c in cases if c["id"] == "jira-ticket-only-no-telemetry")
        self.assertEqual(ticket["expected_correctness"], "insufficient_evidence")

    def test_writer_does_not_receive_calibration_answers(self):
        case = {
            "id": "test", "ticket": "Checkout is failing.", "true_root_cause": "SECRET CAUSE",
            "expected_correctness": "correct", "rca": "SECRET SAMPLE",
            "intake": {"user_hypothesis": "Could be the pool"},
        }
        opt = SkillOptimizer()
        with mock.patch.object(opt, "_ask", new_callable=mock.AsyncMock, return_value="fresh RCA") as writer:
            with mock.patch.object(rca_scorer, "score_rca_doc", new_callable=mock.AsyncMock,
                                   return_value=_detail()) as judge:
                result = asyncio.run(RcaScorer(RUBRIC)._score_one(opt, "skill text", case))
        prompt = writer.call_args.args[1]
        self.assertIn("Checkout is failing.", prompt)
        self.assertIn("Could be the pool", prompt)
        self.assertNotIn("SECRET", prompt)
        self.assertEqual(judge.call_args.args[-1], "SECRET CAUSE")
        self.assertEqual(result[1], "fresh RCA")


class EvaluationUI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_path = telemetry.store.path
        telemetry.init(os.path.join(self.tmp.name, "eval.db"))

    def tearDown(self):
        telemetry.store.path = self.old_path
        self.tmp.cleanup()

    def app(self):
        at = AppTest.from_file(os.path.join(ROOT, "optimizer", "app.py"), default_timeout=60).run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        return at

    def rca_app(self):
        at = self.app()
        at.text_input(key="key-value").set_value("fake-key").run()
        at.button_group(key="evaluation-mode").set_value("RCA evaluation").run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        return at

    @staticmethod
    def button(at, label):
        return next(b for b in at.button if b.label == label)

    def test_modes_load_independent_golden_sets_and_preserve_edits(self):
        at = self.app()
        scenarios = next(t for t in at.text_area if t.label == "scenarios")
        original = json.loads(scenarios.value)
        edited = json.dumps(original[:1])
        scenarios.set_value(edited).run()
        at.button_group(key="evaluation-mode").set_value("RCA evaluation").run()
        cases = json.loads(at.text_area(key="rca-cases-editor").value)
        self.assertEqual(cases, generation_cases(RCA_GOLDEN))
        self.assertNotIn("One per line", [t.label for t in at.text_area])
        self.assertTrue(self.button(at, "Generate scenarios").disabled)
        at.text_area(key="rca-cases-editor").set_value(json.dumps(cases[:1])).run()
        at.button_group(key="evaluation-mode").set_value("Team assignment").run()
        self.assertEqual(next(t.value for t in at.text_area if t.label == "scenarios"), edited)
        at.button_group(key="evaluation-mode").set_value("RCA evaluation").run()
        self.assertEqual(json.loads(at.text_area(key="rca-cases-editor").value), cases[:1])
        self.assertFalse(at.exception)

    def test_invalid_rca_data_disables_both_actions_instead_of_using_old_data(self):
        at = self.rca_app()
        self.assertFalse(self.button(at, "Evaluate skill").disabled)
        for invalid in ("{", "{}", "[]", "[1]", '[{"id": "x", "expected_correctness": "wrong"}]'):
            with self.subTest(invalid=invalid):
                at.text_area(key="rca-cases-editor").set_value(invalid).run()
                self.assertFalse(at.exception)
                self.assertTrue(at.error)
                self.assertTrue(self.button(at, "Evaluate skill").disabled)
                self.assertTrue(self.button(at, "Start optimization").disabled)

    def test_invalid_routing_data_cannot_reuse_previous_valid_scenarios(self):
        at = self.app()
        at.text_input(key="key-value").set_value("fake-key").run()
        next(t for t in at.text_area if t.label == "scenarios").set_value("{}").run()
        self.assertFalse(at.exception)
        self.assertTrue(self.button(at, "Evaluate skill").disabled)
        self.assertTrue(self.button(at, "Start optimization").disabled)

    def test_rca_evaluate_generates_reports_without_mutating_or_routing(self):
        at = self.rca_app()
        at.selectbox(key="rca-profile").set_value("curious").run()
        at.slider(key="rca-judge-runs").set_value(2).run()
        cases = generation_cases(RCA_GOLDEN)[:1]
        at.text_area(key="rca-cases-editor").set_value(json.dumps(cases)).run()

        seen = []

        async def fake_one(self_, client, skill, case):
            seen.append((self_.profile, self_.judge_runs))
            return case, "# Fresh RCA\nMissing index caused slow queries.", _detail()

        with mock.patch.object(RcaScorer, "_score_one", autospec=True,
                               side_effect=fake_one) as scorer, \
                mock.patch.object(SkillOptimizer, "_mutate") as mutator:
            self.button(at, "Evaluate skill").click().run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertEqual(scorer.call_count, 1)
        self.assertEqual(seen, [("curious", 2)])  # sidebar profile and judge runs reach the scorer
        mutator.assert_not_called()
        result = at.session_state["rca_result"]
        self.assertEqual(result["baseline_score"], 92.0)
        self.assertEqual(result["final_score"], 92.0)
        self.assertEqual(result["original_skill_md"], result["improved_skill_md"])
        self.assertEqual(result["mutation_log"], [])
        metrics = {m.label: m.value for m in at.metric}
        self.assertEqual(metrics["Correctness"], "100.0%")
        self.assertEqual(metrics["Quality"], "80.0%")
        self.assertEqual(metrics["Grounding"], "90.0%")
        self.assertTrue(any("Missing index caused slow queries." in m.value for m in at.markdown))
        self.assertTrue(any(h.value == "RCA checks still failing" for h in at.subheader))
        at.button_group(key="evaluation-mode").set_value("Team assignment").run()
        self.assertNotIn("Correctness", [m.label for m in at.metric])
        at.button_group(key="evaluation-mode").set_value("RCA evaluation").run()
        self.assertIn("Correctness", [m.label for m in at.metric])

    def test_routing_evaluate_uses_routing_scorer_without_mutation(self):
        at = self.app()
        at.text_input(key="key-value").set_value("fake-key").run()
        result = {"pass_rate": 100.0, "passed": 1, "total": 1, "per_eval": [],
                  "failures": [], "confusion": []}
        with mock.patch.object(RoutingScorer, "score", new_callable=mock.AsyncMock,
                               return_value=result) as scorer:
            with mock.patch.object(RcaScorer, "score") as rca_score:
                with mock.patch.object(SkillOptimizer, "_mutate") as mutator:
                    self.button(at, "Evaluate skill").click().run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        cases = scorer.call_args.args[2]
        self.assertEqual(len(cases), len(ROUTING_GOLDEN["scenarios"]))
        rca_score.assert_not_called()
        mutator.assert_not_called()
        self.assertEqual(at.session_state["routing_result"]["final_score"], 100.0)

    def test_rca_optimization_keeps_improved_report_and_scores(self):
        at = self.rca_app()
        at.text_area(key="rca-cases-editor").set_value(
            json.dumps(generation_cases(RCA_GOLDEN)[:1])
        ).run()
        scores = iter([80.0, 100.0])

        async def fake_one(self_, client, skill, case):
            return case, f"Report from {skill}", _detail(next(scores))

        analysis = {"mutation_strategy": "add_causal_rule", "diagnosis": "Missing mechanism",
                    "target_section": "RCA", "suggested_change": "Explain cause"}
        mutation = {"new_skill_md": "Improved skill", "description": "Explain cause", "reasoning": "r"}
        with mock.patch.object(RcaScorer, "_score_one", fake_one), \
                mock.patch.object(RcaScorer, "diagnose", new_callable=mock.AsyncMock,
                                  return_value=analysis), \
                mock.patch.object(SkillOptimizer, "_mutate", new_callable=mock.AsyncMock,
                                  return_value=mutation):
            self.button(at, "Start optimization").click().run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        result = at.session_state["rca_result"]
        self.assertEqual(result["score_history"], [92.0, 100.0])
        self.assertEqual(result["quality_pct"], 100.0)
        self.assertEqual(result["case_results"][0]["rca"], "Report from Improved skill")
        self.assertTrue(result["mutation_log"][0]["kept"])

    def test_failed_run_clears_old_result_and_surfaces_error(self):
        at = self.rca_app()
        at.session_state["rca_result"] = {"final_score": 100}
        with mock.patch.object(RcaScorer, "score", new_callable=mock.AsyncMock,
                               side_effect=RuntimeError("Judge unavailable")):
            self.button(at, "Evaluate skill").click().run()
        self.assertFalse(at.exception)
        self.assertTrue(any("Judge unavailable" in e.value for e in at.error))
        self.assertNotIn("rca_result", at.session_state)

    def test_optimization_holds_cases_out_and_flags_overfitting(self):
        at = self.app()
        at.text_input(key="key-value").set_value("fake-key").run()
        at.slider(key="holdout-pct").set_value(50).run()
        scenarios = ROUTING_GOLDEN["scenarios"]
        train_set, held_set = split_holdout(scenarios, 0.5)
        held_ids = {c["id"] for c in held_set}
        calls = []

        async def fake_score(self_, client, skill_md, cases):
            is_held = {c["id"] for c in cases} == held_ids
            calls.append((skill_md, is_held))
            improved = skill_md == "edited"
            # Training cases improve; held-out cases get worse: classic overfit.
            rate = (40.0 if improved else 60.0) if is_held else (90.0 if improved else 50.0)
            return {"pass_rate": rate, "passed": 0, "total": len(cases), "per_eval": [],
                    "failures": [MISROUTE], "confusion": [], "parse_errors": 0}

        analysis = {"mutation_strategy": "add_routing_rule", "diagnosis": "d",
                    "target_section": "t", "suggested_change": "c"}
        with mock.patch.object(RoutingScorer, "score", fake_score), \
                mock.patch.object(RoutingScorer, "diagnose", new_callable=mock.AsyncMock,
                                  return_value=analysis), \
                mock.patch.object(SkillOptimizer, "_mutate", new_callable=mock.AsyncMock,
                                  return_value={"new_skill_md": "edited", "description": "e"}):
            self.button(at, "Start optimization").click().run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        h = at.session_state["routing_result"]["holdout"]
        self.assertEqual((h["total"], h["baseline"], h["final"], h["regressed"]),
                         (len(held_set), 60.0, 40.0, True))
        self.assertTrue(train_set and held_set)
        self.assertFalse(calls[0][1])  # baseline scored on training cases only
        self.assertTrue(any("held-out" in w.value for w in at.warning))

    def test_min_gain_slider_reaches_the_loop(self):
        at = self.app()
        at.text_input(key="key-value").set_value("fake-key").run()
        at.slider(key="min-gain").set_value(10.0).run()
        at.slider(key="holdout-pct").set_value(0).run()
        rates = iter([50.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0])

        async def fake_score(self_, client, skill_md, cases):
            return {"pass_rate": next(rates), "passed": 0, "total": len(cases), "per_eval": [],
                    "failures": [MISROUTE], "confusion": [], "parse_errors": 0}

        with mock.patch.object(RoutingScorer, "score", fake_score), \
                mock.patch.object(RoutingScorer, "diagnose", new_callable=mock.AsyncMock,
                                  return_value={"mutation_strategy": "s"}), \
                mock.patch.object(SkillOptimizer, "_mutate", new_callable=mock.AsyncMock,
                                  return_value={"new_skill_md": "edited", "description": "e"}):
            self.button(at, "Start optimization").click().run()
        res = at.session_state["routing_result"]
        self.assertEqual(res["min_gain"], 10.0)
        self.assertEqual(res["final_score"], 50.0)  # +5 is below the 10-point bar
        self.assertEqual({m["outcome"] for m in res["mutation_log"]}, {"discarded"})


if __name__ == "__main__":
    unittest.main()
