#!/usr/bin/env python3
"""
flip_flop.py — finds code regions that keep getting rewritten back and forth
across git history (a deterministic "indecision hotspot" detector).

Usage:
    python3 flip_flop.py --repo /path/to/repo [--paths PATH ...] [--since DATE]
                          [--min-flips N] [--top N] [--max-files N]
                          [--max-commits-per-file N] [--json]

Read-only: never modifies the working tree, index, commits, or branches.
Makes no network calls; only invokes local `git` and Python's stdlib.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from difflib import SequenceMatcher

DEFAULT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".java", ".rb", ".rs",
    ".c", ".h", ".cpp", ".hpp", ".cs", ".php", ".kt", ".swift", ".scala",
}
CONTEXT_LINES = 2  # lines of stable context used to anchor a changed block


def run_git(repo, args):
    result = subprocess.run(
        ["git", "-C", repo] + args,
        capture_output=True, text=False, check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", errors="replace")


def _looks_like_source(path):
    return any(path.endswith(ext) for ext in DEFAULT_EXTENSIONS)


def discover_hot_files(repo, since, paths, max_files):
    """Cheap single-pass discovery of the most-changed files, so a full scan
    of a large repo stays fast: only files touched often enough to plausibly
    oscillate get the expensive per-commit walk below."""
    if paths:
        return list(paths)
    args = ["log", "--name-only", "--pretty=format:"]
    if since:
        args += ["--since", since]
    output = run_git(repo, args)
    if output is None:
        return []
    counts = defaultdict(int)
    for line in output.splitlines():
        line = line.strip()
        if line:
            counts[line] += 1
    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    candidates = [path for path, count in ranked if count >= 3 and _looks_like_source(path)]
    return candidates[:max_files]


def file_commit_history(repo, path, since, max_commits):
    args = ["log", "--format=%H|%ad|%an", "--date=short", "--reverse"]
    if since:
        args += ["--since", since]
    args += ["--", path]
    output = run_git(repo, args)
    if not output:
        return []
    commits = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            commits.append({"hash": parts[0], "date": parts[1], "author": parts[2]})
    if len(commits) > max_commits:
        commits = commits[-max_commits:]  # keep the most recent window
    return commits


def blob_at(repo, commit_hash, path):
    result = subprocess.run(
        ["git", "-C", repo, "show", "%s:%s" % (commit_hash, path)],
        capture_output=True, check=False,
    )
    if result.returncode != 0:
        return None
    data = result.stdout
    if b"\x00" in data:  # treat as binary, skip
        return None
    return data.decode("utf-8", errors="replace").splitlines()


def normalize(lines):
    return "\n".join(line.rstrip() for line in lines)


def anchor_key(path, prev_lines, start, end):
    before_ctx = [ln.strip() for ln in prev_lines[max(0, start - CONTEXT_LINES):start] if ln.strip()]
    after_ctx = [ln.strip() for ln in prev_lines[end:end + CONTEXT_LINES] if ln.strip()]
    label = " / ".join((before_ctx[-1:] + after_ctx[:1])) or "<file start or end>"
    digest = hashlib.sha1(
        ("%s|%s|%s" % (path, "|".join(before_ctx), "|".join(after_ctx))).encode("utf-8")
    ).hexdigest()[:10]
    return digest, label


def changed_blocks(prev_lines, curr_lines):
    matcher = SequenceMatcher(None, prev_lines, curr_lines, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "delete", "insert") and (i2 > i1 or j2 > j1):
            yield i1, i2, j1, j2


def analyze_file(repo, path, since, max_commits):
    history = defaultdict(list)  # anchor digest -> chronological list of events
    labels = {}
    commits = file_commit_history(repo, path, since, max_commits)
    prev_lines = []
    for commit in commits:
        curr_lines = blob_at(repo, commit["hash"], path)
        if curr_lines is None:
            prev_lines = []
            continue
        for i1, i2, j1, j2 in changed_blocks(prev_lines, curr_lines):
            before_text = normalize(prev_lines[i1:i2])
            after_text = normalize(curr_lines[j1:j2])
            if before_text == after_text:
                continue
            digest, label = anchor_key(path, prev_lines, i1, i2)
            labels.setdefault(digest, label)
            history[digest].append({
                "commit": commit["hash"][:10],
                "date": commit["date"],
                "author": commit["author"],
                "text": after_text,
            })
        prev_lines = curr_lines

    hotspots = []
    for digest, events in history.items():
        if len(events) < 3:
            continue
        seen_at = {}
        flips = []
        for idx, event in enumerate(events):
            key = event["text"]
            if key in seen_at and idx - seen_at[key] >= 2:
                flips.append({
                    "back_to_commit": events[seen_at[key]]["commit"],
                    "back_to_date": events[seen_at[key]]["date"],
                    "at_commit": event["commit"],
                    "at_date": event["date"],
                })
            seen_at[key] = idx
        if flips:
            authors = sorted({e["author"] for e in events})
            hotspots.append({
                "file": path,
                "anchor": labels.get(digest, "<unknown>"),
                "flip_count": len(flips),
                "change_count": len(events),
                "authors": authors,
                "first_date": events[0]["date"],
                "last_date": events[-1]["date"],
                "flips": flips,
                "sample_states": sorted({e["text"] for e in events})[:2],
            })
    return hotspots


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="path to the git repository")
    parser.add_argument("--paths", nargs="*", default=None, help="specific files/dirs to analyze exhaustively")
    parser.add_argument("--since", default=None, help="git-log style date filter, e.g. '2 years ago'")
    parser.add_argument("--min-flips", type=int, default=1)
    parser.add_argument("--top", type=int, default=15)
    parser.add_argument("--max-files", type=int, default=300)
    parser.add_argument("--max-commits-per-file", type=int, default=200)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    files = discover_hot_files(args.repo, args.since, args.paths, args.max_files)
    all_hotspots = []
    for path in files:
        try:
            all_hotspots.extend(analyze_file(args.repo, path, args.since, args.max_commits_per_file))
        except Exception:
            continue  # one file's failure must never abort the whole run

    all_hotspots = [h for h in all_hotspots if h["flip_count"] >= args.min_flips]
    all_hotspots.sort(key=lambda h: (h["flip_count"], len(h["authors"])), reverse=True)
    top = all_hotspots[: args.top]

    if args.as_json:
        print(json.dumps({"files_scanned": len(files), "hotspots": top}, indent=2))
        return 0

    print("Flip-Flop Report — %d file(s) scanned, %d hotspot(s) found\n" % (len(files), len(all_hotspots)))
    for rank, hotspot in enumerate(top, start=1):
        print("%d. %s" % (rank, hotspot["file"]))
        print("   near: %s" % hotspot["anchor"])
        print("   flipped %d time(s) across %d change(s) by %s (%s -> %s)" % (
            hotspot["flip_count"], hotspot["change_count"],
            ", ".join(hotspot["authors"]), hotspot["first_date"], hotspot["last_date"],
        ))
        for flip in hotspot["flips"]:
            print("     - reverted to the state from %s on %s" % (flip["back_to_commit"], flip["back_to_date"]))
        print()
    if not top:
        print("No flip-flop hotspots found in the scanned window.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
