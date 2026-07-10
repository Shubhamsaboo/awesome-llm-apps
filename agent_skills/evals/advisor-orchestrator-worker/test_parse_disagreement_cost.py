#!/usr/bin/env python3
"""Deterministic eval for parse_disagreement_cost.sh — no network."""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(
    HERE, "..", "..", "advisor-orchestrator-worker", "scripts", "parse_disagreement_cost.sh"
)

VALID = {
    "orchestrator_path": {
        "estimated_input_tokens": 500,
        "estimated_output_tokens": 200,
        "estimated_usd": 0.12,
        "summary": "Ship 2-app comparison as planned.",
    },
    "advisor_path": {
        "estimated_input_tokens": 4000,
        "estimated_output_tokens": 2000,
        "estimated_usd": 0.85,
        "summary": "Expand to 8-app matrix per advisor.",
    },
    "delta_usd": 0.73,
    "cost_note": "Advisor path costs $0.73 more for broader scope.",
}

checks = []


def check(name, ok, detail=""):
    checks.append(ok)
    print("  %s %s%s" % ("PASS" if ok else "FAIL", name, (" — " + detail) if detail and not ok else ""))


def run_on(content):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        path = f.name
    r = subprocess.run(["bash", SCRIPT, path], capture_output=True, text=True)
    os.unlink(path)
    return r


def main():
    if not os.path.isfile(SCRIPT):
        print("missing script:", SCRIPT)
        return 1

    r = run_on(json.dumps(VALID))
    check("valid JSON passes", r.returncode == 0 and "orchestrator_path" in r.stdout, r.stderr.strip())

    bad = dict(VALID)
    del bad["cost_note"]
    r = run_on(json.dumps(bad))
    check("missing cost_note fails", r.returncode == 2)

    r = run_on("not json")
    check("garbage fails", r.returncode == 2)

    if all(checks):
        print("\nall %d checks passed" % len(checks))
        return 0
    print("\n%d/%d failed" % (checks.count(False), len(checks)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
