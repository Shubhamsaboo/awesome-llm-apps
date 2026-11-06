"""The generic loop's noise and parse guards, and the any-skill expectations scorer.

No model is called: scorers and the model client are faked.
"""

import asyncio
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "optimizer"))

import skill_paths  # noqa: E402
import telemetry  # noqa: E402
from expectations_scorer import ExpectationsScorer, evals_path, load_cases  # noqa: E402
from skill_optimizer import (PARSE_ERROR, BaseScorer, SkillOptimizer, is_parse_error,  # noqa: E402
                             parse_json, split_holdout)

_tmp = None
_old_path = None


def setUpModule():
    global _tmp, _old_path
    _tmp = tempfile.TemporaryDirectory()
    _old_path = telemetry.store.path
    telemetry.init(os.path.join(_tmp.name, "loop.db"))


def tearDownModule():
    telemetry.store.path = _old_path
    _tmp.cleanup()


ANALYSIS = {"mutation_strategy": "add_rule", "diagnosis": "d", "target_section": "t",
            "suggested_change": "c"}


class ScriptedScorer(BaseScorer):
    """Returns pre-set results in order; records what it was asked to score."""

    kind = "scripted"

    def __init__(self, results, analyses=None):
        self.results, self.analyses = iter(results), iter(analyses or [])
        self.scored = []

    async def score(self, client, skill_md, cases):
        self.scored.append((skill_md, [c["id"] for c in cases]))
        r = next(self.results)
        return {"passed": 0, "total": len(cases), "per_eval": [], "failures": [{"f": 1}],
                "parse_errors": 0, **r}

    async def diagnose(self, client, skill_md, failures, mutation_log):
        self.last_log = list(mutation_log)
        return next(self.analyses, ANALYSIS)


def run(scorer, mutations, **kw):
    it = iter(mutations)

    async def fake_mutate(self, skill_md, analysis, scorer_):
        return next(it)

    with mock.patch.object(SkillOptimizer, "_mutate", fake_mutate):
        return asyncio.run(SkillOptimizer().optimize("v0", scorer, [{"id": 1}, {"id": 2}], **kw))


def edit(md):
    return {"new_skill_md": md, "description": f"to {md}", "reasoning": "r"}


class MinGain(unittest.TestCase):
    def test_small_gain_is_discarded_and_large_gain_kept(self):
        s = ScriptedScorer([{"pass_rate": 50.0}, {"pass_rate": 53.0}, {"pass_rate": 62.0}])
        out = run(s, [edit("v1"), edit("v2")], max_rounds=2, min_gain=5.0)
        self.assertEqual([m["outcome"] for m in out["mutation_log"]], ["discarded", "kept"])
        self.assertEqual((out["final_score"], out["improved_skill_md"]), (62.0, "v2"))

    def test_zero_min_gain_keeps_any_strict_increase(self):
        s = ScriptedScorer([{"pass_rate": 50.0}, {"pass_rate": 50.5}])
        out = run(s, [edit("v1")], max_rounds=1)
        self.assertTrue(out["mutation_log"][0]["kept"])

    def test_base_scorer_rule(self):
        b = BaseScorer()
        self.assertFalse(b.improves({"pass_rate": 60}, {"pass_rate": 60}, 0))
        self.assertFalse(b.improves({"pass_rate": 64}, {"pass_rate": 60}, 5))
        self.assertTrue(b.improves({"pass_rate": 65}, {"pass_rate": 60}, 5))


class ParseFailures(unittest.TestCase):
    def test_more_parse_errors_than_best_is_inconclusive_not_kept(self):
        s = ScriptedScorer([{"pass_rate": 50.0}, {"pass_rate": 90.0, "parse_errors": 2}])
        out = run(s, [edit("v1")], max_rounds=1)
        m = out["mutation_log"][0]
        self.assertEqual((m["outcome"], m["kept"], m["parse_errors"]), ("inconclusive", False, 2))
        self.assertEqual(out["improved_skill_md"], "v0")

    def test_unparseable_analyst_skips_the_round_without_mutating(self):
        bad = {**ANALYSIS, PARSE_ERROR: True}
        s = ScriptedScorer([{"pass_rate": 50.0}], analyses=[bad, bad])
        mutate = mock.AsyncMock()
        with mock.patch.object(SkillOptimizer, "_mutate", mutate):
            out = asyncio.run(SkillOptimizer().optimize("v0", s, [{"id": 1}], max_rounds=5,
                                                        patience=2))
        mutate.assert_not_called()
        self.assertEqual([m["outcome"] for m in out["mutation_log"]], ["skipped", "skipped"])
        self.assertEqual(len(s.scored), 1)  # only the baseline was scored
        self.assertEqual(out["strategy_stats"], {})  # skipped rounds are not strategy evidence

    def test_unparseable_mutator_skips_the_round(self):
        s = ScriptedScorer([{"pass_rate": 50.0}])
        out = run(s, [{**edit("v0"), PARSE_ERROR: True}], max_rounds=1)
        self.assertEqual(out["mutation_log"][0]["outcome"], "skipped")
        self.assertIn("Mutator", out["mutation_log"][0]["description"])

    def test_analyst_is_not_shown_skipped_rounds_as_attempts(self):
        bad = {**ANALYSIS, PARSE_ERROR: True}
        s = ScriptedScorer([{"pass_rate": 50.0}, {"pass_rate": 40.0}, {"pass_rate": 30.0}],
                           analyses=[bad, ANALYSIS, ANALYSIS])
        run(s, [edit("v1"), edit("v2")], max_rounds=3, patience=5)
        block = BaseScorer.tried_block(s.last_log)
        self.assertIn("to v1", block)
        self.assertNotIn("could not be parsed", block)

    def test_client_flags_fallbacks(self):
        async def ask(self, system, user, **kw):
            return "not json"

        with mock.patch.object(SkillOptimizer, "_ask", ask):
            out = asyncio.run(SkillOptimizer()._ask_json("s", "u", fallback={"team": "x"}))
            self.assertTrue(is_parse_error(out))
            self.assertEqual(out["team"], "x")
            with self.assertRaises(ValueError):
                asyncio.run(SkillOptimizer()._ask_json("s", "u"))

    def test_parse_json_tolerates_fences_and_prose(self):
        self.assertEqual(parse_json('```json\n{"a": 1}\n```'), {"a": 1})
        self.assertEqual(parse_json('Here: [1, 2] done'), [1, 2])


class Holdout(unittest.TestCase):
    def test_split_is_deterministic_and_keeps_training_cases(self):
        cases = [{"id": i} for i in range(10)]
        a, b = split_holdout(cases, 0.3), split_holdout(cases, 0.3)
        self.assertEqual(a, b)
        self.assertEqual((len(a[0]), len(a[1])), (7, 3))
        self.assertEqual(split_holdout(cases[:1], 0.9), (cases[:1], []))
        self.assertEqual(len(split_holdout(cases[:2], 0.9)[0]), 1)
        self.assertEqual(split_holdout(cases, 0), (cases, []))

    def test_holdout_never_decides_and_is_reported(self):
        # baseline(train), holdout(start), round(train), holdout(final)
        s = ScriptedScorer([{"pass_rate": 50.0}, {"pass_rate": 70.0},
                            {"pass_rate": 80.0}, {"pass_rate": 60.0}])
        async def fake_mutate(self, *a):
            return edit("v1")

        with mock.patch.object(SkillOptimizer, "_mutate", fake_mutate):
            out = asyncio.run(SkillOptimizer().optimize(
                "v0", s, [{"id": 1}], holdout=[{"id": 9}], max_rounds=1))
        self.assertEqual(out["holdout"], {"baseline": 70.0, "final": 60.0, "total": 1,
                                          "regressed": True, "parse_errors": 0})
        self.assertEqual([ids for _, ids in s.scored], [[1], [9], [1], [9]])
        self.assertEqual(out["final_score"], 80.0)  # kept on training evidence alone

    def test_unchanged_skill_reuses_the_starting_holdout_score(self):
        s = ScriptedScorer([{"pass_rate": 50.0}, {"pass_rate": 70.0}])
        out = asyncio.run(SkillOptimizer().optimize("v0", s, [{"id": 1}],
                                                    holdout=[{"id": 9}], max_rounds=0))
        self.assertEqual((out["holdout"]["final"], len(s.scored)), (70.0, 2))


class Expectations(unittest.TestCase):
    CASES = [{"id": 1, "prompt": "p1", "expected_output": "", "expectations": ["A", "B"]},
             {"id": 2, "prompt": "p2", "expected_output": "", "expectations": ["C"]}]

    def score(self, judge_replies):
        replies = iter(judge_replies)

        async def ask(self, system, user, **kw):
            return "agent output"

        async def ask_json(self, system, user, fallback=None, **kw):
            return next(replies)

        with mock.patch.multiple(SkillOptimizer, _ask=ask, _ask_json=ask_json):
            return asyncio.run(ExpectationsScorer().score(SkillOptimizer(), "skill", self.CASES))

    def test_objective_is_expectations_met(self):
        r = self.score([{"results": [{"index": 0, "passed": True}, {"index": 1, "passed": False}]},
                        {"results": [{"index": 0, "passed": True}]}])
        self.assertEqual((r["pass_rate"], r["passed"], r["total"]), (66.7, 1, 2))
        self.assertEqual([u["expectation"] for u in r["failures"][0]["unmet"]], ["B"])

    def test_missing_or_string_verdicts_fail(self):
        r = self.score([{"results": [{"index": 0, "passed": "true"}]}, {"results": []}])
        self.assertEqual(r["pass_rate"], 0.0)

    def test_judge_parse_errors_are_counted(self):
        r = self.score([{"results": [], PARSE_ERROR: True},
                        {"results": [{"index": 0, "passed": True}]}])
        self.assertEqual(r["parse_errors"], 1)

    def test_every_repo_skill_has_loadable_evals(self):
        # Standardisation check: the generic scorer can read every skill's evals.json.
        skills = [d for d in os.listdir(skill_paths.SKILLS_ROOT)
                  if os.path.isfile(os.path.join(skill_paths.SKILLS_ROOT, d, "SKILL.md"))]
        self.assertIn("triage-issue", skills)
        for name in skills:
            path = evals_path(os.path.join(skill_paths.SKILLS_ROOT, name))
            if os.path.exists(path):
                self.assertTrue(load_cases(path), name)
        self.assertTrue(os.path.exists(evals_path(skill_paths.SKILL_DIR)))


_FAKE_CLAUDE = """#!{python}
import json, sys
prompt = sys.stdin.read()
if "# Expectations" in prompt:
    n = sum(1 for line in prompt.splitlines() if line[:1].isdigit())
    body = json.dumps({{"results": [{{"index": i, "passed": True, "reason": "ok"}} for i in range(n)]}})
else:
    body = "I would run the script and report."
print(json.dumps({{"result": body, "is_error": False, "usage": {{"input_tokens": 1, "output_tokens": 1}}}}))
"""


class OptimizeSkillCli(unittest.TestCase):
    def test_scores_another_repo_skill_with_its_own_evals(self):
        with tempfile.TemporaryDirectory() as d:
            fake = os.path.join(d, "claude")
            with open(fake, "w") as f:
                f.write(_FAKE_CLAUDE.format(python=sys.executable))
            os.chmod(fake, os.stat(fake).st_mode | stat.S_IEXEC)
            skill = os.path.join(skill_paths.SKILLS_ROOT, "scope-creep-detector")
            env = {**os.environ, "TRIAGE_CLAUDE_BIN": fake,
                   "TRIAGE_TRACE_DB": os.path.join(d, "t.db")}
            out = subprocess.run(
                [sys.executable, os.path.join(ROOT, "scripts", "optimize_skill.py"), skill,
                 "--model", "claude_code/haiku", "--json"],
                env=env, capture_output=True, text=True, timeout=120)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        result = json.loads(out.stdout)
        self.assertEqual((result["pass_rate"], result["parse_errors"]), (100.0, 0))
        self.assertEqual(result["total"], len(load_cases(evals_path(skill))))

    def test_optimize_requires_an_output_path(self):
        out = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "optimize_skill.py"),
             skill_paths.SKILL_DIR, "--optimize"], capture_output=True, text=True, timeout=120)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("--out", out.stderr)


if __name__ == "__main__":
    unittest.main()
