#!/usr/bin/env python3
"""Deterministic, offline eval for the dependency-doctor skill.

The eval writes isolated manifests in a temporary directory, runs the skill's
CLI, and checks its classifications and JSON contract. It uses only the Python
standard library and never enables the optional online PyPI check.
"""

# SPDX-License-Identifier: Apache-2.0

import json
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "dependency-doctor"
    / "scripts"
    / "dep_doctor.py"
)
CHECKS = []


def check(name, condition, detail=""):
    """Record one assertion while keeping the full eval running."""
    CHECKS.append(bool(condition))
    suffix = "" if condition or not detail else ": " + detail
    print("  %s %s%s" % ("PASS" if condition else "FAIL", name, suffix))


def run_json(manifest):
    """Run the doctor offline and return its parsed JSON report."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(manifest), "--json"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    check(
        "%s exits successfully" % manifest.name,
        result.returncode == 0,
        result.stderr.strip() or result.stdout.strip(),
    )
    if result.returncode != 0:
        return {"file": str(manifest), "findings": [], "summary": {}}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        check("%s emits valid JSON" % manifest.name, False, str(error))
        return {"file": str(manifest), "findings": [], "summary": {}}


def finding(report, kind, package):
    """Return the first matching finding, if present."""
    return next(
        (
            item
            for item in report.get("findings", [])
            if item.get("kind") == kind and item.get("package") == package
        ),
        None,
    )


def check_finding(report, kind, package, severity, fix_fragment):
    """Assert classification, severity, location, explanation, and fix."""
    item = finding(report, kind, package)
    check("%s classifies %s" % (kind, package), item is not None)
    if item is None:
        return
    check("%s severity is %s" % (kind, severity), item["severity"] == severity)
    check("%s has a source line" % kind, isinstance(item["line"], int) and item["line"] > 0)
    check("%s explains why" % kind, bool(item["why"].strip()))
    check("%s suggests a fix" % kind, fix_fragment.lower() in item["fix"].lower())


def test_requirements(root):
    manifest = root / "requirements.txt"
    manifest.write_text(
        "pathlib==1.0.1\n"
        "enum34==1.1.10\n"
        "requests\n"
        "requests\n"
        "urllib3==1.26.18\n"
        "urllib3==2.2.2\n"
        "-r shared-requirements.txt\n"
        "# a comment is not a dependency\n",
        encoding="utf-8",
    )
    report = run_json(manifest)

    check("report names the input file", report.get("file") == str(manifest))
    check_finding(report, "stdlib-shadowing", "pathlib", "high", "remove")
    check_finding(report, "abandoned-backport", "enum34", "high", "remove")
    check_finding(report, "unpinned", "requests", "medium", "pin")
    check_finding(report, "duplicate-constraint", "requests", "medium", "one")
    check_finding(report, "conflicting-constraints", "urllib3", "high", "choose")

    required = {"severity", "kind", "package", "line", "why", "fix"}
    check(
        "every finding follows the JSON contract",
        all(set(item) == required for item in report.get("findings", [])),
    )
    summary = report.get("summary", {})
    check("summary total matches findings", summary.get("total") == len(report.get("findings", [])))
    check("offline mode is recorded", summary.get("online") is False)
    check(
        "requirements directives are ignored",
        all(item.get("package") != "shared-requirements.txt" for item in report.get("findings", [])),
    )


def test_pyproject(root):
    manifest = root / "pyproject.toml"
    manifest.write_text(
        "[project]\n"
        "dependencies = [\n"
        "  \"typing==3.7.4.3\",\n"
        "  \"httpx\",\n"
        "]\n"
        "[tool.poetry.dependencies]\n"
        "python = \"^3.11\"\n"
        "rich = \"^13.0\"\n"
        "dataclasses = \"*\"\n",
        encoding="utf-8",
    )
    report = run_json(manifest)
    check_finding(report, "abandoned-backport", "typing", "high", "remove")
    check_finding(report, "unpinned", "httpx", "medium", "pin")
    check("Poetry range is treated as a constraint", finding(report, "unpinned", "rich") is None)
    check_finding(report, "unpinned", "dataclasses", "medium", "do not add")


def test_version_marker(root):
    manifest = root / "guarded-requirements.txt"
    manifest.write_text(
        "dataclasses; python_version < \"3.7\"\n",
        encoding="utf-8",
    )
    report = run_json(manifest)
    check(
        "inactive Python-version backport marker is respected",
        not report.get("findings"),
    )


def test_package_json(root):
    manifest = root / "package.json"
    manifest.write_text(
        json.dumps({"dependencies": {"left-pad": "*", "chalk": "5.3.0"}}, indent=2) + "\n",
        encoding="utf-8",
    )
    report = run_json(manifest)
    check_finding(report, "unpinned", "left-pad", "medium", "pin")
    check(
        "exact npm version is not called unpinned",
        finding(report, "unpinned", "chalk") is None,
    )


def main():
    print("dependency-doctor eval:")
    with tempfile.TemporaryDirectory(prefix="dependency-doctor-eval-") as temp_dir:
        root = Path(temp_dir)
        test_requirements(root)
        test_pyproject(root)
        test_version_marker(root)
        test_package_json(root)

    print()
    passed = sum(CHECKS)
    if passed == len(CHECKS):
        print("PASS: %d/%d checks" % (passed, len(CHECKS)))
        return 0
    print("FAIL: %d/%d checks passed" % (passed, len(CHECKS)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
