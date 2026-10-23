"""score_rca: quality scoring is unchanged, and grounding is a separate third score.

The judge is faked, so no model is called. `FakeOpt._ask_json` answers each judge
call from a table keyed by the check ids it was asked about.
"""

import asyncio
import json
import os
import sys
import unittest
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "optimizer"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import score_rca  # noqa: E402

with open(os.path.join(ROOT, "references", "rca-rubric.json")) as f:
    RUBRIC = json.load(f)


class StringVerdictsOnAGoldenCase(unittest.TestCase):
    """Some models answer `"false"` instead of `false`. Score a golden RCA end to end
    with a judge that does that, and a string "false" must count as a failure in both
    the quality checks and the judged grounding checks."""

    def test_string_false_fails_and_string_true_passes(self):
        with open(os.path.join(ROOT, "references", "rca-golden-set.json")) as f:
            case = {c["id"]: c for c in json.load(f)["cases"]}["aws-stack-frame-grounded"]
        judged = [c["id"] for c in RUBRIC["grounding"]["checks"]
                  if c["kind"] == "judged" and c["requires"] == "code"]
        answers = {"ev_quotes_log": "false", "cc_mechanism": "False", "sc_owner": "true",
                   **{cid: "false" for cid in judged}}
        r = asyncio.run(score_rca.score_rca(FakeOpt(answers), case["rca"], case["evidence"],
                                            RUBRIC, runs=1, true_root_cause=case["true_root_cause"]))
        got = {c["id"]: c["passed"] for c in r["checks"]}
        self.assertIs(got["ev_quotes_log"], False)
        self.assertIs(got["cc_mechanism"], False)
        self.assertIs(got["sc_owner"], True)
        self.assertLess(r["quality"], 100)
        grounded = {c["id"]: c["passed"] for c in r["grounding"]["checks"]}
        self.assertTrue(judged)
        for cid in judged:
            self.assertIs(grounded[cid], False, cid)


class FakeOpt:
    """Stands in for TriageOptimizer. `answers` maps check id -> verdict; ids not
    listed pass. Records every judge call so tests can assert on what was asked."""

    def __init__(self, answers=None, gate="correct"):
        self.answers, self.gate, self.calls = answers or {}, gate, []

    async def _ask_json(self, system, user, fallback=None, **kw):
        self.calls.append({"system": system, "user": user, "role": kw.get("role")})
        if "root cause" in user.lower() and "# Question" in user:  # the correctness gate
            return {"verdict": self.gate, "reason": "fake"}
        ids = [line.split('"id": "')[1].split('"')[0]
               for line in user.splitlines() if line.strip().startswith('"id": "')]
        return {"results": [{"id": i, "passed": self.answers.get(i, True), "quote": f"q-{i}"}
                            for i in ids]}


def score(opt, rca="An RCA.", bundle=None, **kw):
    return asyncio.run(score_rca.score_rca(opt, rca, bundle, RUBRIC, **kw))


class QualityUnchanged(unittest.TestCase):
    def test_all_pass_scores_100_and_every_check_is_judged(self):
        r = score(FakeOpt(), runs=1)
        self.assertEqual(r["quality"], 100.0)
        quality_ids = {c["id"] for d in RUBRIC["dimensions"] for c in d["checks"]}
        self.assertEqual({c["id"] for c in r["checks"]}, quality_ids)

    def test_a_failed_check_lowers_only_its_dimension(self):
        r = score(FakeOpt({"ev_quotes_log": False}), runs=1)
        by = {d["dimension"]: d for d in r["per_dimension"]}
        self.assertLess(by["evidence_quality"]["rate"], 100)
        self.assertEqual(by["causal_chain"]["rate"], 100.0)
        self.assertLess(r["quality"], 100)

    def test_majority_vote_across_runs_flags_split_checks(self):
        votes = iter([True, False, True])

        class Flip(FakeOpt):
            async def _ask_json(self, system, user, fallback=None, **kw):
                out = await super()._ask_json(system, user, fallback, **kw)
                if '"id": "ev_window"' in user and kw.get("role") == "judge":
                    for item in out["results"]:
                        if item["id"] == "ev_window":
                            item["passed"] = next(votes)
                return out

        r = score(Flip(), runs=3)
        self.assertIn("ev_window", r["unstable_checks"])
        self.assertTrue(next(c for c in r["checks"] if c["id"] == "ev_window")["passed"])

    def test_missing_judge_output_is_a_failure_not_a_pass(self):
        class Silent(FakeOpt):
            async def _ask_json(self, *a, **k):
                return {"results": []}

        r = score(Silent(), runs=1)
        self.assertEqual(r["quality"], 0.0)

    def test_session_line_is_stripped_before_judging(self):
        opt = FakeOpt()
        score(opt, rca="# RCA\n- **Session:** http://127.0.0.1/replay\n- **Env:** staging\n", runs=1)
        self.assertNotIn("127.0.0.1", opt.calls[0]["user"])

    def test_correctness_gate_still_reported_separately(self):
        r = score(FakeOpt(gate="wrong"), runs=1, true_root_cause="a missing index")
        self.assertEqual(r["correctness"], "wrong")
        self.assertEqual(r["quality"], 100.0)  # never averaged with correctness


TRACE = 'trace="projects/proj/traces/7f3a9c1e88"'
LINK = ("https://console.cloud.google.com/logs/query;query=" + quote(TRACE, safe="")
        + ";startTime=2026-09-18T14%3A00%3A00Z;endTime=2026-09-18T14%3A10%3A00Z?project=proj")
CODE = "        self.max_connections = 10\n        self.acquire_timeout_s = 30"
BUNDLE = {
    "vendor": "gcp", "symptom": "checkout 500s",
    "symptom_window": {"start": "2026-09-18T14:01:02+00:00", "end": "2026-09-18T14:07:44+00:00"},
    "trace_ids": ["7f3a9c1e88"], "services": ["checkout"], "entries": [],
    "links": [{"url": LINK, "label": "the failing trace"}],
    "code": [{"path": "src/db/pool.py", "ref": "abc123", "start_line": 40, "text": CODE}],
}
GROUNDED_RCA = (f"Trace in [Logs Explorer]({LINK}).\n\n## Code\n"
                "- `src/db/pool.py:40` — `self.max_connections = 10` — the hard cap\n")


class Grounding(unittest.TestCase):
    def test_grounded_rca_scores_100_and_does_not_touch_quality(self):
        r = score(FakeOpt(), rca=GROUNDED_RCA, bundle=BUNDLE, runs=1)
        g = r["grounding"]
        self.assertEqual(g["score"], 100.0)
        self.assertFalse(g["hard_fail"])
        self.assertEqual(r["quality"], 100.0)
        self.assertNotIn("grounding", {d["dimension"] for d in r["per_dimension"]})

    def test_judge_sees_the_attached_links_and_numbered_code(self):
        opt = FakeOpt()
        score(opt, rca=GROUNDED_RCA, bundle=BUNDLE, runs=1)
        prompt = opt.calls[0]["user"]
        self.assertIn(LINK, prompt)
        self.assertIn("the failing trace", prompt)
        self.assertIn("  40 |         self.max_connections = 10", prompt)
        self.assertIn("src/db/pool.py @ abc123, lines 40-41", prompt)

    def test_judged_grounding_checks_go_to_their_own_judge_call(self):
        opt = FakeOpt({"gr_code_supports_mechanism": False})
        r = score(opt, rca=GROUNDED_RCA, bundle=BUNDLE, runs=1)
        grounding_calls = [c for c in opt.calls if c["role"] == "judge.grounding"]
        self.assertEqual(len(grounding_calls), 1)
        asked = grounding_calls[0]["user"]
        for cid in ("gr_code_supports_mechanism", "gr_log_to_code", "gr_link_claim_matches"):
            self.assertIn(cid, asked)
        self.assertNotIn("gr_no_invented_code", asked)  # decided in code, never judged
        by = {c["id"]: c for c in r["grounding"]["checks"]}
        self.assertIs(by["gr_code_supports_mechanism"]["passed"], False)
        self.assertLess(r["grounding"]["score"], 100)
        self.assertFalse(r["grounding"]["hard_fail"])

    def test_invented_code_line_is_a_hard_fail_but_quality_is_unchanged(self):
        rca = GROUNDED_RCA + "- `src/db/pool.py:212` — `self.retries = 5` — retries\n"
        r = score(FakeOpt(), rca=rca, bundle=BUNDLE, runs=1)
        self.assertTrue(r["grounding"]["hard_fail"])
        self.assertIn("gr_no_invented_code", r["grounding"]["fabricated"])
        self.assertEqual(r["quality"], 100.0)  # never averaged in

    def test_no_attachments_means_no_grounding_score_and_no_judge_call(self):
        opt = FakeOpt()
        r = score(opt, rca="An RCA citing nothing.", bundle={"vendor": "gcp", "entries": []}, runs=1)
        self.assertIsNone(r["grounding"]["score"])
        self.assertFalse(r["grounding"]["hard_fail"])
        self.assertFalse(any(c["role"] == "judge.grounding" for c in opt.calls))

    def test_rubric_without_grounding_block_reports_no_grounding(self):
        rubric = {k: v for k, v in RUBRIC.items() if k != "grounding"}
        r = asyncio.run(score_rca.score_rca(FakeOpt(), GROUNDED_RCA, BUNDLE, rubric, runs=1))
        self.assertNotIn("grounding", r)

    def test_report_prints_the_third_score(self):
        import contextlib
        import io

        r = score(FakeOpt(), rca=GROUNDED_RCA + "- `src/db/pool.py:212` — `x = 1` — y\n",
                  bundle=BUNDLE, runs=1)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            score_rca.report(r, "incident.md")
        out = buf.getvalue()
        self.assertIn("GROUNDING    FAIL", out)
        self.assertIn("gr_no_invented_code", out)
        self.assertIn("[code ]", out)


_FAKE_CLAUDE = """#!{python}
import json, sys
sys.stdin.read()
print(json.dumps({{"result": json.dumps({{"results": []}}), "is_error": False,
                   "usage": {{"input_tokens": 1, "output_tokens": 1}}}}))
"""


class CliExitCode(unittest.TestCase):
    """The real CLI, on golden cases, with a fake `claude` so no model is called.

    The fake judge returns nothing, so quality is 0 for every case; only grounding
    decides the difference between exit 1 (send back) and exit 2 (blocked).
    """

    def setUp(self):
        import stat
        import tempfile

        self.dir = tempfile.TemporaryDirectory()
        self.bin = os.path.join(self.dir.name, "claude")
        with open(self.bin, "w") as f:
            f.write(_FAKE_CLAUDE.format(python=sys.executable))
        os.chmod(self.bin, os.stat(self.bin).st_mode | stat.S_IEXEC)
        with open(os.path.join(ROOT, "references", "rca-golden-set.json")) as f:
            self.cases = {c["id"]: c for c in json.load(f)["cases"]}

    def tearDown(self):
        self.dir.cleanup()

    def run_case(self, case_id):
        import subprocess

        case = self.cases[case_id]
        rca, ev = (os.path.join(self.dir.name, n) for n in ("rca.md", "ev.json"))
        with open(rca, "w") as f:
            f.write(case["rca"])
        with open(ev, "w") as f:
            json.dump(case["evidence"], f)
        env = {**os.environ, "TRIAGE_CLAUDE_BIN": self.bin,
               "TRIAGE_TRACE_DB": os.path.join(self.dir.name, "t.db")}
        return subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "score_rca.py"), "--rca", rca,
             "--evidence", ev, "--model", "claude_code/haiku", "--runs", "1"],
            env=env, capture_output=True, text=True, timeout=120)

    def test_fabricated_code_line_blocks_handoff(self):
        out = self.run_case("gcp-invented-code-line")
        self.assertEqual(out.returncode, 2, out.stdout + out.stderr)
        self.assertIn("GROUNDING    FAIL", out.stdout)
        self.assertIn("repository.py:31", out.stdout)

    def test_grounded_rca_is_not_blocked_by_grounding(self):
        out = self.run_case("gcp-grounded-links-and-code")
        self.assertEqual(out.returncode, 1, out.stdout + out.stderr)  # quality 0 from the fake judge
        self.assertNotIn("GROUNDING    FAIL", out.stdout)


if __name__ == "__main__":
    unittest.main()
