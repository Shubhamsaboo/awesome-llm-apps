#!/usr/bin/env python3
"""ai-text-detector — probability a document's prose is AI-written, with the linguistic tells.

  python agent.py https://example.com/essay.pdf
  python agent.py ./submission.docx
  python agent.py --text "It is important to note that, in today's fast-paced world, ..."
  python agent.py --smoke
"""
import argparse
import json
from stipple import Stipple, StippleError


def main():
    ap = argparse.ArgumentParser(description="Detect AI-written prose (probability + linguistic tells).")
    ap.add_argument("source", nargs="?", default=None, help="URL or local file path")
    ap.add_argument("--text", default=None, help="check raw text instead of a document")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    st = Stipple()
    if args.smoke:
        p = st.pricing()
        assert "detect_ai_text" in p["costs"]
        print(f"smoke ok: detect_ai_text priced at {p['costs']['detect_ai_text']} credit")
        return

    if not args.source and not args.text:
        ap.error("give a document URL/path, or --text \"...\"")

    try:
        if args.text is not None:
            out = st.detect_ai_text(text=args.text)
        elif args.source.lower().startswith(("http://", "https://")):
            out = st.detect_ai_text(url=args.source)
        else:
            out = st.detect_ai_text(file_path=args.source)
    except FileNotFoundError:
        raise SystemExit(f"file not found: {args.source}")
    except StippleError as e:
        raise SystemExit(str(e))

    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    if out.get("applicable") is False:
        print("abstained: this document is not prose (scans, forms, spreadsheets) — "
              "detection is deliberately refused rather than guessed.")
        return

    prob = out.get("probability", out.get("ai_probability", "?"))
    print(f"AI-written probability: {prob}  (lean: {out.get('lean', '?')})")
    if out.get("prose_ratio") is not None:
        print(f"prose ratio: {out['prose_ratio']}")
    tells = out.get("tells") or []
    if tells:
        print("\nlinguistic tells:")
        for t in tells[:8]:
            print(f"  - {t if isinstance(t, str) else json.dumps(t)}")
    if out.get("reasoning"):
        print(f"\nreasoning: {out['reasoning'][:300]}")
    if out.get("limitations"):
        print(f"\nlimitations: {out['limitations'][:300]}")

    print("\nThis measures style, not authenticity — a human can write generically, "
          "and an AI can write plainly. Treat as one signal alongside review.")
    print("Powered by Stipple — https://www.stipple.sh/?utm_source=stipple-kits")


if __name__ == "__main__":
    main()
