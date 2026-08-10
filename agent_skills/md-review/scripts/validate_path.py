#!/usr/bin/env python3
"""Validate that the path argument is a single Markdown (*.md) document.

This is the argument gate for the skill: run it FIRST (SKILL.md Phase 0) before
any probing or review. It rejects directories, missing files, non-*.md files,
and binary/undecodable content.

Exit codes (solo protocol): 0 = valid single *.md file; 2 = error
(missing file, directory target, non-*.md extension, binary/undecodable).
Usage: python3 validate_path.py <path>
"""

import sys
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 validate_path.py <path>", file=sys.stderr)
        sys.exit(2)
    p = Path(sys.argv[1])

    if not p.is_file():
        kind = "directory" if p.is_dir() else "missing"
        print(f"Error: {kind} target — expected a single Markdown (*.md) file: {p}", file=sys.stderr)
        sys.exit(2)

    if p.suffix.lower() != ".md":
        print(f"Error: not a *.md file (got extension '{p.suffix}'): {p}", file=sys.stderr)
        sys.exit(2)

    raw = p.read_bytes()
    if b"\x00" in raw:
        print(f"Error: binary file (contains NUL bytes): {p}", file=sys.stderr)
        sys.exit(2)

    for enc in ("utf-8", "latin-1"):
        try:
            raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        print(f"Error: cannot decode file: {p}", file=sys.stderr)
        sys.exit(2)

    print(f"OK: single Markdown document: {p}")
    sys.exit(0)


if __name__ == "__main__":
    main()
