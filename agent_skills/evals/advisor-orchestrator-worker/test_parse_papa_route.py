#!/usr/bin/env python3
"""Deterministic eval for parse_papa_route.sh — no network."""

import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "..", "advisor-orchestrator-worker", "scripts", "parse_papa_route.sh")

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
    r = run_on("ROUTE: orchestrator\nREASON: Plan is straightforward.\n")
    check("orchestrator route passes", r.returncode == 0 and "ROUTE: orchestrator" in r.stdout)

    r = run_on("ROUTE: advisor\nREASON: Contradiction needs judgment.\n")
    check("advisor route passes", r.returncode == 0 and "ROUTE: advisor" in r.stdout)

    r = run_on("ROUTE: maybe\nREASON: unclear\n")
    check("invalid route fails", r.returncode == 2)

    r = run_on("No routing here\n")
    check("missing lines fails", r.returncode == 2)

    if all(checks):
        print("\nall %d checks passed" % len(checks))
        return 0
    print("\n%d/%d failed" % (checks.count(False), len(checks)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
