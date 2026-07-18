#!/usr/bin/env python3
"""Reconstruct why a file or line range exists from local git history.

Usage:
    python3 archaeologist.py REPO FILE [--lines A-B] [--json]

Python 3.8+, stdlib only. Read-only and offline.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict


LINE_RANGE_RE = re.compile(r"^([1-9][0-9]*)-([1-9][0-9]*)$")
ISSUE_RE = re.compile(r"(?<![\w/])(?:#[0-9]+|(?:pr|issue|gh)[\s:#-]*[0-9]+)", re.I)
INTENT_PATTERNS = (
    ("revert", re.compile(r"\brevert(?:ed|s|ing)?\b", re.I)),
    ("workaround", re.compile(r"\bwork[ -]?around\b", re.I)),
    ("temporary", re.compile(r"\b(?:temporary|temporarily|temp)\b", re.I)),
    ("todo", re.compile(r"\bTODO\b", re.I)),
)


class ArchaeologistError(Exception):
    """A user-facing validation or git error."""


def git(repo, args, required=True):
    """Run a read-only git command and return stdout."""
    try:
        result = subprocess.run(
            ["git", "-C", repo, *args],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise ArchaeologistError("git is not installed or is not on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise ArchaeologistError("git command timed out") from exc
    if result.returncode != 0 and required:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise ArchaeologistError(detail)
    return result.stdout if result.returncode == 0 else ""


def normalize_inputs(repo_arg, file_arg):
    repo_hint = os.path.abspath(os.path.expanduser(repo_arg))
    if not os.path.isdir(repo_hint):
        raise ArchaeologistError("repository path is not a directory: %s" % repo_arg)
    root = git(repo_hint, ["rev-parse", "--show-toplevel"]).strip()
    if not root:
        raise ArchaeologistError("not a git repository: %s" % repo_arg)
    root = os.path.abspath(root)

    if os.path.isabs(file_arg):
        candidate = os.path.abspath(os.path.expanduser(file_arg))
    else:
        candidate = os.path.abspath(os.path.join(root, file_arg))
    try:
        inside = os.path.commonpath([root, candidate]) == root
    except ValueError:
        inside = False
    if not inside:
        raise ArchaeologistError("file must be inside the repository")

    relative = os.path.relpath(candidate, root).replace(os.sep, "/")
    tracked = git(root, ["ls-files", "--error-unmatch", "--", relative], required=False)
    if not tracked.strip():
        raise ArchaeologistError("file is not tracked at HEAD: %s" % relative)
    return root, relative


def parse_line_range(value):
    if value is None:
        return None
    match = LINE_RANGE_RE.match(value)
    if not match:
        raise ArchaeologistError("line range must use positive A-B form, such as 40-72")
    start, end = int(match.group(1)), int(match.group(2))
    if start > end:
        raise ArchaeologistError("line range start must not exceed its end")
    return start, end


def validate_range(repo, path, line_range):
    if line_range is None:
        return
    content = git(repo, ["show", "HEAD:%s" % path])
    line_count = len(content.splitlines())
    if line_range[1] > line_count:
        raise ArchaeologistError(
            "line range ends at %d, but %s has %d lines at HEAD"
            % (line_range[1], path, line_count)
        )


def history_hashes(repo, path, line_range):
    if line_range:
        selector = "%d,%d:%s" % (line_range[0], line_range[1], path)
        output = git(repo, ["log", "--format=%H", "--no-patch", "-L", selector])
    else:
        output = git(
            repo,
            ["log", "--format=%H", "--no-patch", "--follow", "--", path],
        )
    newest_first = [line.strip() for line in output.splitlines() if line.strip()]
    hashes = []
    seen = set()
    for commit_hash in reversed(newest_first):
        if commit_hash not in seen:
            seen.add(commit_hash)
            hashes.append(commit_hash)
    if not hashes:
        raise ArchaeologistError("no commits found for %s" % path)
    return hashes


def classify_message(subject, body):
    text = "%s\n%s" % (subject, body)
    lowered = text.lower()
    if subject.lower().startswith("merge "):
        return "merge"
    if re.search(r"\brevert(?:ed|s|ing)?\b", lowered):
        return "revert"
    if re.search(r"\bhot[ -]?fix\b", lowered):
        return "hotfix"
    if re.search(r"\b(refactor|cleanup|restructure|rename)\b", lowered):
        return "refactor"
    if re.search(r"\b(fix|fixed|fixes|bug|patch)\b", lowered):
        return "fix"
    if re.search(r"\b(feat|feature|add|added|introduce|implement)\b", lowered):
        return "feat"
    return "other"


def changed_file_details(repo, commit_hash):
    output = git(
        repo,
        [
            "diff-tree", "--root", "--no-commit-id", "--name-status", "-r",
            "-M", commit_hash, "--",
        ],
    )
    paths = set()
    renames = []
    for line in output.splitlines():
        fields = line.split("\t")
        if len(fields) >= 3 and fields[0].startswith("R"):
            old_path, new_path = fields[1], fields[2]
            paths.update((old_path, new_path))
            renames.append({"from": old_path, "to": new_path})
        elif len(fields) >= 2:
            paths.add(fields[-1])
    return sorted(paths), renames


def intent_signals(commit_hash, subject, body):
    text = "%s\n%s" % (subject, body)
    signals = []
    for match in ISSUE_RE.finditer(text):
        signals.append({
            "type": "issue_reference",
            "commit": commit_hash,
            "evidence": match.group(0),
            "subject": subject,
        })
    for signal_type, pattern in INTENT_PATTERNS:
        match = pattern.search(text)
        if match:
            signals.append({
                "type": signal_type,
                "commit": commit_hash,
                "evidence": match.group(0),
                "subject": subject,
            })
    return signals


def read_commit(repo, commit_hash):
    fmt = "%H%x00%an%x00%ae%x00%aI%x00%s%x00%b"
    raw = git(repo, ["show", "-s", "--format=%s" % fmt, commit_hash]).rstrip("\n")
    parts = raw.split("\x00", 5)
    if len(parts) != 6:
        raise ArchaeologistError("could not parse commit metadata for %s" % commit_hash)
    full_hash, author, email, date, subject, body = parts
    signals = intent_signals(full_hash, subject, body)
    files, renames = changed_file_details(repo, full_hash)
    return {
        "hash": full_hash,
        "short_hash": full_hash[:12],
        "author": author,
        "email": email,
        "date": date,
        "subject": subject,
        "body": body.strip(),
        "category": classify_message(subject, body),
        "changed_files": files,
        "renames": renames,
        "intent_signals": [signal["type"] for signal in signals],
    }, signals


def blame_authors(repo, path, line_range):
    args = ["blame", "--line-porcelain"]
    if line_range:
        args.extend(["-L", "%d,%d" % line_range])
    args.extend(["HEAD", "--", path])
    output = git(repo, args, required=False)
    counts = Counter()
    names = {}
    current_name = ""
    current_email = ""
    for line in output.splitlines():
        if line.startswith("author "):
            current_name = line[7:]
        elif line.startswith("author-mail "):
            current_email = line[12:].strip("<>")
        elif line.startswith("\t"):
            if current_email:
                key = current_email.lower()
                counts[key] += 1
                names[key] = (current_name, current_email)
            current_name = ""
            current_email = ""
    return counts, names


def summarize_authors(repo, path, line_range, timeline):
    line_counts, names = blame_authors(repo, path, line_range)
    commit_counts = Counter()
    for entry in timeline:
        key = entry["email"].lower()
        commit_counts[key] += 1
        names.setdefault(key, (entry["author"], entry["email"]))
    authors = []
    for key in set(line_counts) | set(commit_counts):
        name, email = names[key]
        authors.append({
            "name": name,
            "email": email,
            "current_lines": line_counts[key],
            "timeline_commits": commit_counts[key],
        })
    return sorted(
        authors,
        key=lambda author: (
            -author["current_lines"], -author["timeline_commits"],
            author["name"].lower(), author["email"].lower(),
        ),
    )


def historical_paths(path, timeline):
    aliases = {path}
    for entry in reversed(timeline):
        for rename in entry["renames"]:
            if rename["to"] in aliases:
                aliases.add(rename["from"])
    return aliases


def summarize_co_changes(path, timeline):
    threshold = max(2, (len(timeline) + 2) // 3)
    aliases = historical_paths(path, timeline)
    commits_by_file = defaultdict(list)
    for entry in timeline:
        for changed in entry["changed_files"]:
            if changed not in aliases:
                commits_by_file[changed].append(entry["hash"])
    co_changed = []
    for changed, commits in commits_by_file.items():
        if len(commits) >= threshold:
            co_changed.append({
                "file": changed,
                "count": len(commits),
                "commit_ratio": round(len(commits) / len(timeline), 3),
                "commits": commits,
            })
    return (
        threshold,
        sorted(co_changed, key=lambda item: (-item["count"], item["file"])),
        sorted(aliases),
    )


def build_report(repo, path, line_range):
    hashes = history_hashes(repo, path, line_range)
    timeline = []
    signals = []
    for commit_hash in hashes:
        entry, commit_signals = read_commit(repo, commit_hash)
        timeline.append(entry)
        signals.extend(commit_signals)
    threshold, co_changed, aliases = summarize_co_changes(path, timeline)
    return {
        "region": {
            "repo": repo,
            "file": path,
            "mode": "lines" if line_range else "file",
            "lines": (
                {"start": line_range[0], "end": line_range[1]}
                if line_range else None
            ),
            "co_change_threshold": threshold,
            "historical_paths": aliases,
        },
        "introduced_by": timeline[0],
        "timeline": timeline,
        "co_changed": co_changed,
        "authors": summarize_authors(repo, path, line_range, timeline),
        "intent_signals": signals,
    }


def print_human(report):
    region = report["region"]
    target = region["file"]
    if region["lines"]:
        target += ":%d-%d" % (
            region["lines"]["start"], region["lines"]["end"],
        )
    intro = report["introduced_by"]
    print("COMMIT ARCHAEOLOGIST: %s" % target)
    print("Introduced by %s %s: %s" % (
        intro["short_hash"], intro["author"], intro["subject"],
    ))
    print("\nTIMELINE")
    for entry in report["timeline"]:
        print("  %s  %-8s  %s" % (
            entry["short_hash"], entry["category"], entry["subject"],
        ))
    print("\nREPEATED CO-CHANGES")
    if report["co_changed"]:
        for item in report["co_changed"]:
            print("  %dx  %s" % (item["count"], item["file"]))
    else:
        print("  none above threshold")
    print("\nINTENT SIGNALS")
    if report["intent_signals"]:
        for signal in report["intent_signals"]:
            print("  %s  %s  %s" % (
                signal["commit"][:12], signal["type"], signal["evidence"],
            ))
    else:
        print("  none found in commit messages")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Explain why a file or line range exists from local git history.",
    )
    parser.add_argument("repo", help="path to a local git repository")
    parser.add_argument("file", help="tracked file path, relative to the repository")
    parser.add_argument("--lines", metavar="A-B", help="current line range to trace")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="emit the structured dig report as JSON")
    args = parser.parse_args(argv)

    try:
        repo, path = normalize_inputs(args.repo, args.file)
        line_range = parse_line_range(args.lines)
        validate_range(repo, path, line_range)
        report = build_report(repo, path, line_range)
    except ArchaeologistError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
