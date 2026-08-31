#!/usr/bin/env python3
"""doc-authenticity-checker — forensic authenticity signals for any PDF/image.

Anonymous free tier works immediately; add STIPPLE_API_KEY for your own metering.

  python agent.py https://example.com/payslip.pdf
  python agent.py path/to/id-scan.png --deep
  python agent.py --smoke
"""
import argparse
import json
from stipple import Stipple, StippleError

BANDS = {
    "low":    "Nothing looks tampered. (Low coverage is not risk — read inspection_quality.)",
    "medium": "Some signals worth a human look.",
    "high":   "Multiple tamper signals. Do not rely on this document without further checks.",
    "unknown": "Could not determine — see evidence.",
}


def main():
    ap = argparse.ArgumentParser(description="Verify a document's authenticity (risk_band + evidence).")
    ap.add_argument("source", nargs="?", default=None, help="URL, local file path, or - for stdin base64")
    ap.add_argument("--deep", action="store_true", help="deep inspection (10 credits vs 2)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    st = Stipple()
    if args.smoke:
        p = st.pricing()
        assert "verify_document" in p["costs"]
        print(f"smoke ok: verify_document priced at {p['costs']['verify_document']} credits")
        return

    src = args.source
    try:
        w = st.verify_document(url=src) if src.lower().startswith(("http://", "https://")) \
            else st.verify_document(file_path=src)
    except FileNotFoundError:
        raise SystemExit(f"file not found: {src}")
    except StippleError as e:
        raise SystemExit(str(e))

    if args.json:
        print(json.dumps(w, indent=2, ensure_ascii=False))
        return

    band = w.get("risk_band", "unknown")
    quality = w.get("inspection_quality", "?")
    print(f"risk_band:           {band.upper()} — {BANDS.get(band, '')}")
    print(f"inspection_quality:  {quality}")
    if quality in ("limited", "poor"):
        print("  (couldn't inspect everything — low coverage is NOT a fraud signal)")
    if w.get("recommended_action"):
        print(f"recommended action:  {w['recommended_action']}")
    if w.get("summary"):
        print(f"\nsummary: {w['summary']}")
    ev = w.get("signals") or []
    if ev:
        print("\nevidence (signals):")
        for e in ev[:8]:
            print(f"  - [{e.get('status', '?')}] {e.get('title', e.get('signal_id', '?'))}: "
                  f"{e.get('summary', '')[:120]}")
    wid = w.get("warrant_id")
    if wid:
        print(f"\nwarrant: {wid}  (re-check the same file later → cached, free)")
    print("\nThis is a signal, not a verdict — the evidence is the product.")
    print("Powered by Stipple — https://www.stipple.sh/?utm_source=stipple-kits")


if __name__ == "__main__":
    main()
