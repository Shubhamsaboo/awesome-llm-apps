"""Tests for the OpenTelemetry layer: span nesting, storage, feedback.

No network. The store is pointed at a temp file.
"""

import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "optimizer"))

import telemetry  # noqa: E402

_tmp = None
_old_path = None


def setUpModule():
    global _tmp, _old_path
    _tmp = tempfile.TemporaryDirectory()
    _old_path = telemetry.store.path
    telemetry.init(os.path.join(_tmp.name, "t.db"))


def tearDownModule():
    telemetry.store.path = _old_path
    _tmp.cleanup()


def _ids(sp):
    ctx = sp.get_span_context()
    return format(ctx.trace_id, "032x"), format(ctx.span_id, "016x")


class SpanStorage(unittest.TestCase):
    def test_nested_spans_share_a_trace_and_link_to_parents(self):
        with telemetry.span("optimizer.session", **{"triage.model": "m", "triage.backend": "x"}) as root:
            with telemetry.span("optimizer.round", round=1) as rnd:
                with telemetry.span("llm.call", **{"gen_ai.usage.input_tokens": 5,
                                                   "gen_ai.usage.output_tokens": 2}) as call:
                    pass
        trace_id, root_id = _ids(root)
        spans = {s["name"]: s for s in telemetry.store.spans(trace_id)}
        self.assertEqual(set(spans), {"optimizer.session", "optimizer.round", "llm.call"})
        self.assertIsNone(spans["optimizer.session"]["parent_id"])
        self.assertEqual(spans["optimizer.round"]["parent_id"], root_id)
        self.assertEqual(spans["llm.call"]["parent_id"], _ids(rnd)[1])
        self.assertEqual(spans["llm.call"]["attributes"]["gen_ai.usage.input_tokens"], 5)

    def test_exception_marks_span_error(self):
        with self.assertRaises(ValueError):
            with telemetry.span("llm.call") as sp:
                raise ValueError("boom")
        spans = telemetry.store.spans(_ids(sp)[0])
        self.assertEqual(spans[0]["status"], "ERROR")
        self.assertTrue(any(e["name"] == "exception" for e in spans[0]["events"]))

    def test_none_attributes_are_skipped(self):
        with telemetry.span("llm.call", skipped=None, kept="yes") as sp:
            pass
        attrs = telemetry.store.spans(_ids(sp)[0])[0]["attributes"]
        self.assertNotIn("skipped", attrs)
        self.assertEqual(attrs["kept"], "yes")


class Feedback(unittest.TestCase):
    def _call(self):
        with telemetry.span("optimizer.session", **{"triage.model": "m"}) as root:
            with telemetry.span("llm.call") as call:
                pass
        return _ids(root), _ids(call)

    def test_feedback_is_stored_and_latest_wins(self):
        (tid, _), (_, call_id) = self._call()
        telemetry.record_feedback(tid, call_id, "call", 0, "wrong team")
        telemetry.record_feedback(tid, call_id, "call", 1, "actually fine")
        latest = telemetry.store.latest_feedback(tid)[call_id]
        self.assertEqual((latest["rating"], latest["comment"]), (1, "actually fine"))
        self.assertEqual(len(telemetry.store.feedback(tid)), 2)

    def test_feedback_span_is_a_child_of_the_rated_span(self):
        (tid, _), (_, call_id) = self._call()
        telemetry.record_feedback(tid, call_id, "call", 1, "ok")
        fb = [s for s in telemetry.store.spans(tid) if s["name"] == telemetry.FEEDBACK_SPAN]
        self.assertEqual(len(fb), 1)
        self.assertEqual(fb[0]["parent_id"], call_id)
        self.assertEqual(fb[0]["attributes"]["feedback.rating"], 1)

    def test_comment_only_feedback_has_no_rating(self):
        (tid, root_id), _ = self._call()
        telemetry.record_feedback(tid, root_id, "session", None, "just a note")
        self.assertIsNone(telemetry.store.latest_feedback(tid)[root_id]["rating"])


class SessionListing(unittest.TestCase):
    def test_summary_counts_calls_tokens_and_ratings(self):
        with telemetry.span("optimizer.session", **{"triage.model": "demo", "triage.backend": "copilot"}) as root:
            for _ in range(2):
                with telemetry.span("llm.call", **{"gen_ai.usage.input_tokens": 10,
                                                   "gen_ai.usage.output_tokens": 3}) as call:
                    pass
        tid, root_id = _ids(root)
        telemetry.record_feedback(tid, _ids(call)[1], "call", 1)
        row = next(s for s in telemetry.store.sessions() if s["trace_id"] == tid)
        self.assertEqual((row["name"], row["model"], row["backend"]),
                         ("optimizer.session", "demo", "copilot"))
        self.assertEqual((row["calls"], row["input_tokens"], row["output_tokens"], row["rated"]),
                         (2, 20, 6, 1))

    def test_feedback_spans_do_not_count_as_calls_or_roots(self):
        with telemetry.span("optimizer.session") as root:
            pass
        tid, root_id = _ids(root)
        telemetry.record_feedback(tid, root_id, "session", 1)
        row = next(s for s in telemetry.store.sessions() if s["trace_id"] == tid)
        self.assertEqual((row["name"], row["calls"]), ("optimizer.session", 0))


class Content(unittest.TestCase):
    def test_clip_limits_long_text(self):
        out = telemetry.clip("x" * 50, limit=10)
        self.assertTrue(out.startswith("x" * 10))
        self.assertIn("50 chars total", out)

    def test_content_recording_can_be_disabled(self):
        old = os.environ.get("TRIAGE_TRACE_CONTENT")
        os.environ["TRIAGE_TRACE_CONTENT"] = "0"
        try:
            self.assertFalse(telemetry.record_content())
        finally:
            if old is None:
                os.environ.pop("TRIAGE_TRACE_CONTENT")
            else:
                os.environ["TRIAGE_TRACE_CONTENT"] = old
        self.assertTrue(telemetry.record_content())


_OTLP_SCRIPT = """
import sys
sys.path.insert(0, {optimizer!r})
import telemetry
with telemetry.span("optimizer.session") as root:
    with telemetry.span("llm.call") as call:
        pass
tid = format(root.get_span_context().trace_id, "032x")
sid = format(call.get_span_context().span_id, "016x")
telemetry.record_feedback(tid, sid, "call", 1, "ok")
"""


class OtlpExport(unittest.TestCase):
    """With OTEL_EXPORTER_OTLP_ENDPOINT set, spans also reach a collector over OTLP/HTTP.

    Local only: a throwaway HTTP server on 127.0.0.1 stands in for the collector.
    """

    def test_spans_and_feedback_are_posted_to_the_collector(self):
        import http.server
        import subprocess
        import threading

        received = []

        class Collector(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                received.append((self.path, body))
                self.send_response(200)
                self.end_headers()

            def log_message(self, *args):
                pass

        srv = http.server.HTTPServer(("127.0.0.1", 0), Collector)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            env = {**os.environ,
                   "OTEL_EXPORTER_OTLP_ENDPOINT": f"http://127.0.0.1:{srv.server_port}",
                   "TRIAGE_TRACE_DB": os.path.join(_tmp.name, "otlp.db")}
            out = subprocess.run(
                [sys.executable, "-c", _OTLP_SCRIPT.format(optimizer=os.path.join(ROOT, "optimizer"))],
                env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(out.returncode, 0, out.stderr)
        finally:
            srv.shutdown()
            srv.server_close()

        self.assertTrue(received, "collector received nothing")
        self.assertTrue(all(path == "/v1/traces" for path, _ in received))
        payload = b"".join(body for _, body in received)
        for name in (b"optimizer.session", b"llm.call", b"human.feedback", b"triage-agent"):
            self.assertIn(name, payload)


if __name__ == "__main__":
    unittest.main()
