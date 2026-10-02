#!/usr/bin/env python3
"""Deterministic smoke eval for browser-extension-launch helper scripts."""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2] / "browser-extension-launch"


def run(*args):
    return subprocess.run(
        [sys.executable, *map(str, args)],
        capture_output=True,
        text=True,
    )


def check(name, condition, detail=""):
    print(f"  {'PASS' if condition else 'FAIL'} {name}")
    if not condition and detail:
        print(f"    {detail}")
    return bool(condition)


def main():
    checks = []
    scripts = ROOT / "scripts"

    for script in ("project.py", "acceptance_gate.py", "release_bundle.py"):
        result = run(scripts / script, "--help")
        checks.append(check(f"{script} exposes help", result.returncode == 0, result.stderr))

    with tempfile.TemporaryDirectory(prefix="browser-extension-launch-eval-") as temp:
        temp_root = Path(temp)
        project = temp_root / "project"
        project.mkdir()

        init = run(
            scripts / "project.py",
            "init",
            project,
            "--name",
            "Eval Extension",
            "--idea",
            "Save selected text locally",
            "--browser",
            "chrome",
            "--goal",
            "local",
            "--complexity",
            "simple",
            "--complexity-reason",
            "Single local workflow",
        )
        checks.append(check("project init succeeds", init.returncode == 0, init.stderr))
        checks.append(check("project state is created", (project / ".extension-launch").is_dir()))

        status = run(scripts / "project.py", "status", project)
        checks.append(check("project status succeeds", status.returncode == 0, status.stderr))

        build = temp_root / "extension"
        shutil.copytree(ROOT / "assets" / "starter" / "chrome-mv3", build)

        fingerprint = run(scripts / "acceptance_gate.py", "fingerprint", build)
        try:
            candidate = json.loads(fingerprint.stdout)
        except json.JSONDecodeError:
            candidate = {}
        checks.append(check("fingerprint succeeds", fingerprint.returncode == 0, fingerprint.stderr))
        checks.append(
            check(
                "fingerprint emits candidate sha256",
                len(candidate.get("fingerprint_sha256", "")) == 64,
            )
        )

        report = temp_root / "release-report.json"
        release = run(
            scripts / "release_bundle.py",
            "check",
            build,
            "--report",
            report,
        )
        checks.append(check("release bundle check succeeds", release.returncode == 0, release.stderr))
        checks.append(check("release report is written outside build", report.is_file()))

    if not all(checks):
        raise SystemExit(1)
    print(f"browser-extension-launch eval passed: {len(checks)} checks")


if __name__ == "__main__":
    main()
