#!/usr/bin/env python3
"""
Classify scope signals in a unified diff.

Usage:
    python3 scope_creep.py --repo . --intent "fix parser crash" --json
    python3 scope_creep.py --repo . --staged --json
    python3 scope_creep.py --repo . --base main --json
    python3 scope_creep.py --diff change.diff --intent "fix parser crash" --json

Python 3.11 stdlib only. Runs locally and never changes the target repository.
"""

import argparse
import collections
import json
import os
import re
import shlex
import subprocess
import sys


DEFAULT_HUNK_THRESHOLD = 80
STOP_WORDS = {
    "add", "branch", "bug", "change", "changes", "chore", "develop",
    "development", "feat", "feature", "fix", "fixed", "main", "master",
    "the", "this", "to", "update", "with",
}
CONFIG_EXTENSIONS = {".toml", ".yaml", ".yml"}
BUILD_FILES = {
    "cmakelists.txt", "docker-compose.yaml", "docker-compose.yml",
    "dockerfile", "makefile", "meson.build", "procfile",
}
SYMBOL_RE = re.compile(
    r"^\s*(?:(?:async\s+)?def\s+([A-Za-z_]\w*)|class\s+([A-Za-z_]\w*))"
)
HUNK_RE = re.compile(
    r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$"
)
REQUIREMENTS_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9_.-]*)")
JSON_PROPERTY_RE = re.compile(r'^\s*"([A-Za-z0-9@/_.-]+)"\s*:\s*(.+?)[,]?\s*$')
PYPROJECT_STRING_RE = re.compile(r'^\s*["\']([A-Za-z0-9][A-Za-z0-9_.-]*)[^"\']*["\']\s*,?\s*$')
PYPROJECT_ASSIGN_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9_.-]*)\s*=\s*(.+)$")


def clean_path(value):
    """Normalize a git header path without touching the filesystem."""
    value = value.strip()
    if "\t" in value:
        value = value.split("\t", 1)[0].rstrip()
    if value.startswith('"') and value.endswith('"'):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            value = value[1:-1]
    if value in {"/dev/null", "dev/null"}:
        return None
    if value.startswith(("a/", "b/")):
        value = value[2:]
    return value


def new_file(old_path=None, new_path=None):
    return {
        "old_path": old_path,
        "new_path": new_path,
        "path": new_path or old_path or "unknown",
        "hunks": [],
    }


def parse_diff(text):
    """Parse the file and hunk structure needed by the classifiers."""
    files = []
    current = None
    hunk = None
    old_remaining = new_remaining = 0

    for raw in text.splitlines():
        if raw.startswith("diff --git "):
            try:
                parts = shlex.split(raw)
            except ValueError:
                parts = raw.split()
            old_path = clean_path(parts[2]) if len(parts) > 2 else None
            new_path = clean_path(parts[3]) if len(parts) > 3 else None
            current = new_file(old_path, new_path)
            files.append(current)
            hunk = None
            continue

        if current is None:
            if not raw.startswith("--- "):
                continue
            current = new_file()
            files.append(current)

        match = HUNK_RE.match(raw)
        if match:
            old_remaining = int(match.group(2) or "1")
            new_remaining = int(match.group(4) or "1")
            hunk = {"header": raw, "lines": []}
            current["hunks"].append(hunk)
            continue

        if hunk is not None:
            if not raw:
                continue
            marker = raw[0]
            if marker not in {" ", "+", "-"}:
                continue
            entry = {
                "marker": marker,
                "text": raw[1:],
                "index": len(hunk["lines"]),
            }
            hunk["lines"].append(entry)
            if marker != "+":
                old_remaining -= 1
            if marker != "-":
                new_remaining -= 1
            if old_remaining <= 0 and new_remaining <= 0:
                hunk = None
            continue

        if raw.startswith("--- ") and current["hunks"]:
            current = new_file()
            files.append(current)
        if raw.startswith("rename from "):
            current["old_path"] = clean_path(raw[len("rename from "):])
            current["path"] = current["new_path"] or current["old_path"]
            continue
        if raw.startswith("rename to "):
            current["new_path"] = clean_path(raw[len("rename to "):])
            current["path"] = current["new_path"] or current["old_path"]
            continue
        if raw.startswith("--- "):
            current["old_path"] = clean_path(raw[4:])
            current["path"] = current["new_path"] or current["old_path"] or "unknown"
            continue
        if raw.startswith("+++ "):
            current["new_path"] = clean_path(raw[4:])
            current["path"] = current["new_path"] or current["old_path"] or "unknown"
            continue

    return files


def changed_lines(file_change, marker):
    return [
        entry["text"]
        for hunk in file_change["hunks"]
        for entry in hunk["lines"]
        if entry["marker"] == marker
    ]


def tokenize(value):
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    value = re.sub(r"[^A-Za-z0-9]+", " ", value).lower()
    return {
        token for token in value.split()
        if len(token) >= 3 and token not in STOP_WORDS
    }


def subsystem(path):
    parts = path.split("/")
    return parts[0] if len(parts) > 1 else "(root)"


def config_kind(path):
    normalized = path.lower()
    name = os.path.basename(normalized)
    extension = os.path.splitext(name)[1]
    if normalized.startswith(".github/"):
        return "ci"
    if name in BUILD_FILES or name.startswith("dockerfile."):
        return "build"
    if extension in CONFIG_EXTENSIONS:
        return "config"
    return None


def requirement_dependency(line):
    stripped = line.strip()
    if not stripped or stripped.startswith(("#", "-", ".")):
        return None
    match = REQUIREMENTS_RE.match(stripped)
    if not match:
        return None
    return match.group(1).lower().replace("_", "-"), stripped


def package_json_dependencies(file_change, marker):
    dependencies = []
    for hunk in file_change["hunks"]:
        in_dependencies = False
        for entry in hunk["lines"]:
            line = entry["text"]
            top_key = re.match(r'^\s{0,2}"([^"]+)"\s*:', line)
            if top_key:
                in_dependencies = top_key.group(1) in {
                    "dependencies", "devDependencies", "optionalDependencies",
                    "peerDependencies",
                }
                continue
            if entry["marker"] != marker or not in_dependencies:
                continue
            match = JSON_PROPERTY_RE.match(line)
            if match:
                dependencies.append((match.group(1).lower(), line.strip()))
    return dependencies


def pyproject_dependencies(file_change, marker):
    dependencies = []
    section = None
    in_project_list = False
    for hunk in file_change["hunks"]:
        for entry in hunk["lines"]:
            line = entry["text"]
            section_match = re.match(r"^\s*\[([^]]+)\]\s*$", line)
            if section_match:
                section = section_match.group(1).lower()
                in_project_list = False
                continue
            if section == "project" and re.match(r"^\s*dependencies\s*=\s*\[", line):
                in_project_list = True
                continue
            if in_project_list and "]" in line:
                in_project_list = False
            if entry["marker"] != marker:
                continue
            if in_project_list:
                match = PYPROJECT_STRING_RE.match(line)
                if match:
                    dependencies.append((match.group(1).lower().replace("_", "-"), line.strip()))
            elif section in {"tool.poetry.dependencies", "tool.poetry.group.dev.dependencies"}:
                match = PYPROJECT_ASSIGN_RE.match(line)
                if match and match.group(1).lower() != "python":
                    dependencies.append((match.group(1).lower().replace("_", "-"), line.strip()))
    return dependencies


def dependency_lines(file_change, marker):
    path = file_change["path"].lower()
    name = os.path.basename(path)
    if name.startswith("requirements") and name.endswith(".txt"):
        found = []
        for line in changed_lines(file_change, marker):
            parsed = requirement_dependency(line)
            if parsed:
                found.append(parsed)
        return found
    if name == "package.json":
        return package_json_dependencies(file_change, marker)
    if name == "pyproject.toml":
        return pyproject_dependencies(file_change, marker)
    return []


def find_new_dependencies(files):
    found = []
    for file_change in files:
        removed = {name for name, _line in dependency_lines(file_change, "-")}
        for name, line in dependency_lines(file_change, "+"):
            if name not in removed:
                found.append({"path": file_change["path"], "name": name, "line": line})
    unique = {(item["path"], item["name"]): item for item in found}
    return [unique[key] for key in sorted(unique)]


def declaration(entry):
    match = SYMBOL_RE.match(entry["text"])
    if not match:
        return None
    name = match.group(1) or match.group(2)
    if name.startswith("_"):
        return None
    kind = "function" if match.group(1) else "class"
    return {"kind": kind, "name": name, "entry": entry}


def find_api_renames(files):
    renames = []
    for file_change in files:
        for hunk in file_change["hunks"]:
            removed = [declaration(e) for e in hunk["lines"] if e["marker"] == "-"]
            added = [declaration(e) for e in hunk["lines"] if e["marker"] == "+"]
            removed = [item for item in removed if item]
            added = [item for item in added if item]
            used = set()
            for old in removed:
                candidates = [
                    (abs(old["entry"]["index"] - new["entry"]["index"]), index, new)
                    for index, new in enumerate(added)
                    if index not in used
                    and new["kind"] == old["kind"]
                    and new["name"] != old["name"]
                ]
                if not candidates:
                    continue
                distance, index, new = min(candidates)
                if distance > 12:
                    continue
                used.add(index)
                renames.append({
                    "path": file_change["path"],
                    "kind": old["kind"],
                    "from": old["name"],
                    "to": new["name"],
                    "hunk": hunk["header"],
                })
    return sorted(renames, key=lambda item: (item["path"], item["from"], item["to"]))


def lines_are_formatting_only(removed, added):
    if not removed or len(removed) != len(added):
        return False
    normalize = lambda line: re.sub(r"\s+", "", line)
    return [normalize(line) for line in removed] == [normalize(line) for line in added]


def classify(files, intent, hunk_threshold):
    intent_words = tokenize(intent)
    new_deps = find_new_dependencies(files)
    api_renames = find_api_renames(files)
    dep_paths = {item["path"] for item in new_deps}
    rename_paths = {item["path"] for item in api_renames}

    config_edits = []
    oversized = []
    formatting_only = []
    subsystems = collections.Counter()
    additions = deletions = 0
    file_metrics = {}

    for file_change in files:
        path = file_change["path"]
        subsystems[subsystem(path)] += 1
        added_lines = changed_lines(file_change, "+")
        removed_lines = changed_lines(file_change, "-")
        file_additions = len(added_lines)
        file_deletions = len(removed_lines)
        file_metrics[id(file_change)] = (file_additions, file_deletions)
        additions += file_additions
        deletions += file_deletions
        kind = config_kind(path)
        if kind:
            config_edits.append({
                "path": path,
                "kind": kind,
                "churn": file_additions + file_deletions,
            })
        if lines_are_formatting_only(removed_lines, added_lines):
            formatting_only.append(path)
        for hunk in file_change["hunks"]:
            churn = sum(1 for entry in hunk["lines"] if entry["marker"] in {"+", "-"})
            if churn > hunk_threshold:
                oversized.append({"path": path, "hunk": hunk["header"], "churn": churn})

    config_paths = {item["path"] for item in config_edits}
    oversized_paths = {item["path"] for item in oversized}
    formatting_paths = set(formatting_only)
    in_scope = []
    likely_creep = []

    for file_change in sorted(files, key=lambda item: item["path"]):
        path = file_change["path"]
        overlap = sorted(intent_words & tokenize(path))
        score = round(len(overlap) / max(1, len(intent_words)), 3)
        signals = []
        if path in dep_paths:
            signals.append("new_dependency")
        if path in rename_paths:
            signals.append("public_api_rename")
        if path in config_paths:
            signals.append("config_edit")
        if path in oversized_paths:
            signals.append("oversized_hunk")
        if path in formatting_paths:
            signals.append("formatting_only")

        additions_for_file, deletions_for_file = file_metrics[id(file_change)]
        reasons = []
        if overlap:
            reasons.append("intent/path overlap: %s" % ", ".join(overlap))
        elif intent_words:
            reasons.append("no intent/path keyword overlap")
        else:
            reasons.append("intent has no usable keywords")
        reasons.extend(signal.replace("_", " ") for signal in signals)
        item = {
            "path": path,
            "subsystem": subsystem(path),
            "relatedness": score,
            "overlap": overlap,
            "signals": signals,
            "reasons": reasons,
            "additions": additions_for_file,
            "deletions": deletions_for_file,
        }
        (in_scope if overlap else likely_creep).append(item)

    return {
        "intent": intent,
        "in_scope": in_scope,
        "likely_creep": likely_creep,
        "new_deps": new_deps,
        "api_renames": api_renames,
        "config_edits": sorted(config_edits, key=lambda item: item["path"]),
        "stats": {
            "files_touched": len(files),
            "additions": additions,
            "deletions": deletions,
            "subsystems": dict(sorted(subsystems.items())),
            "oversized_hunks": oversized,
            "formatting_only_files": sorted(formatting_only),
            "hunk_threshold": hunk_threshold,
        },
    }


def run_git(repo, args):
    result = subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout


def read_diff(args):
    if args.diff == "-":
        return sys.stdin.read()
    if args.diff:
        with open(args.diff, encoding="utf-8", errors="replace") as handle:
            return handle.read()
    command = ["diff", "--no-ext-diff", "--no-textconv", "--unified=3"]
    if args.staged:
        command.append("--cached")
    elif args.base:
        command.append("%s...HEAD" % args.base)
    command.append("--")
    return run_git(args.repo, command)


def fallback_intent(repo):
    try:
        branch = run_git(repo, ["branch", "--show-current"]).strip()
    except RuntimeError:
        branch = ""
    return branch or "detached HEAD"


def print_human(report):
    stats = report["stats"]
    print("SCOPE REPORT")
    print("intent: %s" % report["intent"])
    print(
        "files: %(files_touched)d  additions: %(additions)d  deletions: %(deletions)d"
        % stats
    )
    print("subsystems: %s" % (", ".join(
        "%s=%d" % item for item in stats["subsystems"].items()
    ) or "none"))
    print("in scope: %d" % len(report["in_scope"]))
    for item in report["in_scope"]:
        print("  KEEP? %s (%s)" % (item["path"], "; ".join(item["reasons"])))
    print("likely creep: %d" % len(report["likely_creep"]))
    for item in report["likely_creep"]:
        print("  SPLIT OR JUSTIFY: %s (%s)" % (item["path"], "; ".join(item["reasons"])))


def build_parser():
    parser = argparse.ArgumentParser(description="Detect scope signals in a git unified diff.")
    parser.add_argument("--repo", default=".", help="Target git repository (default: current directory).")
    parser.add_argument("--diff", help="Read a unified diff from a file, or '-' for stdin.")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--staged", action="store_true", help="Analyze the staged diff.")
    modes.add_argument("--base", help="Analyze BASE...HEAD for a branch diff.")
    parser.add_argument("--intent", help="One-line intent; defaults to the current branch name.")
    parser.add_argument(
        "--hunk-threshold",
        type=int,
        default=DEFAULT_HUNK_THRESHOLD,
        help="Flag hunks with churn above this value (default: 80).",
    )
    parser.add_argument("--json", action="store_true", help="Emit the full JSON report.")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.diff and (args.staged or args.base):
        parser.error("--diff cannot be combined with --staged or --base")
    if args.hunk_threshold < 1:
        parser.error("--hunk-threshold must be at least 1")

    try:
        diff_text = read_diff(args)
        intent = args.intent.strip() if args.intent and args.intent.strip() else fallback_intent(args.repo)
        report = classify(parse_diff(diff_text), intent, args.hunk_threshold)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print("scope_creep.py: error: %s" % error, file=sys.stderr)
        return 2

    if args.json:
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
