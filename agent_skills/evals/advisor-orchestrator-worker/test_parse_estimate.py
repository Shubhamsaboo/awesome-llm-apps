#!/usr/bin/env python3
"""Deterministic eval for parse_estimate.sh — no network."""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "..", "advisor-orchestrator-worker", "scripts", "parse_estimate.sh")

VALID = {
    "estimated_input_tokens": 1000,
    "estimated_output_tokens": 500,
    "estimated_usd": 0.42,
    "breakdown": [{"tier": "workers", "calls": 2, "usd": 0.1}],
    "worth_it": True,
    "recommendation": "Proceed.",
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
    r = run_on(json.dumps(VALID))
    check("valid JSON passes", r.returncode == 0 and "worth_it" in r.stdout, r.stderr.strip())

    fenced = "```json\n" + json.dumps(VALID) + "\n```"
    r = run_on(fenced)
    check("fenced JSON passes", r.returncode == 0, r.stderr.strip())

    bad = dict(VALID)
    del bad["worth_it"]
    r = run_on(json.dumps(bad))
    check("missing worth_it fails", r.returncode == 2)

    r = run_on("not json at all")
    check("garbage fails", r.returncode == 2)

    if all(checks):
        print("\nall %d checks passed" % len(checks))
        return 0
    print("\n%d/%d failed" % (checks.count(False), len(checks)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
