#!/usr/bin/env python3
"""
Executable eval for cost_tracker.sh — deterministic pricing math and ceiling.

    python3 evals/advisor-orchestrator-worker/test_cost_tracker.py

No network. Uses a temp pricing file and tracker state.
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "..", "advisor-orchestrator-worker", "scripts", "cost_tracker.sh")
PRICING_SAMPLE = {
    "models": {
        "gemini-3.5-flash": {"input_per_million": 1.0, "output_per_million": 2.0},
        "claude-fable-5": {"input_per_million": 10.0, "output_per_million": 20.0},
    },
    "fallback_model": "gemini-3.5-flash",
}

checks = []


def check(name, ok, detail=""):
    checks.append(ok)
    tag = "PASS" if ok else "FAIL"
    suffix = (" — " + detail) if detail and not ok else ""
    print("  %s %s%s" % (tag, name, suffix))


def run_tracker(env, *args):
    out = subprocess.run(
        ["bash", SCRIPT, *args],
        capture_output=True,
        text=True,
        env=env,
    )
    return out


def main():
    if not os.path.isfile(SCRIPT):
        print("missing script:", SCRIPT)
        return 1

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as pf:
        json.dump(PRICING_SAMPLE, pf)
        pricing_path = pf.name

    tracker_path = tempfile.mktemp(suffix=".json")
    env = os.environ.copy()
    env["COST_PRICING"] = pricing_path
    env["COST_TRACKER"] = tracker_path

    # init
    r = run_tracker(env, "init", "--approved-usd", "1.00", "--estimated-usd", "0.80")
    check("init exits 0", r.returncode == 0, r.stderr.strip())
    check("init prints tracker path", tracker_path in (r.stdout + r.stderr) or os.path.isfile(tracker_path))

    # record under ceiling: 100k in + 50k out @ flash = 0.10 + 0.10 = 0.20 USD
    r = run_tracker(
        env,
        "record",
        "--tier",
        "worker",
        "--input",
        "100000",
        "--output",
        "50000",
        "--model",
        "gemini-3.5-flash",
    )
    check("record exits 0", r.returncode == 0, r.stderr.strip())

    state = json.load(open(tracker_path))
    check("tokens accumulated", state["total_input_tokens"] == 100_000)
    check("usd accumulated", float(state["total_usd"]) == 0.2)

    r = run_tracker(env, "status")
    check("status exits 0", r.returncode == 0)
    check("status mentions approved", "approved" in r.stdout)

    r = run_tracker(env, "check")
    check("check passes under ceiling", r.returncode == 0, r.stderr.strip())

    # push over ceiling: 50k in + 50k out @ fable = 0.50 + 1.00 = 1.50 → total 1.70
    r = run_tracker(
        env,
        "record",
        "--tier",
        "advisor",
        "--input",
        "50000",
        "--output",
        "50000",
        "--model",
        "claude-fable-5",
    )
    check("record over ceiling still exits 0", r.returncode == 0)

    r = run_tracker(env, "check")
    check("check fails over ceiling", r.returncode == 2)

    os.unlink(pricing_path)
    os.unlink(tracker_path)

    if all(checks):
        print("\nall %d checks passed" % len(checks))
        return 0
    print("\n%d/%d checks failed" % (checks.count(False), len(checks)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
