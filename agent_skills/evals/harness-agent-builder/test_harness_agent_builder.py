#!/usr/bin/env python3
"""Deterministic eval for the harness-agent-builder scaffolder.

Runs scripts/scaffold_agent.py into temp dirs and asserts the generated
agent follows the harness consumer contract. Offline, stdlib only.
"""

import json
import os
import subprocess
import sys
import tempfile

SKILL_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "harness-agent-builder"))
SCRIPT = os.path.join(SKILL_DIR, "scripts", "scaffold_agent.py")

PASS = 0
FAIL = 0


def check(label, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  ok: %s" % label)
    else:
        FAIL += 1
        print("  FAIL: %s %s" % (label, detail))


def scaffold(tmp, *extra):
    out = os.path.join(tmp, "out")
    argv = [sys.executable, SCRIPT, "--name", "radar",
            "--prompt", "You are a dependency analyst.", "--dir", out] + list(extra)
    proc = subprocess.run(argv, capture_output=True, text=True)
    return proc, out


def main():
    print("== cron + json + allow scaffold")
    with tempfile.TemporaryDirectory() as tmp:
        proc, out = scaffold(tmp, "--trigger", "cron", "--cron", "0 0 9 * * *",
                             "--allow", "web::fetch", "--output", "json")
        check("exit 0", proc.returncode == 0, proc.stderr)
        agent = open(os.path.join(out, "agent.js")).read()
        pkg = json.load(open(os.path.join(out, "package.json")))

        check("registers <name>::run on the bus", "'radar::run'" in agent)
        check("starts turns via harness::send", "'harness::send'" in agent)
        check("binds harness::turn-completed instead of polling",
              "'harness::turn-completed'" in agent)
        check("correlates results by session_id", "waiters.get(event?.session_id)" in agent)
        check("binds the cron trigger with the given expression",
              "'cron'" in agent and "0 0 9 * * *" in agent)
        check("fail-closed allow list carries web::fetch",
              '"web::fetch"' in agent and "allow:" in agent)
        check("json output contract present", "output: { type: 'json'" in agent)
        check("resolves model from router::models::list",
              "'router::models::list'" in agent)
        check("no hardcoded model id",
              "claude-" not in agent and "gpt-" not in agent and "gemini" not in agent)
        check("no credentials in generated code",
              "api_key" not in agent.lower() and "apikey" not in agent.lower())
        check("timeout path stops the turn", "'harness::stop'" in agent)
        check("package depends only on iii-sdk",
              list(pkg.get("dependencies", {}).keys()) == ["iii-sdk"])

    print("== http trigger scaffold")
    with tempfile.TemporaryDirectory() as tmp:
        proc, out = scaffold(tmp, "--trigger", "http")
        check("exit 0", proc.returncode == 0, proc.stderr)
        agent = open(os.path.join(out, "agent.js")).read()
        check("http route bound via engine::register_trigger",
              "'engine::register_trigger'" in agent and "api_path" in agent)
        check("degrades gracefully without the http worker",
              "http worker not installed" in agent)
        check("pure chat default has no allow list", "allow:" not in agent)

    print("== guardrails")
    with tempfile.TemporaryDirectory() as tmp:
        proc, out = scaffold(tmp)
        check("plain function scaffold exits 0", proc.returncode == 0, proc.stderr)
        proc2, _ = scaffold(tmp)
        check("refuses to overwrite existing output", proc2.returncode != 0)
    with tempfile.TemporaryDirectory() as tmp:
        proc, _ = scaffold(tmp, "--trigger", "cron", "--cron", "0 9 * * *")
        check("rejects 5-field cron (needs 6 fields)", proc.returncode != 0)
        bad = subprocess.run([sys.executable, SCRIPT, "--name", "Bad-Name",
                              "--prompt", "x", "--dir", os.path.join(tmp, "o2")],
                             capture_output=True, text=True)
        check("rejects invalid --name", bad.returncode != 0)
        badfn = subprocess.run([sys.executable, SCRIPT, "--name", "ok",
                                "--prompt", "x", "--allow", "not a function",
                                "--dir", os.path.join(tmp, "o3")],
                               capture_output=True, text=True)
        check("rejects malformed --allow function id", badfn.returncode != 0)

    print("== determinism")
    with tempfile.TemporaryDirectory() as tmp:
        _, out1 = scaffold(tmp, "--trigger", "cron")
        a1 = open(os.path.join(out1, "agent.js")).read()
    with tempfile.TemporaryDirectory() as tmp:
        _, out2 = scaffold(tmp, "--trigger", "cron")
        a2 = open(os.path.join(out2, "agent.js")).read()
    check("identical inputs produce identical output", a1 == a2)

    print("%d passed, %d failed" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
