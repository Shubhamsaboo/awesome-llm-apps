#!/usr/bin/env python3
"""
Check consumer migration notes against an oas_diff.py JSON report.

Convention: each change section is a `##` heading that names the change id
in either `[BRK-003]` form or an HTML comment `<!-- change: BRK-003 -->`.
Breaking sections must include Before and After examples (headings or bold
labels, plus at least two fenced code blocks).

Usage:
    python3 check_notes.py NOTES.md DIFF.json
    python3 check_notes.py --notes NOTES.md --diff DIFF.json

Exit codes:
    0  every breaking change is covered, no unknown ids, every breaking
       section has before/after examples
    1  coverage failure (uncovered ids, unknown ids, or missing examples)
    2  usage or input error (missing files, invalid JSON, no changes array)
"""

import argparse
import json
import os
import re
import sys


ID_RE = re.compile(
    r"\[((?:BRK|ADD|DEP)-\d{3,})\]|<!--\s*change:\s*((?:BRK|ADD|DEP)-\d{3,})\s*-->",
    re.IGNORECASE,
)
HEADING_RE = re.compile(r"^(#{2})\s+(.*)$")
BEFORE_RE = re.compile(r"(?im)^(?:#{3,6}\s+|\*\*)before\b|^before\s*:")
AFTER_RE = re.compile(r"(?im)^(?:#{3,6}\s+|\*\*)after\b|^after\s*:")
FENCE_RE = re.compile(r"^```", re.MULTILINE)


def extract_ids(text):
    found = []
    for match in ID_RE.finditer(text or ""):
        value = match.group(1) or match.group(2)
        found.append(value.upper())
    return found


def split_sections(markdown):
    lines = markdown.splitlines()
    sections = []
    current = {"heading": "(preamble)", "start": 0, "lines": []}
    for index, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if match:
            if current["lines"] or current["heading"] != "(preamble)":
                current["text"] = "\n".join(current["lines"])
                sections.append(current)
            current = {"heading": match.group(2).strip(), "start": index + 1, "lines": [line]}
        else:
            current["lines"].append(line)
    current["text"] = "\n".join(current["lines"])
    sections.append(current)
    return sections


def has_before_after(text):
    if not BEFORE_RE.search(text or ""):
        return False
    if not AFTER_RE.search(text or ""):
        return False
    return len(FENCE_RE.findall(text or "")) >= 2


def load_diff(path):
    with open(path, encoding="utf-8") as handle:
        try:
            data = json.load(handle)
        except json.JSONDecodeError as error:
            raise ValueError("invalid JSON in %s: %s" % (path, error))
    if isinstance(data, list):
        changes = data
    elif isinstance(data, dict) and isinstance(data.get("changes"), list):
        changes = data["changes"]
    else:
        raise ValueError("%s has no changes array" % path)
    return changes


def evaluate(notes_text, changes):
    known = {}
    for item in changes:
        ident = item.get("id")
        if not ident:
            continue
        known[str(ident).upper()] = item
    breaking = {ident for ident, item in known.items() if item.get("severity") == "breaking" or ident.startswith("BRK-")}

    sections = split_sections(notes_text)
    mentioned = []
    missing_examples = []
    for section in sections:
        ids = extract_ids(section["text"])
        mentioned.extend(ids)
        section_breaking = [ident for ident in ids if ident in breaking]
        if section_breaking and not has_before_after(section["text"]):
            for ident in section_breaking:
                if ident not in missing_examples:
                    missing_examples.append(ident)

    mentioned_set = set(mentioned)
    uncovered = sorted(breaking - mentioned_set)
    unknown = sorted(ident for ident in mentioned_set if ident not in known)
    covered = sorted(breaking & mentioned_set)

    passed = not uncovered and not unknown and not missing_examples
    return {
        "passed": passed,
        "breaking_total": len(breaking),
        "covered": covered,
        "uncovered": uncovered,
        "unknown": unknown,
        "missing_examples": missing_examples,
    }


def format_report(result):
    lines = []
    if result["passed"]:
        lines.append(
            "PASS: %d/%d breaking changes covered, 0 unknown ids, 0 missing examples"
            % (len(result["covered"]), result["breaking_total"])
        )
        return "\n".join(lines) + "\n"
    lines.append("FAIL: migration notes do not cover the differ output")
    if result["uncovered"]:
        lines.append("uncovered: %s" % ", ".join(result["uncovered"]))
    else:
        lines.append("uncovered: (none)")
    if result["unknown"]:
        lines.append("unknown: %s" % ", ".join(result["unknown"]))
    else:
        lines.append("unknown: (none)")
    if result["missing_examples"]:
        lines.append("missing_examples: %s" % ", ".join(result["missing_examples"]))
    else:
        lines.append("missing_examples: (none)")
    lines.append(
        "covered %d/%d breaking changes"
        % (len(result["covered"]), result["breaking_total"])
    )
    return "\n".join(lines) + "\n"


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Check migration notes against an OpenAPI differ report.")
    parser.add_argument("notes", nargs="?", help="migration notes markdown")
    parser.add_argument("diff", nargs="?", help="oas_diff.py JSON output")
    parser.add_argument("--notes", dest="notes_flag", help="migration notes markdown")
    parser.add_argument("--diff", dest="diff_flag", help="oas_diff.py JSON output")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    notes_path = args.notes_flag or args.notes
    diff_path = args.diff_flag or args.diff
    if not notes_path or not diff_path:
        print("usage: check_notes.py NOTES.md DIFF.json", file=sys.stderr)
        return 2
    if not os.path.isfile(notes_path):
        print("file not found: %s" % notes_path, file=sys.stderr)
        return 2
    if not os.path.isfile(diff_path):
        print("file not found: %s" % diff_path, file=sys.stderr)
        return 2
    try:
        changes = load_diff(diff_path)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    with open(notes_path, encoding="utf-8") as handle:
        notes_text = handle.read()
    result = evaluate(notes_text, changes)
    if args.json:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(format_report(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
