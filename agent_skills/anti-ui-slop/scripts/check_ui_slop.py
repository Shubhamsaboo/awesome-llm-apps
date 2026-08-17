#!/usr/bin/env python3
"""Deterministic, local-first source checks for common UI quality risks.

This is a triage tool, not a design judge. It reads supported frontend source
files and emits stable findings that an agent or developer can review.
"""

import argparse
import json
import re
import sys
from pathlib import Path


SUPPORTED = {".css", ".html", ".jsx", ".scss", ".tsx", ".vue"}
GENERIC_COPY = re.compile(
    r"\b(?:click here|lorem ipsum|welcome to our platform|learn more|"
    r"your journey starts here|unlock your potential|seamless experience)\b",
    re.IGNORECASE,
)
BUTTON = re.compile(r"<button\b[^>]*>(.*?)</button\s*>", re.IGNORECASE | re.DOTALL)
IMAGE = re.compile(r"<img\b([^>]*)>", re.IGNORECASE | re.DOTALL)
FORM = re.compile(r"<form\b[^>]*>|\b(?:input|textarea|select)\b", re.IGNORECASE)
STATE_WORDS = re.compile(
    r"\b(?:error|invalid|success|successful|loading|disabled|empty|permission|"
    r"unauthorized|retry|try again)\b",
    re.IGNORECASE,
)
RAW_COLOR = re.compile(r"(?<![\w-])#[0-9a-fA-F]{3,8}\b")
ACTION_HOOK = re.compile(
    r"\b(?:onClick|onSubmit|onChange|data-action|aria-controls|form=|"
    r"type\s*=\s*['\"]submit['\"]|href\s*=)\b",
    re.IGNORECASE,
)


def line_number(text, offset):
    return text.count("\n", 0, offset) + 1


def finding(rule, severity, path, line, message):
    return {
        "rule": rule,
        "severity": severity,
        "file": str(path),
        "line": line,
        "message": message,
    }


def source_files(paths):
    for raw in paths:
        path = Path(raw)
        if path.is_file() and path.suffix.lower() in SUPPORTED:
            yield path
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and child.suffix.lower() in SUPPORTED:
                    yield child


def scan(path):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [finding("read-error", "error", path, 1, str(exc))]

    findings = []
    for match in GENERIC_COPY.finditer(text):
        value = match.group(0)
        findings.append(
            finding(
                "generic-copy",
                "warning",
                path,
                line_number(text, match.start()),
                "placeholder copy: %r" % value,
            )
        )

    for match in BUTTON.finditer(text):
        opening_end = text.find(">", match.start())
        opening = text[match.start() : opening_end + 1] if opening_end >= 0 else ""
        content = match.group(1).strip()
        if not ACTION_HOOK.search(opening) and not ACTION_HOOK.search(content):
            findings.append(
                finding(
                    "inert-control",
                    "warning",
                    path,
                    line_number(text, match.start()),
                    "button has no visible source-level action hook",
                )
            )

    for match in IMAGE.finditer(text):
        attrs = match.group(1)
        if not re.search(r"\balt\s*=", attrs, re.IGNORECASE):
            findings.append(
                finding(
                    "image-alt",
                    "error",
                    path,
                    line_number(text, match.start()),
                    "image is missing alt text",
                )
            )

    if FORM.search(text) and not STATE_WORDS.search(text):
        findings.append(
            finding(
                "missing-state",
                "warning",
                path,
                1,
                "form or field has no visible loading, empty, error, success, or disabled state",
            )
        )

    if path.suffix.lower() in {".css", ".scss"}:
        colors = {}
        for match in RAW_COLOR.finditer(text):
            colors[match.group(0).lower()] = colors.get(match.group(0).lower(), 0) + 1
        for color, count in sorted(colors.items()):
            if count >= 2:
                findings.append(
                    finding(
                        "token-drift",
                        "warning",
                        path,
                        line_number(text, text.lower().find(color)),
                        "raw color %s appears %d times; check for a shared design token" % (color, count),
                    )
                )

    return findings


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", action="append", required=True, help="File or directory to scan; repeatable")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--fail-on", choices=("error", "warning", "never"), default="error")
    return parser.parse_args()


def main():
    args = parse_args()
    files = list(source_files(args.path))
    findings = []
    for path in files:
        findings.extend(scan(path))

    if args.format == "json":
        print(json.dumps({"files": len(files), "findings": findings}, indent=2, sort_keys=True))
    else:
        for item in findings:
            print(
                "%s %s %s:%d — %s"
                % (item["severity"].upper(), item["rule"], item["file"], item["line"], item["message"])
            )
        errors = sum(item["severity"] == "error" for item in findings)
        warnings = sum(item["severity"] == "warning" for item in findings)
        print("\n%d finding(s): %d error(s), %d warning(s)" % (len(findings), errors, warnings))

    if args.fail_on == "never":
        return 0
    threshold = {"error": {"error"}, "warning": {"error", "warning"}}[args.fail_on]
    return 1 if any(item["severity"] in threshold for item in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
