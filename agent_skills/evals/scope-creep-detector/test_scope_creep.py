#!/usr/bin/env python3
"""
Executable eval for scope-creep-detector. Builds a temporary git repository,
creates a deliberately mixed diff, and checks the deterministic classifier.

    python3 agent_skills/evals/scope-creep-detector/test_scope_creep.py

The fixture contains an in-scope parser fix plus an unrelated CI edit, a new
dependency, and a public API rename. It uses only git and the Python stdlib.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile


SCRIPT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "scope-creep-detector",
    "scripts",
    "scope_creep.py",
)

checks = []


def check(name, ok, detail=""):
    checks.append(ok)
    suffix = ": %s" % detail if detail and not ok else ""
    print("  %s %s%s" % ("PASS" if ok else "FAIL", name, suffix))


def write(root, path, content):
    target = os.path.join(root, path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(content)


def build_repo(root):
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "scope-eval@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "scope eval"], cwd=root, check=True)

    write(
        root,
        "src/parser.py",
        "def parse_payload(payload):\n"
        "    return payload[\"value\"]\n",
    )
    write(
        root,
        "src/public_api.py",
        "def load_record(record):\n"
        "    return record\n"
        "\n"
        "def _normalize_record(record):\n"
        "    return record\n",
    )
    write(root, "requirements.txt", "click==8.1.7\n")
    write(
        root,
        "package.json",
        "{\n"
        "  \"dependencies\": {\n"
        "    \"chalk\": \"5.3.0\"\n"
        "  }\n"
        "}\n",
    )
    write(
        root,
        "pyproject.toml",
        "[project]\n"
        "dependencies = [\n"
        "  \"click==8.1.7\",\n"
        "]\n",
    )
    write(root, ".gitattributes", "*.bin diff=scope-eval-textconv\n")
    write(root, "assets/sample.bin", "before\x00data\n")
    write(root, "src/format_only.py", "answer=42\n")
    write(
        root,
        "src/bulk_change.py",
        "".join("old_%03d = %d\n" % (index, index) for index in range(45)),
    )
    write(
        root,
        ".github/workflows/ci.yml",
        "name: CI\n"
        "on: [push]\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n",
    )
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=root, check=True)

    write(
        root,
        "src/parser.py",
        "def parse_payload(payload):\n"
        "    if payload is None:\n"
        "        return None\n"
        "    return payload[\"value\"]\n",
    )
    write(
        root,
        "src/public_api.py",
        "def fetch_record(record):\n"
        "    return record\n"
        "\n"
        "def _coerce_record(record):\n"
        "    return record\n",
    )
    write(root, "requirements.txt", "click==8.1.7\nhttpx==0.27.0\n")
    write(
        root,
        "package.json",
        "{\n"
        "  \"dependencies\": {\n"
        "    \"chalk\": \"5.3.0\",\n"
        "    \"ora\": \"8.0.1\"\n"
        "  }\n"
        "}\n",
    )
    write(
        root,
        "pyproject.toml",
        "[project]\n"
        "dependencies = [\n"
        "  \"click==8.1.7\",\n"
        "  \"rich==13.7.1\",\n"
        "]\n",
    )
    write(root, "assets/sample.bin", "after\x00data\n")
    marker = os.path.join(root, "textconv-ran")
    helper = os.path.join(root, "textconv.py")
    write(
        root,
        "textconv.py",
        "import pathlib\n"
        "import sys\n"
        "pathlib.Path(sys.argv[1]).write_text('ran', encoding='utf-8')\n"
        "print(pathlib.Path(sys.argv[2]).read_bytes().hex())\n",
    )
    subprocess.run(
        [
            "git",
            "config",
            "diff.scope-eval-textconv.textconv",
            "%s %s %s" % (sys.executable, helper, marker),
        ],
        cwd=root,
        check=True,
    )
    write(root, "src/format_only.py", "answer = 42\n")
    write(
        root,
        "src/bulk_change.py",
        "".join("new_%03d = %d\n" % (index, index) for index in range(45)),
    )
    write(
        root,
        ".github/workflows/ci.yml",
        "name: CI\n"
        "on: [push, pull_request]\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n",
    )


def main():
    root = tempfile.mkdtemp(prefix="scope-creep-eval-")
    try:
        build_repo(root)
        marker = os.path.join(root, "textconv-ran")
        result = subprocess.run(
            [
                sys.executable,
                SCRIPT,
                "--repo",
                root,
                "--intent",
                "fix null dereference in parser",
                "--json",
            ],
            capture_output=True,
            text=True,
        )

        print("scope classification:")
        check("script exits successfully", result.returncode == 0, result.stderr.strip())
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            report = {}
            check("stdout is valid JSON", False, str(error))
        else:
            check("stdout is valid JSON", True)

        in_scope = {item["path"] for item in report.get("in_scope", [])}
        creep = {item["path"] for item in report.get("likely_creep", [])}
        deps = report.get("new_deps", [])
        renames = report.get("api_renames", [])
        config = {item["path"] for item in report.get("config_edits", [])}
        stats = report.get("stats", {})

        check("parser fix is in scope", "src/parser.py" in in_scope, sorted(in_scope))
        check("CI edit is likely creep", ".github/workflows/ci.yml" in creep, sorted(creep))
        check("CI edit is classified as config", ".github/workflows/ci.yml" in config, sorted(config))
        check(
            "new dependency is detected",
            any(item.get("name") == "httpx" and item.get("path") == "requirements.txt" for item in deps),
            deps,
        )
        check(
            "package.json dependency is detected",
            any(item.get("name") == "ora" and item.get("path") == "package.json" for item in deps),
            deps,
        )
        check(
            "pyproject dependency is detected",
            any(item.get("name") == "rich" and item.get("path") == "pyproject.toml" for item in deps),
            deps,
        )
        check("git textconv command is not executed", not os.path.exists(marker), marker)
        check("dependency file is likely creep", "requirements.txt" in creep, sorted(creep))
        check(
            "public API rename is detected",
            any(
                item.get("path") == "src/public_api.py"
                and item.get("from") == "load_record"
                and item.get("to") == "fetch_record"
                for item in renames
            ),
            renames,
        )
        check(
            "private helper rename is ignored",
            not any(item.get("from", "").startswith("_") for item in renames),
            renames,
        )
        check(
            "formatting-only file is detected",
            "src/format_only.py" in stats.get("formatting_only_files", []),
            stats.get("formatting_only_files", []),
        )
        check(
            "oversized hunk is detected",
            any(item.get("path") == "src/bulk_change.py" for item in stats.get("oversized_hunks", [])),
            stats.get("oversized_hunks", []),
        )

        plain_diff = os.path.join(root, "plain.diff")
        write(
            root,
            "plain.diff",
            "--- a/src/parser.py\n"
            "+++ b/src/parser.py\n"
            "@@ -1 +1,2 @@\n"
            " def parse_payload(payload):\n"
            "+    return payload\n",
        )
        plain_result = subprocess.run(
            [
                sys.executable,
                SCRIPT,
                "--diff",
                plain_diff,
                "--intent",
                "parser change",
                "--json",
            ],
            capture_output=True,
            text=True,
        )
        try:
            plain_report = json.loads(plain_result.stdout)
        except json.JSONDecodeError:
            plain_report = {}
        check(
            "plain unified diff without git headers is parsed",
            plain_result.returncode == 0
            and plain_report.get("stats", {}).get("files_touched") == 1
            and plain_report.get("in_scope", [{}])[0].get("path") == "src/parser.py",
            plain_result.stderr.strip() or plain_result.stdout.strip(),
        )

        print()
        if all(checks):
            print("PASS: %d/%d checks" % (len(checks), len(checks)))
            return 0
        print("FAIL: %d/%d checks passed" % (sum(checks), len(checks)))
        return 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
