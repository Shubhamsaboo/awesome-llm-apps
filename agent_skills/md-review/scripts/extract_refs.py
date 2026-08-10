#!/usr/bin/env python3
"""Extract and classify all reference links in a Markdown document (target existence is verified manually by the reviewer)."""

import re
import sys
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

def extract_refs(md_path):
    content = read_text_safe(md_path)

    # Extract [text](url) links ((?<!!) excludes ![alt](path) image syntax to avoid double counting)
    links = re.findall(r'(?<!!)\[([^\]]+)\]\(([^)]+)\)', content)

    # Extract ![alt](path) images
    images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)

    # Extract <url> bare links
    bare_urls = re.findall(r'<(https?://[^>]+)>', content)

    print("=== Markdown Reference Extraction ===")
    print(f"Document: {md_path}")
    print(f"Text links: {len(links)}")
    print(f"Image references: {len(images)}")
    print(f"Bare URLs: {len(bare_urls)}")
    print()

    all_refs = []

    for text, url in links:
        all_refs.append({"type": "link", "text": text, "url": url})

    for alt, path in images:
        all_refs.append({"type": "image", "text": alt, "url": path})

    for url in bare_urls:
        all_refs.append({"type": "bare_url", "text": url, "url": url})

    # Classify output
    internal = [r for r in all_refs if not r["url"].startswith(('http://', 'https://'))]
    external = [r for r in all_refs if r["url"].startswith(('http://', 'https://'))]

    if internal:
        print("--- Internal References ---")
        for r in internal:
            print(f"  [{r['type']}] {r['text'][:30]}... -> {r['url']}")

    if external:
        print("--- External References ---")
        for r in external:
            print(f"  [{r['type']}] {r['text'][:30]}... -> {r['url']}")

    # Check for suspicious references
    suspicious = []
    for r in all_refs:
        url = r["url"]
        if url.startswith('http://'):
            suspicious.append((r, "Insecure HTTP protocol"))
        elif url == '#' or url == '':
            suspicious.append((r, "Empty link or placeholder"))
        elif url.startswith('http') and 'localhost' in url:
            suspicious.append((r, "Link contains localhost"))

    if suspicious:
        print()
        print("--- Suspicious References ---")
        for r, reason in suspicious:
            print(f"  ⚠️ {reason}: {r['url']}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 extract_refs.py <markdown-file>")
        sys.exit(1)
    extract_refs(sys.argv[1])
