"""Backend selection (provider API via LiteLLM or Claude Code) and full-run tracing.

No network and no subscription use: `claude` is replaced by a fake executable and
`litellm.acompletion` by a stub.
"""

import json
import os
import stat
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "optimizer"))

import telemetry  # noqa: E402
import triage_optimizer  # noqa: E402
from triage_optimizer import TriageOptimizer  # noqa: E402

FAKE_CLAUDE = """#!{python}
import json, os, sys, time
args = sys.argv[1:]
stdin = sys.stdin.read()
json.dump({{"args": args, "stdin": stdin, "cwd": os.getcwd(), "ls": os.listdir(".")}},
          open(os.environ["FAKE_CLAUDE_RECORD"], "w"))
mode = os.environ.get("FAKE_CLAUDE_MODE", "ok")
if mode == "ok":
    print(json.dumps({{
        "result": '{{"team": "B"}}', "is_error": False, "total_cost_usd": 0.01,
        "usage": {{"input_tokens": 2, "cache_creation_input_tokens": 10,
                   "cache_read_input_tokens": 5, "output_tokens": 4}},
        "modelUsage": {{"claude-haiku-4-5": {{"costUSD": 0.001}},
                        "claude-sonnet-5-5": {{"costUSD": 0.009}}}},
    }}))
elif mode == "error":
    print(json.dumps({{"is_error": True, "result": "rate limited"}})); sys.exit(1)
elif mode == "garbage":
    print("not json"); sys.exit(2)
elif mode == "hang":
    time.sleep(30)
"""

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


def _trace_id(sp):
    return format(sp.get_span_context().trace_id, "032x")


def _fake_completion(**kwargs):
    async def acompletion(model, messages, temperature):
        content = kwargs["respond"](messages)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
            usage=SimpleNamespace(prompt_tokens=7, completion_tokens=3),
        )
    return acompletion


class ClaudeCodeBackend(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.bin = os.path.join(self.dir.name, "claude")
        with open(self.bin, "w") as f:
            f.write(FAKE_CLAUDE.format(python=sys.executable))
        os.chmod(self.bin, os.stat(self.bin).st_mode | stat.S_IEXEC)
        self.record = os.path.join(self.dir.name, "record.json")
        self.env = mock.patch.dict(os.environ, {
            "TRIAGE_CLAUDE_BIN": self.bin, "FAKE_CLAUDE_RECORD": self.record,
            "FAKE_CLAUDE_MODE": "ok"})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.dir.cleanup()

    def _recorded(self):
        with open(self.record) as f:
            return json.load(f)

    async def test_call_is_isolated_and_parsed(self):
        opt = TriageOptimizer(model="claude_code/sonnet")
        with telemetry.span("test.root") as root:
            text = await opt._ask("SYSTEM TEXT", "USER TEXT", role="executor.route")
        self.assertEqual(json.loads(text), {"team": "B"})

        rec = self._recorded()
        a = rec["args"]
        self.assertIn("-p", a)
        self.assertEqual(a[a.index("--model") + 1], "sonnet")
        self.assertEqual(a[a.index("--tools") + 1], "")  # no tools
        self.assertEqual(a[a.index("--setting-sources") + 1], "")  # no hooks/settings
        self.assertEqual(a[a.index("--system-prompt") + 1], "SYSTEM TEXT")
        for flag in ("--no-session-persistence", "--disable-slash-commands", "--strict-mcp-config"):
            self.assertIn(flag, a)
        self.assertNotIn("--bare", a)  # --bare would require an API key
        self.assertEqual(rec["stdin"], "USER TEXT")  # prompt via stdin, not argv
        self.assertEqual(rec["ls"], [])  # empty cwd: no CLAUDE.md to leak in

        call = next(s for s in telemetry.store.spans(_trace_id(root)) if s["name"] == "llm.call")
        at = call["attributes"]
        self.assertEqual(at["triage.backend"], "claude_code")
        self.assertEqual(at["triage.role"], "executor.route")
        self.assertEqual(at["gen_ai.usage.input_tokens"], 17)  # 2 + 10 + 5 cached
        self.assertEqual(at["gen_ai.usage.output_tokens"], 4)
        self.assertEqual(at["gen_ai.response.model"], "claude-sonnet-5-5")  # not the haiku helper
        self.assertEqual(at["triage.cost_usd"], 0.01)
        self.assertEqual(at["triage.user_prompt"], "USER TEXT")

    async def test_cli_reported_error_raises_and_span_is_error(self):
        os.environ["FAKE_CLAUDE_MODE"] = "error"
        opt = TriageOptimizer(model="claude_code/opus")
        with telemetry.span("test.root") as root:
            with self.assertRaisesRegex(RuntimeError, "rate limited"):
                await opt._ask("s", "u")
        call = next(s for s in telemetry.store.spans(_trace_id(root)) if s["name"] == "llm.call")
        self.assertEqual(call["status"], "ERROR")

    async def test_non_json_output_raises_with_context(self):
        os.environ["FAKE_CLAUDE_MODE"] = "garbage"
        with self.assertRaisesRegex(RuntimeError, "without JSON"):
            await TriageOptimizer(model="claude_code/haiku")._ask("s", "u")

    async def test_timeout_kills_the_process(self):
        os.environ["FAKE_CLAUDE_MODE"] = "hang"
        with mock.patch.object(triage_optimizer, "CLAUDE_CODE_TIMEOUT_S", 0.5):
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                await TriageOptimizer(model="claude_code/sonnet")._ask("s", "u")

    async def test_content_recording_can_be_turned_off(self):
        os.environ["TRIAGE_TRACE_CONTENT"] = "0"
        try:
            with telemetry.span("test.root") as root:
                await TriageOptimizer(model="claude_code/sonnet")._ask("secret sys", "secret user")
        finally:
            os.environ.pop("TRIAGE_TRACE_CONTENT")
        at = next(s for s in telemetry.store.spans(_trace_id(root)) if s["name"] == "llm.call")["attributes"]
        self.assertNotIn("triage.user_prompt", at)
        self.assertNotIn("triage.response", at)
        self.assertEqual(at["triage.prompt_chars"], len("secret sys") + len("secret user"))


class CliTrace(unittest.TestCase):
    """score_routing.py as a real subprocess on the Claude Code backend: one session."""

    # Same fake `claude` setup, without inheriting (and re-running) those tests.
    setUp = ClaudeCodeBackend.setUp
    tearDown = ClaudeCodeBackend.tearDown

    def test_score_routing_cli_is_one_traced_session(self):
        import subprocess

        skill = os.path.join(self.dir.name, "SKILL.md")
        golden = os.path.join(self.dir.name, "golden.json")
        db = os.path.join(self.dir.name, "cli.db")
        with open(skill, "w") as f:
            f.write("route everything to B")
        with open(golden, "w") as f:
            json.dump({"teams": ["A", "B"], "evals": [{"id": 1, "name": "team_correct"}],
                       "scenarios": [{"id": i, "name": f"s{i}", "input": "x",
                                      "expected_team": "B"} for i in (1, 2)]}, f)
        env = {**os.environ, "TRIAGE_TRACE_DB": db}
        out = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "score_routing.py"),
             "--model", "claude_code/sonnet", "--skill", skill, "--golden", golden,
             "--min-accuracy", "100"],
            env=env, capture_output=True, text=True, timeout=120)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("100.0%", out.stdout)

        store = telemetry.Store(db)
        sessions = store.sessions()
        self.assertEqual(len(sessions), 1)
        s = sessions[0]
        self.assertEqual((s["name"], s["backend"], s["calls"]),
                         ("cli.score_routing", "claude_code", 2))


_IMPORT_UNDER_LOGGING = """
import logging, sys, threading, time
sys.path.insert(0, {optimizer!r})
stop = False

def noisy():  # stands in for Streamlit's server thread logging asyncio errors
    log = logging.getLogger("asyncio")
    while not stop:
        log.error("Exception in default exception handler")
        time.sleep(0.005)

threading.Thread(target=noisy, daemon=True).start()
before = logging.root.manager.disable
import triage_optimizer
stop = True
import litellm
print("disable_restored", logging.root.manager.disable == before)
print("redaction_on", litellm._logging._ENABLE_SECRET_REDACTION is True)
"""


class ImportDeadlock(unittest.TestCase):
    def test_litellm_imports_while_another_thread_logs(self):
        # Without TriageOptimizer's guarded import, LiteLLM's redaction filter ran on
        # the logging thread, lazily imported a module the importing thread held, and
        # Python raised _DeadlockError (4 of 4 runs when reproduced).
        import subprocess

        out = subprocess.run(
            [sys.executable, "-c", _IMPORT_UNDER_LOGGING.format(
                optimizer=os.path.join(ROOT, "optimizer"))],
            capture_output=True, text=True, timeout=120)
        self.assertEqual(out.returncode, 0, out.stderr[-1500:])
        self.assertNotIn("DeadlockError", out.stderr)
        self.assertIn("disable_restored True", out.stdout)  # logging not left switched off
        self.assertIn("redaction_on True", out.stdout)  # the guard did not weaken redaction


class ImportGuard(unittest.TestCase):
    def test_works_when_litellm_lacks_the_private_filter(self):
        # Review finding: on a LiteLLM without `_logging._secret_filter` the warm-up
        # raised AttributeError and every entry point failed to import.
        import logging
        from types import SimpleNamespace

        stub = SimpleNamespace(__name__="litellm")  # no _logging attribute at all
        before = logging.root.manager.disable
        with mock.patch.object(triage_optimizer.importlib, "import_module", return_value=stub):
            self.assertIs(triage_optimizer._import_litellm(), stub)
        self.assertEqual(logging.root.manager.disable, before)

    def test_import_error_propagates_and_logging_is_restored(self):
        import logging

        before = logging.root.manager.disable
        with mock.patch.object(triage_optimizer.importlib, "import_module",
                               side_effect=ImportError("no litellm")):
            with self.assertRaisesRegex(ImportError, "no litellm"):
                triage_optimizer._import_litellm()
        self.assertEqual(logging.root.manager.disable, before)


class BackendNames(unittest.TestCase):
    def test_backend_per_model_prefix(self):
        self.assertEqual(TriageOptimizer(model="claude_code/sonnet").backend, "claude_code")
        self.assertEqual(TriageOptimizer(model="gpt-4o-mini").backend, "litellm")

    def test_claude_code_model_never_sets_an_api_key(self):
        saved = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            TriageOptimizer(model="claude_code/sonnet", api_key="sk-x")
            self.assertNotIn("ANTHROPIC_API_KEY", os.environ)
        finally:
            if saved is not None:
                os.environ["ANTHROPIC_API_KEY"] = saved


class LiteLLMPathTracing(unittest.IsolatedAsyncioTestCase):
    async def test_litellm_path_records_usage_and_role(self):
        fake = _fake_completion(respond=lambda m: '{"ok": true}')
        opt = TriageOptimizer(model="gpt-4o-mini")
        with mock.patch.object(triage_optimizer.litellm, "acompletion", fake):
            with telemetry.span("test.root") as root:
                out = await opt._ask_json("sys", "usr", role="analyst")
        self.assertEqual(out, {"ok": True})
        at = next(s for s in telemetry.store.spans(_trace_id(root)) if s["name"] == "llm.call")["attributes"]
        self.assertEqual((at["triage.backend"], at["triage.role"]), ("litellm", "analyst"))
        self.assertEqual((at["gen_ai.usage.input_tokens"], at["gen_ai.usage.output_tokens"]), (7, 3))


class FullRunTrace(unittest.IsolatedAsyncioTestCase):
    """One optimize() run: the loop fixes a mis-route, and the trace shows how."""

    def _respond(self, messages):
        system, user = messages[0]["content"], messages[1]["content"]
        if "execution agent" in system:
            team = "B" if "FIXED" in user else "A"  # wrong until the skill is mutated
            return json.dumps({"team": team, "severity": "P2", "reasoning": "r", "confidence": 1})
        if "diagnose" in system.lower():
            return json.dumps({"diagnosis": "d", "mutation_strategy": "add_routing_rule",
                               "target_section": "t", "suggested_change": "c"})
        return json.dumps({"description": "add rule", "reasoning": "why",
                           "new_skill_md": "---\nname: s\n---\nFIXED"})

    async def test_run_produces_session_baseline_round_and_calls(self):
        opt = TriageOptimizer(model="gpt-4o-mini", concurrency=2)
        scenarios = [{"id": 1, "name": "n", "input": "boom", "expected_team": "B",
                      "expected_severity": "P2"}]
        evals = [{"id": 1, "name": "team_correct"}]
        events = []

        async def cb(ev):
            events.append(ev["type"])

        with mock.patch.object(triage_optimizer.litellm, "acompletion",
                               _fake_completion(respond=self._respond)):
            payload = await opt.optimize("---\nname: s\n---\nold", {"teams": ["A", "B"]},
                                         scenarios, evals, max_rounds=3, callback=cb)

        self.assertEqual((payload["baseline_score"], payload["final_score"]), (0.0, 100.0))
        self.assertIn("complete", events)

        sessions = [s for s in telemetry.store.sessions()
                    if s["name"] == "optimizer.session" and s["calls"] >= 4]
        self.assertTrue(sessions)
        tid = sessions[0]["trace_id"]
        spans = telemetry.store.spans(tid)
        by_name = {}
        for s in spans:
            by_name.setdefault(s["name"], []).append(s)

        root = by_name["optimizer.session"][0]
        self.assertIsNone(root["parent_id"])
        self.assertEqual(root["attributes"]["triage.baseline_score"], 0.0)
        self.assertEqual(root["attributes"]["triage.final_score"], 100.0)
        self.assertEqual(root["attributes"]["triage.backend"], "litellm")

        baseline = by_name["optimizer.baseline"][0]
        rnd = by_name["optimizer.round"][0]
        self.assertEqual(baseline["parent_id"], root["span_id"])
        self.assertEqual(rnd["parent_id"], root["span_id"])
        self.assertTrue(rnd["attributes"]["triage.kept"])
        self.assertEqual(rnd["attributes"]["triage.strategy"], "add_routing_rule")

        roles = {c["attributes"]["triage.role"]: c for c in by_name["llm.call"]}
        self.assertEqual(set(roles), {"executor.route", "analyst", "mutator"})
        parents = {c["attributes"]["triage.role"]: c["parent_id"] for c in by_name["llm.call"]}
        self.assertEqual(roles["analyst"]["parent_id"], rnd["span_id"])
        self.assertEqual(roles["mutator"]["parent_id"], rnd["span_id"])
        # Executor calls run in asyncio.gather tasks: they must still nest under a
        # baseline or round span, not become orphan traces.
        route_parents = {c["parent_id"] for c in by_name["llm.call"]
                         if c["attributes"]["triage.role"] == "executor.route"}
        self.assertEqual(route_parents, {baseline["span_id"], rnd["span_id"]})
        self.assertTrue(parents)


if __name__ == "__main__":
    unittest.main()
