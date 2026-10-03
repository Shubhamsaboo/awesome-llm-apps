
"""Produce the scanner's view of a draft: what a skimming reader actually
fixates on, and nothing else.

Eyetracking work (Nielsen Norman Group) shows scanners fixate on headings,
the first words of lines and paragraphs, bold spans, numbers, and links,
and skip nearly everything else. This prints exactly that view so a fresh
reader agent can answer the only question a scanner answers: what is this,
and do I commit? Feeding the full text would break the experiment, so this
script deliberately truncates.

Usage: 
    python3 skim.py <draft.md|draft.txt> [--lang ja]
"""
import argparse
import re
from pathlib import Path

# Reading speeds:
# English: ~238 words per minute (Brysbaert 2019)
# Japanese/Chinese (CJK): ~500 characters per minute
WPM_EN = 238
CPM_CJK = 500

MOBILE_CHARS_PER_LINE = 38
MOBILE_LINES_PER_SCREEN = 14
FIRST_WORDS = 9
FIRST_CHARS_CJK = 30


def paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def first_sentence(p, lang="en"):
    if lang in ("ja", "zh", "cjk"):
        # Match up to Japanese/Chinese sentence terminators (。！？) or English (.!?)
        m = re.match(r".+?[。！？.!?](?=\s|$)", p, re.S)
    else:
        m = re.match(r".+?[.!?](?=\s|$)", p, re.S)
    return (m.group(0) if m else p).replace("\n", " ")


def first_words(p, n=FIRST_WORDS, lang="en"):
    if lang in ("ja", "zh", "cjk"):
        # CJK text does not use spaces, so truncate by character count
        clean = p.replace("\n", " ").strip()
        if len(clean) <= FIRST_CHARS_CJK:
            return clean
        return clean[:FIRST_CHARS_CJK] + " ..."
    
    # Default English / space-separated words
    words = p.replace("\n", " ").split()
    if len(words) <= n:
        return " ".join(words)
    return " ".join(words[:n]) + " ..."


def calculate_stats(text, lang="en"):
    """Calculate volume and reading time according to language."""
    if lang in ("ja", "zh", "cjk"):
        chars = len(re.sub(r"\s+", "", text))
        read_time = max(1, round(chars / CPM_CJK))
        return f"{chars} chars | ~{read_time} min full read"
    else:
        words = len(text.split())
        read_time = max(1, round(words / WPM_EN))
        return f"{words} words | ~{read_time} min full read"


def main():
    parser = argparse.ArgumentParser(description="Produce scanner view of a draft.")
    parser.add_argument("file", help="Path to draft markdown or text file")
    parser.add_argument("--lang", default="en", help="Language code (e.g. 'en', 'ja', 'zh')")
    args = parser.parse_args()

    draft_path = Path(args.file)
    if not draft_path.exists():
        parser.error(f"File not found: {args.file}")

    text = draft_path.read_text(encoding="utf-8")
    lang = args.lang.lower()
    paras = paragraphs(text)
    
    bold = re.findall(r"\*\*(.+?)\*\*|__(.+?)__", text)
    bold = [a or b for a, b in bold]
    links = re.findall(r"\[([^\]]+)\]\(", text)
    numbers = re.findall(
    r"(?<![a-zA-Z0-9./-])(?:\$[\d,.]+[kKmMbB]?|\d+(?:[.,]\d+)*%?|\d{2,4})", text
)
    
    screens = max(1, round(len(text) / (MOBILE_CHARS_PER_LINE * MOBILE_LINES_PER_SCREEN)))

    print("SCANNER VIEW (what a skimming reader fixates on; the full text is withheld)")
    print(f"stats: {calculate_stats(text, lang)} | ~{screens} phone screens")
    print(f"fixation tokens: numbers={numbers[:20] if numbers else 'NONE'}")
    if bold:
        print(f"bold spans: {[b[:60] for b in bold[:12]]}")
    if links:
        print(f"link texts: {links[:12]}")
    print("-" * 60)
    body_count = 0
    for p in paras:
        if re.match(r"#{1,6}\s", p):
            print(p.splitlines()[0])
            continue
        if p.startswith(("- ", "* ", "1.", "> ")):
            for line in p.splitlines()[:6]:
                print("  " + first_words(line.lstrip("->*1234567890. "), lang=lang))
            continue
        body_count += 1
        if body_count <= 2:
            print(first_sentence(p, lang=lang))
        else:
            print(first_words(p, lang=lang))
    print("-" * 60)
    print(
        "Question for the reader: from this view alone, say (1) what you think "
        "this piece is and what it will argue, (2) whether your cast persona "
        "commits to a full read or moves on, and (3) the single element above "
        "that decided it."
    )


if __name__ == "__main__":
    main()