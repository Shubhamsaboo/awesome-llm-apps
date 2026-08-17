#!/usr/bin/env python3
"""Structural analysis: lines/words/tokens, heading-level distribution, code-block languages, tables/links/images, incomplete markers, heading skips (Phase 1)."""

import re
import sys
from collections import Counter
from pathlib import Path

def read_text_safe(md_path):
    """Read a file, trying utf-8 first then common encodings; exit 2 on missing/binary."""
    p = Path(md_path)
    if not p.is_file():
        print(f"Error: file not found: {md_path}", file=sys.stderr)
        sys.exit(2)
    raw = p.read_bytes()
    if b"\x00" in raw:
        print(f"Error: binary file (contains NUL bytes): {md_path}", file=sys.stderr)
        sys.exit(2)
    for enc in ("utf-8", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    print(f"Error: cannot decode file: {md_path}", file=sys.stderr)
    sys.exit(2)

def analyze(md_path):
    text = read_text_safe(md_path)
    lines = text.splitlines()
    print(f"=== Structural Analysis: {md_path} ===")
    print(f"Lines: {len(lines)} | Words: {len(text.split())} | Est. tokens: ~{len(text) // 4}")

    heads = [(i + 1, l) for i, l in enumerate(lines) if l.startswith("#")]
    levels = Counter(len(re.match(r"^(#+)", h).group(1)) for _, h in heads)
    print(f"Heading levels: {dict(sorted(levels.items()))} | Total headings: {len(heads)}")

    langs = Counter(re.findall(r"^```(\w*)", text, re.M))
    print(f"Code-block languages: {dict(langs) if langs else 'none'}")

    tables = sum(1 for l in lines if l.strip().startswith("|"))
    links = len(re.findall(r"(?<!!)\[[^\]]+\]\([^)]+\)", text))  # (?<!!) excludes image syntax
    images = len(re.findall(r"!\[[^\]]*\]\([^)]+\)", text))
    print(f"Table rows: {tables} | Links: {links} | Images: {images}")

    todos = [l for l in lines if re.search(r"TODO|FIXME|HACK|TBD|WIP", l)]
    print(f"Incomplete markers (TODO/FIXME/HACK/TBD/WIP): {len(todos)}")

    skips = []
    prev = 0
    for num, h in heads:
        level = len(re.match(r"^(#+)", h).group(1))
        if prev and level > prev + 1:
            skips.append((num, h))
        prev = level
    print(f"Heading skips (affect TOC generation; flag in report): {len(skips)}")
    for num, h in skips[:5]:
        print(f"  L{num}: {h}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_structure.py <markdown-file>")
        sys.exit(1)
    analyze(sys.argv[1])
