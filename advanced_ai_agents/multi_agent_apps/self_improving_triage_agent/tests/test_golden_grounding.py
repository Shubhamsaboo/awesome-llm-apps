"""The golden set's grounding labels hold, offline.

Every case that declares `expected_grounding` is scored by the deterministic
checks alone (no model). If an edit to a case, to grounding.py or to the rubric
changes which checks fail, this says so before any judge run.
"""

import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import grounding  # noqa: E402
import log_links  # noqa: E402

with open(os.path.join(ROOT, "references", "rca-rubric.json")) as f:
    SPEC = json.load(f)["grounding"]
with open(os.path.join(ROOT, "references", "rca-golden-set.json")) as f:
    CASES = json.load(f)["cases"]

LABELED = [c for c in CASES if "expected_grounding" in c]


class GoldenGrounding(unittest.TestCase):
    def test_there_are_labeled_grounding_cases(self):
        self.assertGreaterEqual(len(LABELED), 3)

    def test_deterministic_checks_match_the_labels(self):
        for case in LABELED:
            with self.subTest(case=case["id"]):
                det = grounding.run_deterministic(case["rca"], case["evidence"], SPEC)
                s = grounding.summarize(det, [], SPEC)
                failed = sorted(c["id"] for c in det if c["passed"] is False)
                want = case["expected_grounding"]
                self.assertEqual(failed, sorted(want["failed"]),
                                 {c["id"]: c["detail"] for c in det})
                self.assertEqual(s["hard_fail"], want["hard_fail"])

    def test_every_attached_link_parses(self):
        for case in LABELED:
            for item in case["evidence"].get("links", []):
                with self.subTest(case=case["id"], url=item["url"][:60]):
                    self.assertIsNotNone(log_links.parse_link(item["url"]))

    def test_attached_code_is_where_the_snippets_say(self):
        # Every snippet's line count matches its declared start, so citations are checkable.
        for case in LABELED:
            for s in grounding.snippets(case["evidence"]):
                with self.subTest(case=case["id"], path=s["path"]):
                    self.assertEqual(s["end"] - s["start"] + 1, len(s["lines"]))

    def test_invented_and_grounded_cases_differ_only_by_the_invention(self):
        # The pair isolates one variable: same evidence, same RCA, one made-up line.
        by = {c["id"]: c for c in CASES}
        a, b = by["gcp-grounded-links-and-code"], by["gcp-invented-code-line"]
        self.assertEqual(a["evidence"], b["evidence"])
        added = set(b["rca"].splitlines()) - set(a["rca"].splitlines())
        self.assertEqual(len(added), 1)
        self.assertIn("repository.py:31", added.pop())

    def test_each_citation_trap_is_one_citation_away_from_its_reference(self):
        by = {c["id"]: c for c in CASES}
        ref = by["aws-stack-frame-grounded"]
        traps = {"aws-stack-frame-off-by-digit": "CheckoutService.java:14`",
                 "aws-stack-frame-range": "CheckoutService.java:142-150",
                 "aws-invented-config-line": "application.properties:12"}
        for trap_id, invented in traps.items():
            with self.subTest(case=trap_id):
                trap = by[trap_id]
                self.assertEqual(trap["evidence"], ref["evidence"])
                added = set(trap["rca"].splitlines()) - set(ref["rca"].splitlines())
                self.assertEqual(len(added), 1)
                self.assertIn(invented, added.pop())

    def test_cases_without_attachments_are_not_marked_down(self):
        for case in CASES:
            ev = case.get("evidence") or {}
            if ev.get("links") or ev.get("code"):
                continue
            with self.subTest(case=case["id"]):
                # Ticket-only cases carry no reference RCA; score an empty one.
                rca = case.get("rca", "")
                s = grounding.summarize(grounding.run_deterministic(rca, ev, SPEC), [], SPEC)
                self.assertIsNone(s["score"])
                self.assertFalse(s["hard_fail"])


if __name__ == "__main__":
    unittest.main()
