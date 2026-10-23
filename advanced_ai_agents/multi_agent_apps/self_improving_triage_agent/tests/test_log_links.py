"""Offline parsing of Logs Explorer links."""

import os
import sys
import unittest
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import log_links  # noqa: E402

QUERY = 'resource.labels.container_name="checkout" trace="projects/my-proj/traces/7f3a9c1e88"'


def gcp(query=QUERY, project="my-proj", **params):
    segs = "".join(f";{k}={quote(v, safe='')}" for k, v in params.items())
    return (f"https://console.cloud.google.com/logs/query;query={quote(query, safe='')}"
            f"{segs}?project={project}")


class ParseGcp(unittest.TestCase):
    def test_absolute_window_and_trace_id(self):
        p = log_links.parse_link(gcp(startTime="2026-09-18T14:00:00.000Z",
                                     endTime="2026-09-18T14:10:00.000Z"))
        self.assertEqual((p["vendor"], p["project"]), ("gcp", "my-proj"))
        self.assertEqual(p["query"], QUERY)
        self.assertEqual(p["trace_ids"], ["7f3a9c1e88"])
        self.assertEqual(p["start"], "2026-09-18T14:00:00+00:00")
        self.assertEqual(p["end"], "2026-09-18T14:10:00+00:00")
        self.assertTrue(p["pinned"])

    def test_time_range_with_slash_is_an_absolute_window(self):
        p = log_links.parse_link(gcp(timeRange="2026-09-18T14:00:00Z/2026-09-18T14:10:00Z"))
        self.assertEqual((p["start"], p["end"]),
                         ("2026-09-18T14:00:00+00:00", "2026-09-18T14:10:00+00:00"))
        self.assertTrue(p["pinned"])

    def test_cursor_alone_is_pinned(self):
        p = log_links.parse_link(gcp(cursorTimestamp="2026-09-18T14:02:11.123456Z", duration="PT1H"))
        self.assertTrue(p["pinned"])
        self.assertEqual(p["duration"], "PT1H")
        self.assertIsNone(p["start"])

    def test_relative_range_is_not_pinned(self):
        p = log_links.parse_link(gcp(timeRange="PT1H"))
        self.assertFalse(p["pinned"])
        self.assertEqual(p["duration"], "PT1H")

    def test_no_time_at_all_is_not_pinned(self):
        self.assertFalse(log_links.parse_link(gcp())["pinned"])

    def test_alternative_trace_filter_forms(self):
        for q, want in [
            ('jsonPayload.traceId="abc123"', ["abc123"]),
            ('jsonPayload.trace_id=abc-123', ["abc-123"]),
            ('logging.googleapis.com/trace="projects/p/traces/DEAD00beef"', ["DEAD00beef"]),
            ('severity>=ERROR', []),
        ]:
            self.assertEqual(log_links.parse_link(gcp(query=q))["trace_ids"], want, q)

    def test_non_logs_urls_are_rejected(self):
        self.assertIsNone(log_links.parse_link("https://example.com/logs/query;query=x"))
        self.assertIsNone(log_links.parse_link("https://console.cloud.google.com/compute/instances"))


class FindLinks(unittest.TestCase):
    def test_finds_links_in_markdown_and_strips_trailing_punctuation(self):
        a = gcp(startTime="2026-09-18T14:00:00Z", endTime="2026-09-18T14:10:00Z")
        b = gcp(query='severity>=ERROR', cursorTimestamp="2026-09-18T14:02:11Z")
        text = f"See [the trace]({a}) and also {b}. Done."
        found = log_links.find_links(text)
        self.assertEqual(len(found), 2)
        self.assertEqual(found[1]["cursor"], "2026-09-18T14:02:11+00:00")

    def test_same_link_twice_is_one_link(self):
        a = gcp(startTime="2026-09-18T14:00:00Z", endTime="2026-09-18T14:10:00Z")
        self.assertEqual(len(log_links.find_links(f"{a} then again {a}")), 1)

    def test_reencoded_link_has_the_same_key(self):
        a = gcp(startTime="2026-09-18T14:00:00Z", endTime="2026-09-18T14:10:00Z")
        b = a.replace("%22", '"')  # same query, written with raw quotes
        ka, kb = (log_links.link_key(log_links.parse_link(u)) for u in (a, b))
        self.assertEqual(ka, kb)

    def test_no_links(self):
        self.assertEqual(log_links.find_links("no links here"), [])


class ReviewFindings(unittest.TestCase):
    """Regressions from the code review; each was reproduced before the fix."""

    BASE = "https://console.cloud.google.com/logs"

    def test_old_viewer_links_with_different_filters_get_different_keys(self):
        a = f"{self.BASE}/viewer?project=p&advancedFilter=resource.type%3D%22gce%22"
        b = f"{self.BASE}/viewer?project=p&advancedFilter=INVENTED"
        pa, pb = log_links.parse_link(a), log_links.parse_link(b)
        self.assertEqual(pa["query"], 'resource.type="gce"')
        self.assertNotEqual(log_links.link_key(pa), log_links.link_key(pb))

    def test_query_string_form_is_parsed_like_the_path_form(self):
        q = f"{self.BASE}/query?project=p&query={quote(QUERY, safe='')}" \
            "&startTime=2026-09-18T14:00:00Z&endTime=2026-09-18T14:10:00Z"
        p = log_links.parse_link(q)
        self.assertEqual((p["query"], p["trace_ids"], p["pinned"]), (QUERY, ["7f3a9c1e88"], True))

    def test_links_with_no_query_never_collide(self):
        a = log_links.parse_link(f"{self.BASE}/query?project=p&foo=1")
        b = log_links.parse_link(f"{self.BASE}/query?project=p&foo=2")
        self.assertNotEqual(log_links.link_key(a), log_links.link_key(b))

    def test_raw_parentheses_and_quotes_round_trip(self):
        # As a browser writes it: `>`, `=` and spaces encoded, `( ) '` left raw.
        url = (f"{self.BASE}/query;query=(severity%3E%3DERROR)%20AND%20jsonPayload.user%3D'bob'"
               ";startTime=2026-09-18T14:00:00Z;endTime=2026-09-18T14:10:00Z?project=p")
        attached = log_links.parse_link(url)
        self.assertEqual(attached["query"], "(severity>=ERROR) AND jsonPayload.user='bob'")
        found = log_links.find_links(f"See [the logs]({url}).")
        self.assertEqual(len(found), 1)
        self.assertEqual(log_links.link_key(found[0]), log_links.link_key(attached))

    def test_round_trips_helper(self):
        self.assertTrue(log_links.round_trips(gcp(startTime="2026-09-18T14:00:00Z",
                                                  endTime="2026-09-18T14:10:00Z")))


class Coverage(unittest.TestCase):
    SYMPTOM = {"start": "2026-09-18T14:01:02+00:00", "end": "2026-09-18T14:07:44+00:00"}

    def test_window_overlapping_symptom(self):
        p = log_links.parse_link(gcp(startTime="2026-09-18T14:00:00Z", endTime="2026-09-18T14:10:00Z"))
        self.assertTrue(log_links.covers_symptom(p, self.SYMPTOM))

    def test_window_on_another_day(self):
        p = log_links.parse_link(gcp(startTime="2026-09-17T14:00:00Z", endTime="2026-09-17T14:10:00Z"))
        self.assertFalse(log_links.covers_symptom(p, self.SYMPTOM))

    def test_cursor_inside_and_outside(self):
        near = log_links.parse_link(gcp(cursorTimestamp="2026-09-18T14:02:11Z"))
        far = log_links.parse_link(gcp(cursorTimestamp="2026-09-18T18:00:00Z"))
        self.assertTrue(log_links.covers_symptom(near, self.SYMPTOM))
        self.assertFalse(log_links.covers_symptom(far, self.SYMPTOM))

    def test_undecidable_cases_are_none(self):
        p = log_links.parse_link(gcp(timeRange="PT1H"))
        self.assertIsNone(log_links.covers_symptom(p, self.SYMPTOM))
        win = log_links.parse_link(gcp(startTime="2026-09-18T14:00:00Z", endTime="2026-09-18T14:10:00Z"))
        self.assertIsNone(log_links.covers_symptom(win, None))

    def test_describe_flags_unpinned(self):
        self.assertIn("not pinned", log_links.describe(log_links.parse_link(gcp(timeRange="PT1H"))))


if __name__ == "__main__":
    unittest.main()
