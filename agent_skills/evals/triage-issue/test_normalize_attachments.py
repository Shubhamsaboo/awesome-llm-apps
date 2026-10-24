"""normalize_evidence.py attaches links and code, and refuses ones it cannot grade."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import quote

# The skill under test: agent_skills/triage-issue (this file is in agent_skills/evals/triage-issue).
ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "triage-issue")
SCRIPT = os.path.join(ROOT, "scripts", "normalize_evidence.py")
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import grounding  # noqa: E402
import normalize_evidence  # noqa: E402

LINK = ("https://console.cloud.google.com/logs/query;query="
        + quote('trace="projects/p/traces/abc123"', safe="")
        + ";startTime=2026-09-18T14%3A00%3A00Z;endTime=2026-09-18T14%3A10%3A00Z?project=p")
LOGS = [{"timestamp": "2026-09-18T14:02:11Z", "severity": "ERROR", "logName": "x",
         "trace": "projects/p/traces/abc123", "jsonPayload": {"message": "boom"}}]


class CodeArg(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        os.makedirs(os.path.join(self.dir.name, "src"))
        with open(os.path.join(self.dir.name, "src", "pool.py"), "w") as f:
            f.write("".join(f"line {i}\n" for i in range(1, 21)))

    def tearDown(self):
        self.dir.cleanup()

    def read(self, spec):
        return normalize_evidence.read_code_arg(spec, self.dir.name)

    def test_range(self):
        s = self.read("src/pool.py:5-7")
        self.assertEqual((s["path"], s["start_line"]), ("src/pool.py", 5))
        self.assertNotIn("ref", s)  # a ref means "read from git"; see CodeAtRef
        self.assertEqual(s["text"], "line 5\nline 6\nline 7")

    def test_single_line_and_whole_file(self):
        self.assertEqual(self.read("src/pool.py:9")["text"], "line 9")
        whole = self.read("src/pool.py")
        self.assertEqual((whole["start_line"], whole["text"].count("\n")), (1, 19))
        self.assertNotIn("ref", whole)

    def test_out_of_range_is_refused(self):
        with self.assertRaisesRegex(ValueError, "out of range"):
            self.read("src/pool.py:15-40")

    def test_attached_code_is_citable_at_its_real_line_numbers(self):
        bundle = {"code": [self.read("src/pool.py:5-7")]}
        self.assertTrue(grounding.gr_no_invented_code("see `src/pool.py:6`", bundle)[0])
        self.assertIs(grounding.gr_no_invented_code("see `src/pool.py:8`", bundle)[0], False)


class CodeAtRef(unittest.TestCase):
    """`--code path@ref` reads the file from git at that ref, not the working tree."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        d = self.dir.name

        def git(*args):
            subprocess.run(["git", "-C", d, *args], check=True, capture_output=True)

        git("init", "-q")
        git("config", "user.email", "t@example.com")
        git("config", "user.name", "t")
        with open(os.path.join(d, "pool.py"), "w") as f:
            f.write("max_size = 10\ntimeout = 30\n")
        git("add", "pool.py")
        git("commit", "-qm", "one")
        self.first = subprocess.run(["git", "-C", d, "rev-parse", "--short", "HEAD"],
                                    capture_output=True, text=True, check=True).stdout.strip()
        with open(os.path.join(d, "pool.py"), "w") as f:
            f.write("max_size = 50\ntimeout = 30\n")  # working tree differs from the commit

    def tearDown(self):
        self.dir.cleanup()

    def test_reads_the_committed_version(self):
        s = normalize_evidence.read_code_arg(f"pool.py:1@{self.first}", self.dir.name)
        self.assertEqual((s["text"], s["ref"]), ("max_size = 10", self.first))

    def test_without_ref_reads_the_working_tree(self):
        self.assertEqual(normalize_evidence.read_code_arg("pool.py:1", self.dir.name)["text"],
                         "max_size = 50")

    def test_unknown_ref_is_a_clean_error(self):
        with self.assertRaisesRegex(ValueError, "git could not read"):
            normalize_evidence.read_code_arg("pool.py:1@deadbeef0", self.dir.name)


class LinkArg(unittest.TestCase):
    def test_label_is_kept(self):
        self.assertEqual(normalize_evidence.parse_link_arg(LINK, "the trace"),
                         {"url": LINK, "label": "the trace"})

    def test_link_that_would_not_round_trip_is_refused(self):
        bad = LINK.replace("%22", '"')  # a raw quote: cut short when pasted into an RCA
        with self.assertRaisesRegex(ValueError, "would not survive"):
            normalize_evidence.parse_link_arg(bad)

    def test_unparseable_link_is_refused(self):
        with self.assertRaisesRegex(ValueError, "Not a recognised"):
            normalize_evidence.parse_link_arg("https://example.com/whatever")


class Cli(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.logs = os.path.join(self.dir.name, "logs.json")
        with open(self.logs, "w") as f:
            json.dump(LOGS, f)
        os.makedirs(os.path.join(self.dir.name, "src"))
        with open(os.path.join(self.dir.name, "src", "pool.py"), "w") as f:
            f.write("a = 1\nb = 2\nc = 3\n")

    def tearDown(self):
        self.dir.cleanup()

    def run_cli(self, *extra):
        return subprocess.run([sys.executable, SCRIPT, self.logs, *extra],
                              capture_output=True, text=True, timeout=60)

    def test_links_and_code_land_in_the_bundle(self):
        out = self.run_cli("--link", f"{LINK}|failing trace", "--code", "src/pool.py:2-3",
                           "--code-root", self.dir.name)
        self.assertEqual(out.returncode, 0, out.stderr)
        b = json.loads(out.stdout)
        self.assertEqual(b["links"], [{"url": LINK, "label": "failing trace"}])
        self.assertEqual(b["code"], [{"path": "src/pool.py", "start_line": 2,
                                      "text": "b = 2\nc = 3"}])
        self.assertEqual(b["trace_ids"], ["abc123"])

    def test_no_attachments_gives_empty_lists(self):
        b = json.loads(self.run_cli().stdout)
        self.assertEqual((b["links"], b["code"]), ([], []))

    def test_bad_attachment_fails_without_writing_a_bundle(self):
        out_path = os.path.join(self.dir.name, "bundle.json")
        out = self.run_cli("--link", "https://example.com/nope", "-o", out_path)
        self.assertEqual(out.returncode, 2)
        self.assertIn("Not a recognised", out.stderr)
        self.assertFalse(os.path.exists(out_path))

    def test_missing_code_file_fails_cleanly(self):
        out = self.run_cli("--code", "src/missing.py:1", "--code-root", self.dir.name)
        self.assertEqual(out.returncode, 2)
        self.assertNotIn("Traceback", out.stderr)


class GoldenCodeFromSubdirectory(unittest.TestCase):
    """End to end through the CLI: rebuild a golden case's attached code from a git repo
    where the service lives in a subdirectory. `--code-root` must hold with or without
    `@ref`, and a same-named file at the repo root must never be picked up instead."""

    def setUp(self):
        with open(os.path.join(ROOT, "references", "rca-golden-set.json")) as f:
            case = {c["id"]: c for c in json.load(f)["cases"]}["gcp-grounded-links-and-code"]
        self.snippet = case["evidence"]["code"][0]
        self.dir = tempfile.TemporaryDirectory()
        d, path = self.dir.name, self.snippet["path"]
        padding = "".join(f"# line {i}\n" for i in range(1, self.snippet["start_line"]))
        for where, text in ((os.path.join(d, "services", path), padding + self.snippet["text"] + "\n"),
                            (os.path.join(d, path), "# decoy at the repo root\n" * 40)):
            os.makedirs(os.path.dirname(where), exist_ok=True)
            with open(where, "w") as f:
                f.write(text)
        for args in (["init", "-q"], ["config", "user.email", "t@example.com"],
                     ["config", "user.name", "t"], ["add", "-A"], ["commit", "-qm", "seed"]):
            subprocess.run(["git", "-C", d, *args], check=True, capture_output=True)
        self.logs = os.path.join(d, "logs.json")
        with open(self.logs, "w") as f:
            json.dump(LOGS, f)

    def tearDown(self):
        self.dir.cleanup()

    def bundle_code(self, ref):
        s = self.snippet
        end = s["start_line"] + len(s["text"].splitlines()) - 1
        spec = f"{s['path']}:{s['start_line']}-{end}" + (f"@{ref}" if ref else "")
        out = subprocess.run([sys.executable, SCRIPT, self.logs, "--code", spec,
                              "--code-root", os.path.join(self.dir.name, "services")],
                             capture_output=True, text=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)["code"][0]

    def test_ref_and_working_tree_attach_the_same_golden_snippet(self):
        for ref in (None, "HEAD"):
            with self.subTest(ref=ref):
                got = self.bundle_code(ref)
                self.assertEqual((got["path"], got["start_line"], got["text"]),
                                 (self.snippet["path"], self.snippet["start_line"], self.snippet["text"]))


if __name__ == "__main__":
    unittest.main()
