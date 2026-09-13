#!/usr/bin/env python3
"""
Map a local git unified diff to an evidence-backed shortlist of tests to run.

Usage:
    python3 impact_map.py --repo . --json
    python3 impact_map.py --repo . --staged --json
    python3 impact_map.py --repo . --base main --json
    python3 impact_map.py --repo . --diff change.diff --json

Python 3.11 stdlib only. Runs locally and never changes the target repository.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from collections import defaultdict, deque


WEIGHTS = {
    "path": 8,
    "self": 7,
    "import": 5,
    "importer": 4,
    "symbol": 3,
    "cochange": 2,
    "name": 1,
}
DEFAULT_LIMIT = 20
DEFAULT_DEPTH = 3
MAX_WALK_FILES = 4000
MAX_FILE_BYTES = 1_000_000
GIT_TIMEOUT = 30
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    ".mypy_cache", ".tox", ".pytest_cache", "coverage", ".next", "target",
    ".eggs", ".ruff_cache",
}
CODE_EXTS = {
    ".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".go", ".rb", ".java", ".rs",
}
SRC_PREFIXES = ("src/", "lib/", "app/", "pkg/")
HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")
PY_FROM_RE = re.compile(r"^\s*from\s+(\.*)([\w.]*)\s+import\b")
PY_IMPORT_RE = re.compile(r"^\s*import\s+([\w.]+)")
JS_FROM_RE = re.compile(
    r"""(?:from|import|require)\s*\(?\s*['"]([^'"]+)['"]"""
)
PY_SYMBOL_RE = re.compile(
    r"^\s*(?:async\s+)?(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)"
)
JS_SYMBOL_RE = re.compile(
    r"^\s*(?:export\s+)?(?:async\s+)?(?:function|class|const|let|var)\s+"
    r"([A-Za-z_][A-Za-z0-9_]*)"
)
GO_SYMBOL_RE = re.compile(
    r"^\s*func\s+(?:\([^)]+\)\s+)?([A-Za-z_][A-Za-z0-9_]*)"
)
WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{3,}")


def clean_path(value):
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
    """Parse file and hunk structure from a unified diff. No git textconv."""
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
            hunk["lines"].append({"marker": marker, "text": raw[1:]})
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


def posix(path):
    return path.replace("\\", "/")


def is_test_path(path):
    path = posix(path)
    name = os.path.basename(path)
    stem, ext = os.path.splitext(name)
    if ext.lower() not in CODE_EXTS:
        return False
    parts = path.split("/")
    if any(part in {"tests", "test", "spec", "__tests__"} for part in parts[:-1]):
        return True
    lower = name.lower()
    if name.startswith("test_") or stem.endswith("_test"):
        return True
    if ".test." in lower or ".spec." in lower:
        return True
    if stem.endswith("Test") or stem.endswith("Tests"):
        return True
    return False


def is_code_path(path):
    return os.path.splitext(posix(path))[1].lower() in CODE_EXTS


def walk_code_files(repo):
    """Yield repo-relative posix paths for source and test files."""
    found = []
    repo = os.path.abspath(repo)
    for dirpath, dirs, files in os.walk(repo):
        dirs[:] = [
            name for name in dirs
            if name not in SKIP_DIRS and not name.startswith(".")
        ]
        for name in files:
            if len(found) >= MAX_WALK_FILES:
                return found
            ext = os.path.splitext(name)[1].lower()
            if ext not in CODE_EXTS:
                continue
            full = os.path.join(dirpath, name)
            rel = posix(os.path.relpath(full, repo))
            if rel.startswith("../"):
                continue
            found.append(rel)
    return found


def read_text(repo, rel):
    full = os.path.join(repo, rel)
    try:
        if os.path.getsize(full) > MAX_FILE_BYTES:
            return ""
        with open(full, encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return ""


def module_candidates(rel):
    """Filesystem paths a Python/JS import of this file might name."""
    rel = posix(rel)
    no_ext, ext = os.path.splitext(rel)
    names = {rel, no_ext}
    if os.path.basename(no_ext) == "index":
        names.add(os.path.dirname(no_ext))
    if os.path.basename(no_ext) == "__init__":
        names.add(os.path.dirname(no_ext))
    dotted = no_ext.replace("/", ".")
    names.add(dotted)
    for prefix in SRC_PREFIXES:
        if rel.startswith(prefix):
            trimmed = rel[len(prefix):]
            no_ext_t = os.path.splitext(trimmed)[0]
            names.add(trimmed)
            names.add(no_ext_t.replace("/", "."))
    return {item for item in names if item}


def resolve_import(importer, spec):
    """Return candidate relative paths for an import specifier."""
    spec = spec.strip()
    if not spec or spec.startswith(("http:", "https:", "node:", "data:")):
        return []
    if spec.startswith("@"):
        return []

    if spec.startswith("."):
        dots = len(spec) - len(spec.lstrip("."))
        rest = spec[dots:].lstrip("/")
        base = os.path.dirname(importer)
        for _ in range(max(0, dots - 1)):
            base = os.path.dirname(base)
        joined = posix(os.path.normpath(os.path.join(base or ".", rest)))
        if joined.startswith("../"):
            return []
        return _with_exts(joined)

    if "/" in spec or spec.endswith((".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs")):
        return _with_exts(spec.lstrip("./"))

    dotted = spec.replace(".", "/")
    return _with_exts(dotted)


def _with_exts(path):
    path = posix(path).strip("/")
    if not path or path == ".":
        return []
    out = [path]
    root, ext = os.path.splitext(path)
    if not ext:
        for suffix in (
            ".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
            ".go", ".rb",
            "/__init__.py", "/index.js", "/index.ts", "/index.tsx",
        ):
            out.append(path + suffix)
    else:
        out.append(root)
    return out


def extract_imports(rel, text):
    specs = []
    ext = os.path.splitext(rel)[1].lower()
    for line in text.splitlines():
        if ext in {".py", ".pyi"}:
            match = PY_FROM_RE.match(line)
            if match:
                dots, rest = match.group(1), match.group(2)
                if dots:
                    specs.append("." * len(dots) + rest)
                elif rest:
                    specs.append(rest)
                continue
            match = PY_IMPORT_RE.match(line)
            if match:
                specs.append(match.group(1))
        else:
            for match in JS_FROM_RE.finditer(line):
                specs.append(match.group(1))
    return specs


def extract_symbols(file_change):
    names = set()
    for hunk in file_change["hunks"]:
        for entry in hunk["lines"]:
            if entry["marker"] not in {"+", "-"}:
                continue
            line = entry["text"]
            for regex in (PY_SYMBOL_RE, JS_SYMBOL_RE, GO_SYMBOL_RE):
                match = regex.match(line)
                if match:
                    name = match.group(1)
                    if not name.startswith("_"):
                        names.add(name)
    return names


def path_pairs(source):
    """Conventional test paths for a source file that exists in the tree."""
    source = posix(source)
    directory, name = os.path.split(source)
    stem, ext = os.path.splitext(name)
    rel_dir = directory
    for prefix in SRC_PREFIXES:
        if rel_dir == prefix.rstrip("/") or rel_dir.startswith(prefix):
            rel_dir = rel_dir[len(prefix):]
            break
    candidates = [
        posix(os.path.join("tests", "test_%s%s" % (stem, ext))),
        posix(os.path.join("test", "test_%s%s" % (stem, ext))),
        posix(os.path.join("tests", "%s_test%s" % (stem, ext))),
        posix(os.path.join(directory, "test_%s%s" % (stem, ext))),
        posix(os.path.join(directory, "%s_test%s" % (stem, ext))),
        posix(os.path.join(directory, "%s.test%s" % (stem, ext))),
        posix(os.path.join(directory, "%s.spec%s" % (stem, ext))),
        posix(os.path.join(directory, "__tests__", "%s.test%s" % (stem, ext))),
        posix(os.path.join(directory, "__tests__", "%s.spec%s" % (stem, ext))),
    ]
    if rel_dir:
        candidates.extend([
            posix(os.path.join("tests", rel_dir, "test_%s%s" % (stem, ext))),
            posix(os.path.join("tests", rel_dir, "%s_test%s" % (stem, ext))),
            posix(os.path.join("tests", rel_dir, "%s.test%s" % (stem, ext))),
            posix(os.path.join("spec", rel_dir, "%s_spec%s" % (stem, ext))),
        ])
    if ext in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
        for js_ext in (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"):
            candidates.append(posix(os.path.join(directory, "%s.test%s" % (stem, js_ext))))
            candidates.append(posix(os.path.join(directory, "%s.spec%s" % (stem, js_ext))))
    cleaned = []
    seen = set()
    for item in candidates:
        item = posix(os.path.normpath(item))
        if item.startswith("../") or item in seen:
            continue
        seen.add(item)
        cleaned.append(item)
    return cleaned


def stem_tokens(path):
    name = os.path.splitext(os.path.basename(path))[0]
    name = re.sub(r"^(test_|spec_)", "", name)
    name = re.sub(r"(_test|_spec|\.test|\.spec)$", "", name)
    return {token.lower() for token in re.split(r"[^A-Za-z0-9]+", name) if len(token) >= 3}


def add_evidence(bucket, path, kind, detail, changed):
    item = bucket[path]
    item["path"] = path
    item["changed_files"].add(changed)
    key = (kind, detail)
    if key in item["_seen"]:
        return
    item["_seen"].add(key)
    item["evidence"].append({
        "kind": kind,
        "detail": detail,
        "weight": WEIGHTS[kind],
    })
    item["score"] += WEIGHTS[kind]


def run_git(repo, args):
    result = subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
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


def diff_source_label(args):
    if args.diff:
        return "diff"
    if args.staged:
        return "staged"
    if args.base:
        return "base:%s" % args.base
    return "working"


def build_import_graph(repo, files):
    """Map each file to files that import it (reverse dependents)."""
    path_set = set(files)
    importers = defaultdict(set)
    for rel in files:
        text = read_text(repo, rel)
        if not text:
            continue
        for spec in extract_imports(rel, text):
            for candidate in resolve_import(rel, spec):
                if candidate in path_set:
                    importers[candidate].add(rel)
                    break
                # Python dotted modules already expanded by resolve_import.
    return importers


def reverse_impact(changed, importers, depth):
    """BFS through reverse imports. Returns path -> (distance, via)."""
    found = {}
    queue = deque()
    for path in changed:
        queue.append((path, 0, None))
        found[path] = (0, None)
    while queue:
        path, distance, via = queue.popleft()
        if distance >= depth:
            continue
        for importer in importers.get(path, ()):
            if importer in found:
                continue
            found[importer] = (distance + 1, path)
            queue.append((importer, distance + 1, path))
    return found


def cochange_tests(repo, changed_path, test_set):
    """Tests that appear in recent commits alongside a changed file."""
    try:
        output = run_git(
            repo,
            ["log", "-n", "40", "--name-only", "--format=", "--", changed_path],
        )
    except (RuntimeError, subprocess.TimeoutExpired):
        return []
    counts = defaultdict(int)
    for line in output.splitlines():
        path = posix(line.strip())
        if path in test_set:
            counts[path] += 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def classify(repo, files, tree_files, args):
    test_set = {path for path in tree_files if is_test_path(path)}
    source_set = {path for path in tree_files if is_code_path(path)}
    importers = build_import_graph(repo, tree_files)

    changed = []
    for file_change in files:
        path = posix(file_change["path"])
        if path in {"unknown", "/dev/null"}:
            continue
        kind = "test" if is_test_path(path) else ("source" if is_code_path(path) else "other")
        changed.append({
            "path": path,
            "kind": kind,
            "old_path": file_change.get("old_path"),
            "symbols": sorted(extract_symbols(file_change)),
        })

    impact = reverse_impact(
        [item["path"] for item in changed if item["kind"] in {"source", "test"}],
        importers,
        args.max_depth,
    )

    bucket = defaultdict(lambda: {
        "path": "",
        "score": 0,
        "evidence": [],
        "changed_files": set(),
        "_seen": set(),
    })

    for item in changed:
        path = item["path"]
        if item["kind"] == "test" and path in test_set:
            add_evidence(bucket, path, "self", "changed test file", path)

        if item["kind"] != "source":
            continue

        for candidate in path_pairs(path):
            if candidate in test_set:
                add_evidence(
                    bucket, candidate, "path",
                    "conventional pair of %s" % path, path,
                )

        source_tokens = stem_tokens(path)
        for test_path in test_set:
            if not (source_tokens & stem_tokens(test_path)):
                continue
            if test_path in bucket and any(
                ev["kind"] == "path" for ev in bucket[test_path]["evidence"]
            ):
                continue
            # Shared basename token is a weak hint, not a path pair.
            if os.path.splitext(os.path.basename(test_path))[0].replace("test_", "").replace("_test", "") == \
                    os.path.splitext(os.path.basename(path))[0]:
                add_evidence(
                    bucket, test_path, "name",
                    "shared stem with %s" % path, path,
                )

        for symbol in item["symbols"]:
            pattern = re.compile(r"\b%s\b" % re.escape(symbol))
            for test_path in test_set:
                text = read_text(repo, test_path)
                if pattern.search(text):
                    add_evidence(
                        bucket, test_path, "symbol",
                        "%s mentioned (from %s)" % (symbol, path), path,
                    )

        if not args.no_history:
            for test_path, count in cochange_tests(repo, path, test_set):
                add_evidence(
                    bucket, test_path, "cochange",
                    "committed with %s in %d recent commit%s" % (
                        path, count, "" if count == 1 else "s",
                    ),
                    path,
                )

    for path, (distance, via) in impact.items():
        if path not in test_set or distance == 0:
            continue
        # Attribute to the nearest changed source on the reverse chain.
        origin = path
        current = path
        hops = []
        seen = set()
        while current in impact and impact[current][1] and current not in seen:
            seen.add(current)
            parent = impact[current][1]
            hops.append(parent)
            current = parent
        origin = hops[-1] if hops else path
        if distance == 1:
            add_evidence(
                bucket, path, "import",
                "imports %s" % origin, origin,
            )
        else:
            via_path = via or origin
            add_evidence(
                bucket, path, "importer",
                "imports %s, which depends on %s" % (via_path, origin), origin,
            )

    recommended = []
    for item in bucket.values():
        recommended.append({
            "path": item["path"],
            "score": item["score"],
            "evidence": sorted(
                item["evidence"],
                key=lambda ev: (-ev["weight"], ev["kind"], ev["detail"]),
            ),
            "changed_files": sorted(item["changed_files"]),
        })
    recommended.sort(key=lambda item: (-item["score"], item["path"]))
    recommended = recommended[: args.limit]

    mapped_changes = set()
    for item in recommended:
        mapped_changes.update(item["changed_files"])
    unmapped = [
        item["path"] for item in changed
        if item["path"] not in mapped_changes
    ]

    return {
        "diff_source": diff_source_label(args),
        "repo": os.path.abspath(repo),
        "changed_files": [
            {"path": item["path"], "kind": item["kind"], "symbols": item["symbols"]}
            for item in changed
        ],
        "recommended": recommended,
        "unmapped": unmapped,
        "stats": {
            "files_changed": len(changed),
            "tests_discovered": len(test_set),
            "sources_scanned": len(source_set),
            "recommended": len(recommended),
            "mapped_changes": len(mapped_changes),
            "unmapped_changes": len(unmapped),
            "limit": args.limit,
            "max_depth": args.max_depth,
        },
    }


def print_human(report):
    stats = report["stats"]
    print("TEST IMPACT")
    print("source: %s" % report["diff_source"])
    print(
        "changed: %d  tests in repo: %d  recommended: %d"
        % (stats["files_changed"], stats["tests_discovered"], stats["recommended"])
    )
    if not report["recommended"]:
        print("  (no evidence-backed tests)")
    for item in report["recommended"]:
        print()
        print("  %s  score=%d" % (item["path"], item["score"]))
        for ev in item["evidence"]:
            print("    %s: %s" % (ev["kind"], ev["detail"]))
    if report["unmapped"]:
        print()
        print("unmapped (no test evidence):")
        for path in report["unmapped"]:
            print("  %s" % path)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Map a git unified diff to likely tests to run.",
    )
    parser.add_argument("--repo", default=".", help="Target git repository (default: current directory).")
    parser.add_argument("--diff", help="Read a unified diff from a file, or '-' for stdin.")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--staged", action="store_true", help="Analyze the staged diff.")
    modes.add_argument("--base", help="Analyze BASE...HEAD for a branch diff.")
    parser.add_argument(
        "--limit", type=int, default=DEFAULT_LIMIT,
        help="Maximum tests to recommend (default: %d)." % DEFAULT_LIMIT,
    )
    parser.add_argument(
        "--max-depth", type=int, default=DEFAULT_DEPTH,
        help="Reverse-import walk depth (default: %d)." % DEFAULT_DEPTH,
    )
    parser.add_argument(
        "--no-history", action="store_true",
        help="Skip git co-change history (path, import, and symbol evidence only).",
    )
    parser.add_argument("--json", action="store_true", help="Emit the full JSON report.")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.diff and (args.staged or args.base):
        parser.error("--diff cannot be combined with --staged or --base")
    if args.limit < 1:
        parser.error("--limit must be at least 1")
    if args.max_depth < 1:
        parser.error("--max-depth must be at least 1")

    repo = os.path.abspath(args.repo)
    try:
        diff_text = read_diff(args)
        files = parse_diff(diff_text)
        tree_files = walk_code_files(repo)
        report = classify(repo, files, tree_files, args)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print("impact_map.py: error: %s" % error, file=sys.stderr)
        return 2

    if args.json:
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
