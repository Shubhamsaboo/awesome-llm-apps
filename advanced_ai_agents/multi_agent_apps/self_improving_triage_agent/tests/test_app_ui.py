"""Streamlit UI: backend switch and the Sessions tab with human feedback.

Headless via AppTest. The span store points at a temp file; `claude` is a fake
executable so the Claude Code option can be exercised without a login.
"""

import os
import stat
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "optimizer", "app.py")
sys.path.insert(0, os.path.join(ROOT, "optimizer"))

import telemetry  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

_tmp = None
_old_path = None


def setUpModule():
    global _tmp, _old_path
    _tmp = tempfile.TemporaryDirectory()
    _old_path = telemetry.store.path
    telemetry.init(os.path.join(_tmp.name, "ui.db"))


def tearDownModule():
    telemetry.store.path = _old_path
    _tmp.cleanup()


def _app():
    return AppTest.from_file(APP, default_timeout=60).run()


def _seed_session():
    with telemetry.span("optimizer.session", **{
            "triage.model": "claude_code/sonnet", "triage.backend": "claude_code",
            "triage.baseline_score": 50.0, "triage.final_score": 75.0}) as root:
        with telemetry.span("optimizer.baseline", **{"triage.score": 50.0}):
            with telemetry.span("llm.call", **{
                    "triage.role": "executor.route", "triage.system_prompt": "SYS",
                    "triage.user_prompt": "USR", "triage.response": '{"team": "A"}',
                    "gen_ai.usage.input_tokens": 11, "gen_ai.usage.output_tokens": 4}) as call:
                pass
        with telemetry.span("optimizer.round", **{
                "triage.round": 1, "triage.kept": True, "triage.strategy": "add_routing_rule",
                "triage.description": "route DB timeouts to Platform",
                "triage.score_before": 50.0, "triage.score_after": 75.0}) as rnd:
            with telemetry.span("llm.call", **{"triage.role": "analyst"}):
                pass
    fmt = lambda sp, w: format(getattr(sp.get_span_context(), w), "032x" if w == "trace_id" else "016x")
    return fmt(root, "trace_id"), fmt(root, "span_id"), fmt(call, "span_id"), fmt(rnd, "span_id")


class BackendSwitch(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.dir.cleanup()

    def _fake_claude(self):
        path = os.path.join(self.dir.name, "claude")
        with open(path, "w") as f:
            f.write("#!/bin/sh\nexit 0\n")
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
        return path

    def test_three_backends_offered_copilot_default(self):
        at = _app()
        self.assertFalse(at.exception)
        seg = at.button_group(key="backend")
        self.assertEqual(seg.value, "GitHub Copilot")
        self.assertEqual(list(seg.options_labels) if hasattr(seg, "options_labels") else
                         [o.content for o in seg.proto.options],
                         ["GitHub Copilot", "Claude Code", "API key"])

    def test_claude_code_backend_ready_when_cli_found(self):
        with mock.patch.dict(os.environ, {"TRIAGE_CLAUDE_BIN": self._fake_claude()}):
            at = _app()
            at.button_group(key="backend").set_value("Claude Code").run()
            self.assertFalse(at.exception)
            self.assertEqual(at.selectbox(key="claude-code-model").options, ["sonnet", "opus", "haiku"])
            self.assertTrue(any("Claude Code login" in s.value for s in at.success))
            start = next(b for b in at.button if b.label == "Start optimization")
            self.assertFalse(start.disabled)  # golden set + teams load from references/

    def test_claude_code_backend_blocked_without_cli(self):
        missing = os.path.join(self.dir.name, "no-such-claude")
        with mock.patch.dict(os.environ, {"TRIAGE_CLAUDE_BIN": missing}):
            at = _app()
            at.button_group(key="backend").set_value("Claude Code").run()
            self.assertTrue(any("not found" in w.value for w in at.warning))
            start = next(b for b in at.button if b.label == "Start optimization")
            self.assertTrue(start.disabled)

    def test_api_key_backend_still_available(self):
        at = _app()
        at.button_group(key="backend").set_value("API key").run()
        self.assertFalse(at.exception)
        self.assertEqual(at.selectbox(key="key-provider").options, ["OpenAI", "Anthropic", "Google"])


class SessionsTab(unittest.TestCase):
    def test_seeded_session_renders_with_metrics_and_content(self):
        tid, *_ = _seed_session()
        at = _app()
        self.assertFalse(at.exception)
        at.selectbox(key="sessions-pick").set_value(tid).run()
        metrics = {m.label: m.value for m in at.metric}
        self.assertEqual(metrics["Backend"], "claude_code")
        self.assertEqual(metrics["LLM calls"], "2")
        self.assertEqual(metrics["Score"], "75.0%")
        self.assertIn('{"team": "A"}', [c.value for c in at.code])

    def test_session_whose_root_is_a_single_call_renders(self):
        # "Generate scenarios" used to trace as one bare llm.call: it was the root
        # and the only call, so the session form and the call form shared a key
        # (StreamlitDuplicateElementKey). Old traces in the store still look like this.
        with telemetry.span("llm.call", **{"triage.role": "generate",
                                           "triage.response": "{}"}) as call:
            pass
        tid = format(call.get_span_context().trace_id, "032x")
        at = _app()
        at.selectbox(key="sessions-pick").set_value(tid).run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertEqual(sum(1 for b in at.button if b.label == "Save feedback"), 1)

    def test_same_second_sessions_get_distinct_labels(self):
        # Two runs started in the same second with the same backend and model used
        # to share a label, so picking one could display the other.
        a, *_ = _seed_session()
        b, *_ = _seed_session()
        at = _app()
        pick = at.selectbox(key="sessions-pick")
        labels = pick.options
        self.assertEqual(len(labels), len(set(labels)))
        pick.set_value(b).run()
        self.assertEqual(at.selectbox(key="sessions-pick").value, b)
        self.assertIn(f"step-{b}", [getattr(x, "key", None) for x in at.selectbox])

    def test_round_step_shows_strategy(self):
        tid, *_ = _seed_session()
        at = _app()
        at.selectbox(key="sessions-pick").set_value(tid).run()
        step = at.selectbox(key=f"step-{tid}")
        round_label = next(o for o in step.options if o.startswith("Round 1"))
        self.assertIn("kept", round_label)
        step.set_value(round_label).run()
        self.assertFalse(at.exception)
        self.assertTrue(any("route DB timeouts to Platform" in m.value for m in at.markdown))

    def test_call_feedback_is_saved(self):
        tid, _, call_id, _ = _seed_session()
        at = _app()
        at.selectbox(key="sessions-pick").set_value(tid).run()
        # Form keys are "<target>-<span_id>" so one span can carry two forms.
        key = f"call-{call_id}"
        fb = next(f for f in at.get("feedback") if f.proto.id.endswith(f"fb-rating-{key}")
                  or getattr(f, "key", None) == f"fb-rating-{key}")
        fb.set_value(0)
        at.text_input(key=f"fb-comment-{key}").set_value("should be Platform")
        submit = next(b for b in at.button if b.label == "Save feedback"
                      and b.proto.form_id.endswith(f"fb-{key}"))
        submit.click().run()
        self.assertFalse(at.exception)
        saved = telemetry.store.latest_feedback(tid)[call_id]
        self.assertEqual((saved["target"], saved["rating"], saved["comment"]),
                         ("call", 0, "should be Platform"))

    def test_empty_feedback_is_rejected(self):
        tid, _, call_id, _ = _seed_session()
        at = _app()
        at.selectbox(key="sessions-pick").set_value(tid).run()
        submit = next(b for b in at.button if b.label == "Save feedback"
                      and b.proto.form_id.endswith(f"fb-call-{call_id}"))
        submit.click().run()
        self.assertTrue(any("Pick a thumb" in w.value for w in at.warning))
        self.assertNotIn(call_id, telemetry.store.latest_feedback(tid))


if __name__ == "__main__":
    unittest.main()
