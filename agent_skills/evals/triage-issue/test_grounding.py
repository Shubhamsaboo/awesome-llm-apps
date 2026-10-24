"""Deterministic grounding checks, and how the third score is assembled."""

import json
import os
import sys
import unittest
from urllib.parse import quote

# The skill under test: agent_skills/triage-issue (this file is in agent_skills/evals/triage-issue).
ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "triage-issue")
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import grounding  # noqa: E402

with open(os.path.join(ROOT, "references", "rca-rubric.json")) as f:
    SPEC = json.load(f)["grounding"]

TRACE = 'trace="projects/proj/traces/7f3a9c1e88"'


def link(query=TRACE, **params):
    segs = "".join(f";{k}={quote(v, safe='')}" for k, v in params.items())
    return f"https://console.cloud.google.com/logs/query;query={quote(query, safe='')}{segs}?project=proj"


GOOD = link(startTime="2026-09-18T14:00:00Z", endTime="2026-09-18T14:10:00Z")
OTHER_DAY = link(severity := "severity>=ERROR", startTime="2026-09-17T14:00:00Z", endTime="2026-09-17T14:10:00Z")
OTHER_TRACE = link('trace="projects/proj/traces/deadbeef00"', startTime="2026-09-18T14:00:00Z",
                   endTime="2026-09-18T14:10:00Z")
RELATIVE = link("severity>=ERROR", timeRange="PT1H")

CODE_TEXT = (
    "class Pool:\n"                                          # 38
    "    def __init__(self):\n"                              # 39
    "        self.max_connections = 10\n"                    # 40
    "        self.acquire_timeout_s = 30\n"                  # 41
    "    def acquire(self):\n"                               # 42
    "        return self._wait(self.acquire_timeout_s)"      # 43
)

BUNDLE = {
    "trace_ids": ["7f3a9c1e88"],
    "symptom_window": {"start": "2026-09-18T14:01:02+00:00", "end": "2026-09-18T14:07:44+00:00"},
    "links": [{"url": GOOD}, {"url": OTHER_DAY}, {"url": OTHER_TRACE}, {"url": RELATIVE}],
    "code": [{"path": "src/db/pool.py", "ref": "abc123", "start_line": 38, "text": CODE_TEXT}],
}


def run(check, rca, bundle=BUNDLE):
    return grounding.DETERMINISTIC[check](rca, bundle)


class SpecMatchesCode(unittest.TestCase):
    def test_every_deterministic_check_is_implemented_and_nothing_extra(self):
        declared = {c["id"] for c in SPEC["checks"] if c["kind"] == "deterministic"}
        self.assertEqual(declared, set(grounding.DETERMINISTIC))

    def test_hard_fail_ids_exist_and_are_deterministic(self):
        ids = {c["id"]: c for c in SPEC["checks"]}
        for h in SPEC["hard_fail"]:
            self.assertEqual(ids[h]["kind"], "deterministic", h)

    def test_judged_checks_declare_what_they_need(self):
        for c in SPEC["checks"]:
            if c["kind"] == "judged":
                self.assertIn(c["requires"], {"code", "links"}, c["id"])

    def test_check_ids_are_unique(self):
        ids = [c["id"] for c in SPEC["checks"]]
        self.assertEqual(len(ids), len(set(ids)))


class LinkChecks(unittest.TestCase):
    def test_cited_attached_link(self):
        self.assertTrue(run("gr_link_cited", f"Evidence: [logs]({GOOD})")[0])

    def test_no_attached_link_cited(self):
        self.assertIs(run("gr_link_cited", "I looked at the logs.")[0], False)

    def test_link_checks_are_na_without_attachments(self):
        bare = {"trace_ids": [], "symptom_window": None}
        for check in ("gr_link_cited", "gr_no_invented_link", "gr_link_pinned", "gr_link_scopes_evidence"):
            self.assertEqual(run(check, "no links at all", bare)[0], "na", check)

    def test_invented_link_fails(self):
        made_up = link('trace="projects/proj/traces/7f3a9c1e88" AND severity=ERROR',
                       startTime="2026-09-18T14:00:00Z", endTime="2026-09-18T14:10:00Z")
        verdict, detail = run("gr_no_invented_link", f"See {made_up}")
        self.assertIs(verdict, False)
        self.assertIn("never attached", detail)

    def test_link_when_none_were_attached_is_invented(self):
        verdict, _ = run("gr_no_invented_link", f"See {GOOD}", {"links": []})
        self.assertIs(verdict, False)

    def test_reencoded_attached_link_is_not_invented(self):
        # Same query, different percent-encoding case: it is the same link.
        self.assertNotEqual(GOOD, GOOD.replace("%3D", "%3d"))
        self.assertTrue(run("gr_no_invented_link", f"See {GOOD.replace('%3D', '%3d')}")[0])

    def test_link_with_raw_quotes_is_cut_short_and_not_matched(self):
        # Not a valid URL, and the finder stops at a quote so that `"https://…"` in
        # prose does not swallow the closing quote. Pinned so a change is deliberate.
        verdict, _ = run("gr_no_invented_link", f"See {GOOD.replace('%22', chr(34))}")
        self.assertIs(verdict, False)

    def test_relative_range_is_not_pinned(self):
        verdict, detail = run("gr_link_pinned", f"See {RELATIVE}")
        self.assertIs(verdict, False)
        self.assertIn("relative", detail)

    def test_pinned_link_passes_and_unrelied_link_is_na(self):
        self.assertTrue(run("gr_link_pinned", f"See {GOOD}")[0])
        self.assertEqual(run("gr_link_pinned", "no link cited")[0], "na")

    def test_link_to_the_wrong_day_does_not_scope_the_evidence(self):
        verdict, detail = run("gr_link_scopes_evidence", f"See {OTHER_DAY}")
        self.assertIs(verdict, False)
        self.assertIn("symptom window", detail)

    def test_link_filtering_another_trace_does_not_scope_the_evidence(self):
        verdict, detail = run("gr_link_scopes_evidence", f"See {OTHER_TRACE}")
        self.assertIs(verdict, False)
        self.assertIn("not in the evidence", detail)

    def test_right_trace_and_window_scopes_the_evidence(self):
        self.assertTrue(run("gr_link_scopes_evidence", f"See {GOOD}")[0])


class CodeChecks(unittest.TestCase):
    def test_cited_location_inside_attached_code(self):
        self.assertTrue(run("gr_code_cited", "The limit is set at `src/db/pool.py:40`.")[0])

    def test_filename_alone_matches_the_attached_path(self):
        self.assertTrue(run("gr_code_cited", "See `pool.py:40`.")[0])
        self.assertTrue(run("gr_no_invented_code", "See `pool.py:40-41`.")[0])

    def test_partial_filename_does_not_match(self):
        self.assertIs(run("gr_code_cited", "See `ool.py:40`.")[0], False)

    def test_no_citation(self):
        self.assertIs(run("gr_code_cited", "The pool is too small.")[0], False)

    def test_code_checks_are_na_without_code(self):
        bare = {"links": []}
        self.assertEqual(run("gr_code_cited", "nothing", bare)[0], "na")
        self.assertEqual(run("gr_no_invented_code", "nothing", bare)[0], "na")

    def test_line_outside_the_attached_range_is_invented(self):
        verdict, detail = run("gr_no_invented_code", "Set at `src/db/pool.py:210`.")
        self.assertIs(verdict, False)
        self.assertIn("pool.py:210", detail)

    def test_range_running_past_the_snippet_is_invented(self):
        self.assertIs(run("gr_no_invented_code", "See `src/db/pool.py:42-60`.")[0], False)

    def test_unattached_file_is_invented(self):
        self.assertIs(run("gr_no_invented_code", "See `src/db/schema.sql:12`.")[0], False)

    def test_citation_when_no_code_was_attached_is_invented(self):
        self.assertIs(run("gr_no_invented_code", "See `src/db/pool.py:40`.", {"code": []})[0], False)

    def test_log_text_in_backticks_is_not_a_code_citation(self):
        rca = "`HikariPool-1 - Connection is not available`, at `14:02:11Z`, trace `7f3a9c1e88`."
        self.assertEqual(run("gr_no_invented_code", rca, {"code": []})[0], "na")


class QuoteChecks(unittest.TestCase):
    def rca(self, line):
        return f"## Evidence\n`other.py:1` | `not code`\n\n## Code\n{line}\n\n## Timeline\n- `x.py:9` — `ignored`\n"

    def test_verbatim_quote_passes(self):
        self.assertTrue(run("gr_quotes_verbatim",
                            self.rca("- `src/db/pool.py:40` — `self.max_connections = 10` — hard cap"))[0])

    def test_whitespace_differences_are_ignored(self):
        self.assertTrue(run("gr_quotes_verbatim",
                            self.rca("- `src/db/pool.py:40` — `self.max_connections   =   10` — cap"))[0])

    def test_ellipsis_fragments_must_each_be_verbatim(self):
        ok = self.rca("- `src/db/pool.py:42-43` — `def acquire(self): … self.acquire_timeout_s)` — wait")
        self.assertTrue(run("gr_quotes_verbatim", ok)[0])
        bad = self.rca("- `src/db/pool.py:42-43` — `def acquire(self): … raise Timeout` — wait")
        self.assertIs(run("gr_quotes_verbatim", bad)[0], False)

    def test_paraphrase_presented_as_a_quote_fails(self):
        verdict, detail = run("gr_quotes_verbatim",
                              self.rca("- `src/db/pool.py:40` — `pool_size = 10` — hard cap"))
        self.assertIs(verdict, False)
        self.assertIn("not verbatim", detail)

    def test_real_line_cited_at_the_wrong_location_fails(self):
        # `acquire_timeout_s = 30` exists, but on line 41, not 40.
        self.assertIs(run("gr_quotes_verbatim",
                          self.rca("- `src/db/pool.py:40` — `self.acquire_timeout_s = 30` — t/o"))[0], False)

    def test_quote_from_unattached_location_fails(self):
        self.assertIs(run("gr_quotes_verbatim",
                          self.rca("- `src/db/pool.py:300` — `max = 10` — cap"))[0], False)

    def test_inline_code_in_the_explanation_is_not_a_quote(self):
        # Regression: `max_connections` in the "why" field was treated as a quote of
        # line 40, so a correct RCA failed a hard-fail check.
        rca = self.rca("- `src/db/pool.py:41` — `self.acquire_timeout_s = 30` — unlike `max_connections`, this is 30")
        self.assertTrue(run("gr_quotes_verbatim", rca)[0])

    def test_spaced_hyphen_also_separates_fields(self):
        rca = self.rca("- `src/db/pool.py:40` - `self.max_connections = 10` - see `acquire()`")
        self.assertTrue(run("gr_quotes_verbatim", rca)[0])

    def test_two_fragments_in_the_quote_field_are_one_quote(self):
        rca = self.rca("- `src/db/pool.py:40-41` — `self.max_connections = 10` … `self.acquire_timeout_s = 30` — both")
        self.assertTrue(run("gr_quotes_verbatim", rca)[0])
        rca = self.rca("- `src/db/pool.py:40-41` — `self.max_connections = 10` … `self.retries = 3` — both")
        self.assertIs(run("gr_quotes_verbatim", rca)[0], False)

    def test_na_without_a_code_section(self):
        # A `## Code` entry with a citation but no quote now fails; see ReviewFindings.
        self.assertEqual(run("gr_quotes_verbatim", "## Evidence\n`pool.py:40` — `x`")[0], "na")
        self.assertEqual(run("gr_quotes_verbatim", "## Code\nNo code was attached.\n")[0], "na")


class ReviewFindings(unittest.TestCase):
    """Regressions from the code review; each was reproduced before the fix."""

    def test_host_port_and_ip_port_are_not_code_citations(self):
        rca = "Connections to `db-primary.internal:5432` were refused; `10.0.4.12:8080` timed out."
        self.assertEqual(run("gr_no_invented_code", rca, {})[0], "na")  # ticket-only: nothing to grade
        self.assertTrue(run("gr_no_invented_code", rca)[0])  # with code attached: still not invented
        s = grounding.summarize(grounding.run_deterministic(rca, {}, SPEC), [], SPEC)
        self.assertFalse(s["hard_fail"])
        self.assertIsNone(s["score"])

    def test_stack_frame_quoted_from_the_logs_is_not_invented(self):
        bundle = {**BUNDLE, "entries": [{"message": "NullPointerException at PaymentClient.java:88",
                                         "attributes": {}}]}
        rca = "The trace shows `PaymentClient.java:88` raising; the cap is `src/db/pool.py:40`."
        self.assertTrue(run("gr_no_invented_code", rca, bundle)[0])

    def test_the_same_stack_frame_under_code_is_strict(self):
        bundle = {**BUNDLE, "entries": [{"message": "at PaymentClient.java:88", "attributes": {}}]}
        rca = "## Code\n- `PaymentClient.java:88` — `client.pay(order)` — throws\n"
        self.assertIs(run("gr_no_invented_code", rca, bundle)[0], False)

    def test_source_file_not_in_logs_or_code_is_still_invented(self):
        self.assertIs(run("gr_no_invented_code", "Root cause in `PaymentClient.java:88`.")[0], False)

    def test_hyphen_inside_a_quote_is_still_checked(self):
        bundle = {"code": [{"path": "src/db/pool.py", "start_line": 10, "text": "x = total - used\nreturn x"}]}
        ok = "## Code\n- `src/db/pool.py:10` — `x = total - used` — why\n"
        bad = "## Code\n- `src/db/pool.py:10` — `x = total - INVENTED` — why\n"
        self.assertTrue(run("gr_quotes_verbatim", ok, bundle)[0])
        self.assertIs(run("gr_quotes_verbatim", bad, bundle)[0], False)

    def test_colon_separator_is_accepted(self):
        rca = "## Code\n- `src/db/pool.py:40`: `self.max_connections = 10` — cap\n"
        self.assertTrue(run("gr_quotes_verbatim", rca)[0])

    def test_code_entry_with_no_quote_fails(self):
        verdict, detail = run("gr_quotes_verbatim", "## Code\n- `src/db/pool.py:40` — the cap\n")
        self.assertIs(verdict, False)
        self.assertIn("no quote", detail)

    def test_fragments_must_appear_in_order(self):
        rca = "## Code\n- `src/db/pool.py:42-43` — `self._wait(self.acquire_timeout_s)` … `def acquire(self):` — x\n"
        self.assertIs(run("gr_quotes_verbatim", rca)[0], False)

    def test_invented_directory_prefix_is_invented(self):
        self.assertIs(run("gr_no_invented_code", "See `totally/fake/src/db/pool.py:40`.")[0], False)
        self.assertTrue(run("gr_no_invented_code", "See `db/pool.py:40`.")[0])  # cited is a suffix: fine

    def test_scopes_evidence_is_na_with_nothing_to_compare(self):
        bundle = {"links": BUNDLE["links"]}  # no symptom window, no trace ids
        self.assertEqual(run("gr_link_scopes_evidence", f"See {GOOD}", bundle)[0], "na")


class Summary(unittest.TestCase):
    def good_rca(self):
        return (f"See [logs]({GOOD}).\n\n## Code\n"
                "- `src/db/pool.py:40` — `self.max_connections = 10` — cap\n")

    def test_clean_rca_scores_100_on_deterministic_checks(self):
        det = grounding.run_deterministic(self.good_rca(), BUNDLE, SPEC)
        s = grounding.summarize(det, [], SPEC)
        self.assertFalse(s["hard_fail"])
        self.assertEqual(s["fabricated"], [])
        failed = [c["id"] for c in s["checks"] if c["passed"] is False]
        self.assertEqual(failed, [])

    def test_fabrication_is_a_hard_fail_and_lowers_the_score(self):
        rca = self.good_rca() + "- `src/db/pool.py:999` — `retries = 5` — retry\n"
        s = grounding.summarize(grounding.run_deterministic(rca, BUNDLE, SPEC), [], SPEC)
        self.assertTrue(s["hard_fail"])
        self.assertIn("gr_no_invented_code", s["fabricated"])
        self.assertLess(s["score"], 100)

    def test_unscoped_link_is_a_miss_not_a_fabrication(self):
        rca = f"See {OTHER_DAY}.\n"
        s = grounding.summarize(grounding.run_deterministic(rca, BUNDLE, SPEC), [], SPEC)
        self.assertFalse(s["hard_fail"])
        self.assertLess(s["score"], 100)

    def test_nothing_attached_means_no_score_not_zero(self):
        det = grounding.run_deterministic("a ticket-only RCA", {}, SPEC)
        s = grounding.summarize(det, [], SPEC)
        self.assertIsNone(s["score"])
        self.assertEqual((s["passed"], s["total"], s["hard_fail"]), (0, 0, False))
        self.assertEqual(s["na"], len(SPEC["checks"]))

    def test_judged_verdicts_are_folded_in_and_na_for_the_rest(self):
        det = grounding.run_deterministic(self.good_rca(), BUNDLE, SPEC)
        judged = [{"id": "gr_code_supports_mechanism", "passed": False, "quote": "only related"}]
        s = grounding.summarize(det, judged, SPEC)
        by = {c["id"]: c for c in s["checks"]}
        self.assertIs(by["gr_code_supports_mechanism"]["passed"], False)
        self.assertEqual(by["gr_code_supports_mechanism"]["detail"], "only related")
        self.assertEqual(by["gr_log_to_code"]["passed"], "na")  # not judged this time
        self.assertFalse(s["hard_fail"])  # judged checks never hard-fail

    def test_checks_come_back_in_rubric_order(self):
        s = grounding.summarize(grounding.run_deterministic("x", BUNDLE, SPEC), [], SPEC)
        self.assertEqual([c["id"] for c in s["checks"]], [c["id"] for c in SPEC["checks"]])

    def test_applicable_judged_follows_what_is_attached(self):
        both = {c["id"] for c in grounding.applicable_judged(BUNDLE, SPEC)}
        self.assertEqual(both, {"gr_code_supports_mechanism", "gr_log_to_code", "gr_link_claim_matches"})
        only_links = {c["id"] for c in grounding.applicable_judged({"links": BUNDLE["links"]}, SPEC)}
        self.assertEqual(only_links, {"gr_link_claim_matches"})
        self.assertEqual(grounding.applicable_judged({}, SPEC), [])


if __name__ == "__main__":
    unittest.main()
