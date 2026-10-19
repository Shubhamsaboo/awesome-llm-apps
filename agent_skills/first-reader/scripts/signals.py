#!/usr/bin/env python3
"""Measure the trust signals a draft pays, and what they cost the writer.

Readers judge credibility by costly signals: details that could be checked,
numbers that could be wrong, commitments that expose the writer. Free
signals (generic praise, safe hedges, uniform confidence) are worthless
precisely because they cost nothing. The accurate human detectors of AI
text (Russell et al. 2025) key on this layer, not on banned words.

These are measurements, not verdicts. A poem scores zero specifics and is
not worse for it; a launch post scoring zero specifics is a finding. The
skill decides what a number means for this genre; this script only counts.

Usage: python3 signals.py <draft> [--lang ja] [--json]
"""
import argparse
import json
import re
import statistics
import sys
from pathlib import Path

HEDGES = r"\b(might|may|could|perhaps|possibly|arguably|potentially|seems?|somewhat|likely|probably|tend(?:s)? to|in some cases|to some extent|it could be argued)\b"
CERTAINTY = r"\b(definitely|certainly|always|never|must|undeniably|clearly|obviously|of course|without a doubt)\b"
FIRST_PERSON = r"\b(I|I'm|I've|I'd|my|me|we|our)\b"
SECOND_PERSON = r"\b(you|your|you're|you've)\b"
ADMISSION = r"\b(I was wrong|we were wrong|I don't know|I'm not sure|didn't work|failed|my mistake|I missed|we missed|turned out I|I had to throw|embarrassing|uncomfortable|I still can't|was a fantasy|took us .{0,20} to notice|we broke|our fault)\b"


def clean(text):
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    return re.sub(r"^#{1,6}\s.*$", " ", text, flags=re.M)


def sentences(text, lang="en"):
    if lang in ("ja", "zh", "cjk"):
        # Split on Japanese/Chinese sentence terminators or English punctuation
        parts = re.split(r"(?<=[。！？.!?])\s*", clean(text).replace("\n", " "))
        return [s.strip() for s in parts if len(s.strip()) >= 5]
    else:
        parts = re.split(r"(?<=[.!?])\s+", clean(text).replace("\n", " "))
        return [s.strip() for s in parts if len(s.split()) >= 3]


def proper_nouns(text):
    # capitalized tokens not at sentence start: rough named-entity proxy
    hits = re.findall(r"(?<![.!?]\s)(?<!^)(?<!\n)\b([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*)\b", text)
    stop = {"I", "The", "A", "An", "But", "And", "It", "This", "That", "If", "So"}
    return [h for h in hits if h not in stop]


def main():
    parser = argparse.ArgumentParser(description="Measure trust signals in a draft.")
    parser.add_argument("file", help="Path to draft markdown or text file")
    parser.add_argument("--lang", default="en", help="Language code (e.g. 'en', 'ja', 'zh')")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    draft_path = Path(args.file)
    if not draft_path.exists():
        parser.error(f"File not found: {args.file}")

    text = draft_path.read_text(encoding="utf-8")
    lang = args.lang.lower()
    sents = sentences(text, lang=lang)
    if not sents:
        if args.json:
            print(json.dumps({"error": "No prose sentences found."}))
            return
        sys.exit("No prose sentences found.")

    is_cjk = lang in ("ja", "zh", "cjk")
    if is_cjk:
        lens = [len(s) for s in sents]
        unit = "chars"
        rate_key = "per100"
        numbers = re.findall(r"(?<![a-zA-Z0-9./-])(?:\$[\d,.]+[kKmMbB]?|\d+(?:[.,]\d+)*%?|\d{2,4})", clean(text))
        quotes = re.findall(r"[\"“「『]([^\"”」』]{5,200})[\"”」』]", text)
        tokens = list(re.sub(r"\s+", "", text.lower()))
    else:
        lens = [len(s.split()) for s in sents]
        unit = "words"
        rate_key = "per100w"
        # any token carrying a digit counts as a checkable specific: 4,100, $3M,
        # 90-second, v2.3, 48MB, 2:47am all expose the writer to being wrong
        numbers = re.findall(r"\b[\w$][\w.,:%$-]*\d[\w.,:%$-]*", clean(text))
        quotes = re.findall(r"[\"“]([^\"”]{10,200})[\"”]", text)
        tokens = re.findall(r"[a-zA-Z']+", text.lower())

    total_units = sum(lens)
    per100 = lambda n: round(n * 100 / max(total_units, 1), 2)

    hedged = [s for s in sents if re.search(HEDGES, s, re.I)]
    certain = [s for s in sents if re.search(CERTAINTY, s, re.I)]
    admissions = [s for s in sents if re.search(ADMISSION, s, re.I)]
    nouns = proper_nouns(clean(text))
    ttr = round(len(set(tokens)) / max(len(tokens), 1), 3)

    # portable sentences: no digit, no named entity, no first person: could
    # move unchanged into any other document on the topic
    portable = [s for s in sents
                if not re.search(r"\d", s)
                and not re.search(FIRST_PERSON, s)
                and not any(n in s for n in set(nouns))]

    # epistemic temperature: share of sentences carrying ANY marker of how
    # sure the writer is; near-zero variance in commitment is the machine tell
    marked = len(set(hedged) | set(certain))

    result = {
        unit: total_units,
        "sentences": len(sents),
        "sentence_len": {
            "mean": round(statistics.mean(lens), 1),
            "sd": round(statistics.pstdev(lens), 1),
            "burstiness": round(statistics.pstdev(lens) / max(statistics.mean(lens), 1), 2),
            "max": max(lens),
            "min": min(lens),
        },
        "costly": {
            "numbers": {"count": len(numbers), rate_key: per100(len(numbers)), "sample": numbers[:10]},
            "named_entities": {"count": len(nouns), rate_key: per100(len(nouns)), "sample": list(dict.fromkeys(nouns))[:10]},
            "direct_quotes": len(quotes),
            "admissions_against_interest": {"count": len(admissions), "sample": admissions[:3]},
            "first_person_sentences": sum(1 for s in sents if re.search(FIRST_PERSON, s)),
        },
        "free": {
            "hedged_sentences": {"count": len(hedged), "share": round(len(hedged) / len(sents), 2), "sample": hedged[:3]},
            "certainty_sentences": {"count": len(certain), "share": round(len(certain) / len(sents), 2)},
            "epistemically_marked_share": round(marked / len(sents), 2),
        },
        "portable_sentences": {
            "count": len(portable),
            "share": round(len(portable) / len(sents), 2),
            "sample": portable[:5],
        },
        "type_token_ratio": ttr,
    }
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    print("TRUST SIGNAL MEASUREMENTS (counts, not verdicts; genre decides meaning)")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("\nReading notes: costly signals expose the writer and buy trust; "
          "portable sentences fit any document and buy nothing. A piece where "
          "most sentences are portable and unmarked is committing to nothing.")


if __name__ == "__main__":
    main()