#!/usr/bin/env python3
"""Deterministic eval for the commit-archaeologist skill.

Builds a temporary git repository with a known file history, runs the skill's
offline script, and checks the resulting dig report.

    python3 agent_skills/evals/commit-archaeologist/test_archaeologist.py

Python stdlib plus git only. The fixture never touches the source checkout.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile


SCRIPT = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "..", "..", "commit-archaeologist", "scripts", "archaeologist.py",
))
EMAIL = "archaeologist-eval@example.com"
checks = []


def check(name, condition, detail=""):
    checks.append(bool(condition))
    status = "PASS" if condition else "FAIL"
    suffix = " - %s" % detail if detail and not condition else ""
    print("  %s %s%s" % (status, name, suffix))


def git(repo, *args, env=None):
    result = subprocess.run(
        ["git", *args], cwd=repo, env=env, capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def write(repo, path, content):
    target = os.path.join(repo, path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(content)


def commit(repo, date, message, files):
    for path, content in files.items():
        write(repo, path, content)
    git(repo, "add", "-A")
    env = dict(
        os.environ,
        GIT_AUTHOR_DATE=date,
        GIT_COMMITTER_DATE=date,
    )
    git(repo, "commit", "-m", message, env=env)
    return git(repo, "rev-parse", "HEAD")


def build_repo(root):
    repo = os.path.join(root, "fixture")
    os.makedirs(repo)
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Ada Archaeologist")
    git(repo, "config", "user.email", EMAIL)

    introduced = commit(
        repo,
        "2026-01-01T10:00:00+0000",
        "feat: introduce calculator #12",
        {
            "src/calculator.py": (
                "def add(values):\n"
                "    return sum(values)\n"
            ),
            "docs/decision.md": "Calculator experiment notes.\n",
        },
    )
    refactored = commit(
        repo,
        "2026-01-02T10:00:00+0000",
        "refactor: name the accumulator",
        {
            "src/calculator.py": (
                "def add(values):\n"
                "    total = 0\n"
                "    for value in values:\n"
                "        total += value\n"
                "    return total\n"
            ),
            "src/helpers.py": (
                "def normalize_zero():\n"
                "    return 0\n"
            ),
        },
    )
    workaround = commit(
        repo,
        "2026-01-03T10:00:00+0000",
        "fix: temporary workaround for empty totals #34",
        {
            "src/calculator.py": (
                "from .helpers import normalize_zero\n\n"
                "def add(values):\n"
                "    total = 0\n"
                "    for value in values:\n"
                "        total += value\n"
                "    return total if values else normalize_zero()\n"
            ),
            "src/helpers.py": (
                "def normalize_zero():\n"
                "    # Keep the legacy integer return type.\n"
                "    return 0\n"
            ),
        },
    )
    return repo, [introduced, refactored, workaround]


def run(repo, *args, file_path="src/calculator.py"):
    return subprocess.run(
        [sys.executable, SCRIPT, repo, file_path, *args],
        capture_output=True,
        text=True,
    )


def main():
    root = tempfile.mkdtemp(prefix="commit-archaeologist-eval-")
    try:
        repo, expected_hashes = build_repo(root)

        print("line-range report:")
        result = run(repo, "--lines", "1-7", "--json")
        check("script exits cleanly", result.returncode == 0, result.stderr)
        if result.returncode != 0:
            return 1
        report = json.loads(result.stdout)

        check(
            "region identifies the requested lines",
            report["region"]["file"] == "src/calculator.py"
            and report["region"]["lines"] == {"start": 1, "end": 7},
            str(report.get("region")),
        )
        check(
            "introducing commit is the first commit",
            report["introduced_by"]["hash"] == expected_hashes[0],
            report["introduced_by"]["hash"],
        )
        timeline_hashes = [entry["hash"] for entry in report["timeline"]]
        check(
            "timeline is oldest to newest",
            timeline_hashes == expected_hashes,
            str(timeline_hashes),
        )
        check(
            "commit categories follow message intent",
            [entry["category"] for entry in report["timeline"]]
            == ["feat", "refactor", "fix"],
        )
        co_changed = {entry["file"]: entry for entry in report["co_changed"]}
        check(
            "helper is detected as a repeated co-change",
            co_changed.get("src/helpers.py", {}).get("count") == 2,
            str(report["co_changed"]),
        )
        check(
            "one-off neighboring files stay below the threshold",
            "docs/decision.md" not in co_changed,
            str(report["co_changed"]),
        )
        single_commit = run(repo, "--json", file_path="docs/decision.md")
        single_commit_report = (
            json.loads(single_commit.stdout) if single_commit.returncode == 0 else {}
        )
        check(
            "single-commit history has no repeated co-changes",
            single_commit.returncode == 0
            and single_commit_report.get("co_changed") == []
            and single_commit_report.get("region", {}).get("co_change_threshold") == 2,
            single_commit.stderr or str(single_commit_report),
        )
        signal_types = {entry["type"] for entry in report["intent_signals"]}
        check("workaround signal is present", "workaround" in signal_types)
        check("temporary signal is present", "temporary" in signal_types)
        check("issue reference signal is present", "issue_reference" in signal_types)
        check(
            "blame authorship is summarized",
            any(
                author["email"] == EMAIL and author["current_lines"] == 7
                for author in report["authors"]
            ),
            str(report["authors"]),
        )

        repeat = run(repo, "--lines", "1-7", "--json")
        check("JSON output is deterministic", repeat.stdout == result.stdout)

        print("file-wide rename and error behavior:")
        git(repo, "mv", "src/calculator.py", "src/arithmetic.py")
        git(repo, "commit", "-m", "refactor: rename calculator module")
        renamed = git(repo, "rev-parse", "HEAD")
        file_result = run(repo, "--json", file_path="src/arithmetic.py")
        file_report = json.loads(file_result.stdout) if file_result.returncode == 0 else {}
        check("file-wide mode exits cleanly", file_result.returncode == 0, file_result.stderr)
        check(
            "file-wide mode uses follow history",
            file_report.get("region", {}).get("mode") == "file"
            and [entry["hash"] for entry in file_report.get("timeline", [])]
            == expected_hashes + [renamed],
        )
        check(
            "a target's old name is not reported as a co-change",
            all(
                entry["file"] != "src/calculator.py"
                for entry in file_report.get("co_changed", [])
            ),
            str(file_report.get("co_changed")),
        )

        invalid = run(
            repo, "--lines", "7-1", "--json", file_path="src/arithmetic.py",
        )
        check("invalid line range fails", invalid.returncode != 0)
        check(
            "invalid line range explains the problem without a traceback",
            "line range" in invalid.stderr.lower() and "traceback" not in invalid.stderr.lower(),
            invalid.stderr,
        )

        print()
        if all(checks):
            print("PASS - %d/%d checks" % (len(checks), len(checks)))
            return 0
        print("FAIL - %d/%d checks passed" % (sum(checks), len(checks)))
        return 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
