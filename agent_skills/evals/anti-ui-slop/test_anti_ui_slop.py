#!/usr/bin/env python3
"""Executable eval for the local anti-ui-slop source checker."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "anti-ui-slop" / "scripts" / "check_ui_slop.py"
checks = []


def check(name, ok, detail=""):
    checks.append(ok)
    suffix = " — %s" % detail if detail and not ok else ""
    print("  %s %s%s" % ("PASS" if ok else "FAIL", name, suffix))


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def main():
    with tempfile.TemporaryDirectory(prefix="anti-ui-slop-eval-") as root:
        root = Path(root)
        bad = root / "Bad.tsx"
        bad.write_text(
            '<h1>Welcome to our platform</h1>\n'
            '<button>Click here</button>\n'
            '<img src="hero.png">\n'
            '<form><input /></form>\n',
            encoding="utf-8",
        )
        css = root / "styles.css"
        css.write_text(".a { color: #123456; }\n.b { color: #123456; }\n", encoding="utf-8")

        result = run("--path", str(root), "--format", "json", "--fail-on", "warning")
        payload = json.loads(result.stdout)
        rules = {item["rule"] for item in payload["findings"]}
        check("bad fixture fails warning threshold", result.returncode == 1)
        check(
            "all deterministic rules fire",
            {"generic-copy", "inert-control", "image-alt", "missing-state", "token-drift"}.issubset(rules),
            sorted(rules),
        )

        good = root / "Good.tsx"
        good.write_text(
            '<button onClick={save}>Save</button>\n'
            '<img src="hero.png" alt="Product preview">\n'
            '<p>Loading…</p>\n',
            encoding="utf-8",
        )
        clean = run("--path", str(good), "--format", "json")
        check("good fixture passes", clean.returncode == 0)
        check("good fixture has no findings", json.loads(clean.stdout)["findings"] == [])

    print()
    passed = sum(checks)
    print("PASS — %d/%d checks" % (passed, len(checks)) if passed == len(checks) else "FAIL — %d/%d checks passed" % (passed, len(checks)))
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
