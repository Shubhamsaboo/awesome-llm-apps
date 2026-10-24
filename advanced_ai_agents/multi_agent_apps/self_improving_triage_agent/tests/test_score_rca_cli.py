"""The app's score_rca.py wrapper: the skill's CLI on this app's Claude Code backend.

A fake `claude` stands in for the model, so nothing is called. The fake judge
returns nothing, so quality is 0 for every case; only grounding decides the
difference between exit 1 (send back) and exit 2 (blocked).
"""

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "optimizer"))

import skill_paths  # noqa: E402
import telemetry  # noqa: E402

_FAKE_CLAUDE = """#!{python}
import json, sys
sys.stdin.read()
print(json.dumps({{"result": json.dumps({{"results": []}}), "is_error": False,
                   "usage": {{"input_tokens": 1, "output_tokens": 1}}}}))
"""


class CliExitCode(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.bin = os.path.join(self.dir.name, "claude")
        with open(self.bin, "w") as f:
            f.write(_FAKE_CLAUDE.format(python=sys.executable))
        os.chmod(self.bin, os.stat(self.bin).st_mode | stat.S_IEXEC)
        self.db = os.path.join(self.dir.name, "t.db")
        with open(skill_paths.RCA_GOLDEN) as f:
            self.cases = {c["id"]: c for c in json.load(f)["cases"]}

    def tearDown(self):
        self.dir.cleanup()

    def run_case(self, case_id):
        case = self.cases[case_id]
        rca, ev = (os.path.join(self.dir.name, n) for n in ("rca.md", "ev.json"))
        with open(rca, "w") as f:
            f.write(case["rca"])
        with open(ev, "w") as f:
            json.dump(case["evidence"], f)
        env = {**os.environ, "TRIAGE_CLAUDE_BIN": self.bin, "TRIAGE_TRACE_DB": self.db}
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

    def test_cli_run_is_one_traced_session_on_claude_code(self):
        self.run_case("gcp-grounded-links-and-code")
        sessions = telemetry.Store(self.db).sessions()
        self.assertEqual([(s["name"], s["backend"]) for s in sessions],
                         [("cli.score_rca", "claude_code")])

    def test_parse_error_marker_matches_the_skill(self):
        # The app's client flags unparseable replies; the skill's scorer counts them.
        import score_rca
        import skill_optimizer

        self.assertEqual(skill_optimizer.PARSE_ERROR, score_rca.PARSE_ERROR)
        self.assertEqual(os.path.realpath(os.path.dirname(score_rca.__file__)),
                         os.path.realpath(skill_paths.SKILL_SCRIPTS))


if __name__ == "__main__":
    unittest.main()
