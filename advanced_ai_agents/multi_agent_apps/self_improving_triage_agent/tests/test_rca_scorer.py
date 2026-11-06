"""RCA scorer: grounding is aggregated, reported, and vetoes regressions.

The per-case scorer is replaced with a stub, so no model is called.
"""

import asyncio
import json
import os
import sys
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "optimizer"))

import rca_scorer  # noqa: E402
import skill_paths  # noqa: E402
from rca_scorer import RcaScorer  # noqa: E402
from routing_scorer import RoutingScorer  # noqa: E402
from skill_optimizer import SkillOptimizer  # noqa: E402

with open(skill_paths.RCA_RUBRIC) as f:
    RUBRIC = json.load(f)


def detail(grounding=None, quality=100.0, correctness="correct"):
    d = {"quality": quality, "correctness": correctness, "correctness_reason": "",
         "checks": [], "per_dimension": [{"dimension": x["id"], "passed": 1, "total": 1}
                                         for x in RUBRIC["dimensions"]]}
    if grounding is not None:
        d["grounding"] = grounding
    return d


def g(score, hard_fail=False, failed=()):
    checks = [{"id": cid, "question": "q", "detail": f"{cid} failed", "passed": False}
              for cid in failed]
    return {"score": score, "hard_fail": hard_fail,
            "fabricated": [c for c in failed if c.startswith("gr_no_invented") or c == "gr_quotes_verbatim"]
            if hard_fail else [], "checks": checks}


class Aggregation(unittest.TestCase):
    def score(self, details):
        cases = [{"id": f"c{i}", "expected_correctness": "correct", "evidence": {}}
                 for i in range(len(details))]
        it = iter(details)

        async def fake_one(self, client, skill_md, case):
            return case, "rca text", next(it)

        with mock.patch.object(RcaScorer, "_score_one", fake_one):
            return asyncio.run(RcaScorer(RUBRIC).score(SkillOptimizer(), "skill", cases))

    def test_grounding_pct_averages_only_cases_that_have_a_score(self):
        r = self.score([detail(g(100.0)), detail(g(50.0)), detail(g(None)), detail()])
        self.assertEqual(r["grounding_pct"], 75.0)

    def test_no_grounded_cases_gives_none(self):
        self.assertIsNone(self.score([detail(), detail(g(None))])["grounding_pct"])

    def test_grounding_does_not_enter_the_objective(self):
        a = self.score([detail(g(100.0))])
        b = self.score([detail(g(10.0, hard_fail=True, failed=["gr_no_invented_code"]))])
        self.assertEqual(a["pass_rate"], b["pass_rate"])  # same correctness + quality
        self.assertNotEqual(a["grounding_pct"], b["grounding_pct"])

    def test_fabrications_are_listed_and_reach_failures(self):
        r = self.score([detail(g(40.0, hard_fail=True, failed=["gr_no_invented_code"])), detail(g(100.0))])
        self.assertEqual(r["fabricated"], [{"case_id": "c0", "checks": ["gr_no_invented_code"]}])
        f = next(x for x in r["failures"] if x["case_id"] == "c0")
        self.assertEqual(f["grounding"], 40.0)
        self.assertEqual([x["id"] for x in f["grounding_failed"]], ["gr_no_invented_code"])

    def test_a_grounding_miss_alone_makes_a_case_a_failure(self):
        r = self.score([detail(g(80.0, failed=["gr_link_pinned"]))])
        self.assertEqual([f["case_id"] for f in r["failures"]], ["c0"])


class Improves(unittest.TestCase):
    opt = RcaScorer(RUBRIC)

    def r(self, pass_rate, grounding_pct=None, fabricated=0):
        return {"pass_rate": pass_rate, "grounding_pct": grounding_pct,
                "fabricated": [{"case_id": f"c{i}"} for i in range(fabricated)]}

    def test_higher_objective_with_equal_grounding_is_kept(self):
        self.assertTrue(self.opt.improves(self.r(70, 90), self.r(60, 90)))

    def test_new_fabrication_vetoes_a_higher_objective(self):
        self.assertFalse(self.opt.improves(self.r(80, 90, fabricated=1), self.r(60, 90)))

    def test_lower_grounding_vetoes_a_higher_objective(self):
        self.assertFalse(self.opt.improves(self.r(80, 70), self.r(60, 90)))

    def test_fewer_fabrications_with_a_higher_objective_is_kept(self):
        self.assertTrue(self.opt.improves(self.r(70, 90, fabricated=0), self.r(60, 80, fabricated=2)))

    def test_grounding_alone_cannot_buy_a_lower_objective(self):
        self.assertFalse(self.opt.improves(self.r(50, 100), self.r(60, 40)))

    def test_missing_grounding_on_either_side_is_ignored(self):
        self.assertTrue(self.opt.improves(self.r(70, None), self.r(60, 90)))
        self.assertTrue(self.opt.improves(self.r(70, 90), self.r(60, None)))

    def test_routing_optimizer_is_unchanged(self):
        base = RoutingScorer([], [])
        self.assertTrue(base.improves({"pass_rate": 70}, {"pass_rate": 60}))
        self.assertFalse(base.improves({"pass_rate": 60}, {"pass_rate": 60}))


class ReviewFindings(unittest.TestCase):
    """Regressions from the code review; each was reproduced before the fix."""

    opt = RcaScorer(RUBRIC)

    @staticmethod
    def r(pass_rate, fabs=(), grounding_pct=80):
        return {"pass_rate": pass_rate, "grounding_pct": grounding_pct,
                "fabricated": [{"case_id": c, "checks": ["gr_no_invented_code"]} for c in fabs]}

    def test_swapping_one_fabrication_for_another_is_vetoed(self):
        self.assertFalse(self.opt.improves(self.r(75, ["B"]), self.r(70, ["A"])))

    def test_equal_objective_that_removes_fabrication_is_kept(self):
        self.assertTrue(self.opt.improves(self.r(70, [], 95), self.r(70, ["A"], 60)))

    def test_equal_objective_without_fewer_fabrications_is_not_kept(self):
        self.assertFalse(self.opt.improves(self.r(70, ["A"]), self.r(70, ["A"])))
        self.assertFalse(self.opt.improves(self.r(70, ["A", "B"]), self.r(70, ["A"])))

    def test_not_converged_at_100_while_fabrications_remain(self):
        self.assertFalse(self.opt.converged(self.r(100.0, ["A"])))
        self.assertTrue(self.opt.converged(self.r(100.0, [])))
        self.assertTrue(RoutingScorer([], []).converged({"pass_rate": 100.0}))

    def test_loop_keeps_running_past_100_to_remove_fabrication(self):
        scores = iter([self.r(100.0, ["A"], 60), self.r(100.0, [], 95)])

        async def fake_score(self, *a):
            return {**next(scores), "passed": 1, "total": 1, "per_eval": [],
                    "failures": [], "confusion": []}

        async def fake_analyze(self, *a):
            return {"mutation_strategy": "add_citation_rule", "diagnosis": "d",
                    "target_section": "t", "suggested_change": "c"}

        async def fake_mutate(self, *a):
            return {"description": "cite only attached code", "reasoning": "r",
                    "new_skill_md": "fixed skill"}

        with mock.patch.multiple(RcaScorer, score=fake_score, diagnose=fake_analyze), \
                mock.patch.object(SkillOptimizer, "_mutate", fake_mutate):
            out = asyncio.run(SkillOptimizer().optimize(
                "skill", RcaScorer(RUBRIC), [{"id": "c"}], max_rounds=3))
        self.assertEqual(out["improved_skill_md"], "fixed skill")
        self.assertEqual(out["fabricated"], [])
        self.assertEqual(out["grounding_pct"], 95)

    def test_results_carry_grounding_even_without_a_kept_mutation(self):
        async def fake_score(self, *a):
            return {**ReviewFindings.r(50.0, ["A"], 70), "passed": 0, "total": 1,
                    "per_eval": [], "failures": [], "confusion": []}

        with mock.patch.object(RcaScorer, "score", fake_score):
            out = asyncio.run(SkillOptimizer().optimize(
                "skill", RcaScorer(RUBRIC), [{"id": "c"}], max_rounds=0))
        self.assertEqual(out["grounding_pct"], 70)
        self.assertEqual([f["case_id"] for f in out["fabricated"]], ["A"])

    def test_routing_results_have_no_grounding_keys(self):
        async def fake_score(self, *a):
            return {"pass_rate": 50.0, "passed": 0, "total": 1, "per_eval": [],
                    "failures": [], "confusion": []}

        with mock.patch.object(RoutingScorer, "score", fake_score):
            out = asyncio.run(SkillOptimizer().optimize(
                "skill", RoutingScorer([], []), [{"id": "c"}], max_rounds=0))
        self.assertNotIn("grounding_pct", out)

    def test_analyst_system_prompt_offers_the_citation_strategy(self):
        self.assertIn("add_citation_rule", rca_scorer.RCA_ANALYST_SYSTEM)


class AnalystPriority(unittest.TestCase):
    def test_invented_evidence_is_flagged_high_priority(self):
        captured = {}

        async def fake_ask_json(self, system, user, fallback=None, **kw):
            captured["user"] = user
            return fallback

        failures = [{"case_id": "c0", "expected_correctness": "correct", "correctness": "correct",
                     "credit": 1.0, "grounding_failed": [
                         {"id": "gr_no_invented_code", "question": "q", "detail": "cites pool.py:210",
                          "hard_fail": True},
                         {"id": "gr_link_pinned", "question": "q", "detail": "relative"}]}]
        with mock.patch.object(SkillOptimizer, "_ask_json", fake_ask_json):
            asyncio.run(RcaScorer(RUBRIC).diagnose(SkillOptimizer(), "skill", failures, []))
        prompt = captured["user"]
        self.assertIn("cited evidence that was never attached", prompt)
        self.assertIn("cites pool.py:210", prompt)
        self.assertIn("add_citation_rule", prompt)
        block = prompt.split("never attached", 1)[1]
        self.assertNotIn("gr_link_pinned", block.split("# ", 1)[0])  # misses aren't fabrications

    def test_no_invented_block_without_fabrication(self):
        captured = {}

        async def fake_ask_json(self, system, user, fallback=None, **kw):
            captured["user"] = user
            return fallback

        failures = [{"case_id": "c0", "credit": 1.0, "grounding_failed": [
            {"id": "gr_link_pinned", "question": "q", "detail": "relative"}]}]
        with mock.patch.object(SkillOptimizer, "_ask_json", fake_ask_json):
            asyncio.run(RcaScorer(RUBRIC).diagnose(SkillOptimizer(), "skill", failures, []))
        self.assertNotIn("never attached", captured["user"])


class KeepDecisionInTheLoop(unittest.TestCase):
    """The loop must call the scorer's improves(), not compare pass_rate itself."""

    def test_loop_discards_a_higher_scoring_but_fabricating_mutation(self):
        scores = iter([
            {"pass_rate": 50.0, "grounding_pct": 100.0, "fabricated": []},              # baseline
            {"pass_rate": 90.0, "grounding_pct": 60.0, "fabricated": [{"case_id": "c"}]},  # round 1
        ])

        async def fake_score(self, client, skill_md, cases):
            r = next(scores)
            return {**r, "passed": 0, "total": 1, "per_eval": [], "failures": [{"case_id": "c"}],
                    "confusion": []}

        async def fake_analyze(self, *a):
            return {"mutation_strategy": "add_citation_rule", "diagnosis": "d",
                    "target_section": "t", "suggested_change": "c"}

        async def fake_mutate(self, *a):
            return {"description": "edit", "reasoning": "r", "new_skill_md": "changed skill"}

        with mock.patch.multiple(RcaScorer, score=fake_score, diagnose=fake_analyze), \
                mock.patch.object(SkillOptimizer, "_mutate", fake_mutate):
            out = asyncio.run(SkillOptimizer().optimize(
                "original skill", RcaScorer(RUBRIC), [{"id": "c"}], max_rounds=1))
        self.assertEqual(out["improved_skill_md"], "original skill")
        self.assertFalse(out["mutation_log"][0]["kept"])
        self.assertEqual(out["final_score"], 50.0)


if __name__ == "__main__":
    unittest.main()
