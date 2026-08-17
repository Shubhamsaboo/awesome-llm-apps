#!/usr/bin/env python3
"""Weighted scoring: overall = Σ(dimension×weight), 0-100 validation, grade and risk (Phase 4 report).

Usage: python3 score.py <d1> <d2> <d3> <d4> <d5> <d6> [--p0 N]
Weights: Logic 30% / Scenario completeness 25% / Sections 15% / References 10% / Redundancy 10% / Format 10%
--p0 N: P0 (bug-level) issue count, used for the risk level (default 0).
"""

import sys

WEIGHTS = [0.30, 0.25, 0.15, 0.10, 0.10, 0.10]
NAMES = ["Logic (bug detection)", "Scenario completeness", "Sections", "References", "Redundancy", "Format"]

def risk_level(total, p0):
    if total >= 80 and p0 == 0:
        return "Low"
    if total >= 60:
        return "Medium"
    if total >= 40:
        return "High"
    return "Critical"

def score(scores, p0):
    if len(scores) != 6:
        print(f"Error: expected 6 dimension scores, got {len(scores)}", file=sys.stderr)
        sys.exit(2)
    for s in scores:
        if not (0 <= s <= 100):
            print(f"Error: score {s} out of 0-100 range", file=sys.stderr)
            sys.exit(2)
    print("=== Weighted Score ===")
    total = 0.0
    for n, w, s in zip(NAMES, WEIGHTS, scores):
        wv = s * w
        total += wv
        print(f"  {n}: {s:.0f} x {w:.0%} = {wv:.1f}")
    print(f"  Overall: {total:.1f}/100")
    if total >= 90:
        grade, action = "Excellent", "Ready to publish; minor polish only"
    elif total >= 75:
        grade, action = "Good", "Fix P0/P1, then publish"
    elif total >= 60:
        grade, action = "Passing", "Must fix P0 (bug-level) before re-review"
    else:
        grade, action = "Failing", "Rewrite or restructure recommended"
    print(f"  Grade: {grade} | Risk: {risk_level(total, p0)}")
    print(f"  Action: {action}")

if __name__ == "__main__":
    args = sys.argv[1:]
    p0 = 0
    if "--p0" in args:
        i = args.index("--p0")
        try:
            p0 = int(args[i + 1])
        except (IndexError, ValueError):
            print("Error: --p0 requires an integer argument", file=sys.stderr)
            sys.exit(2)
        del args[i:i + 2]
    if len(args) < 6:
        print("Usage: python3 score.py <d1> <d2> <d3> <d4> <d5> <d6> [--p0 N]")
        sys.exit(1)
    try:
        scores = [float(a) for a in args[:6]]
    except ValueError:
        print("Error: arguments must be numbers", file=sys.stderr)
        sys.exit(2)
    score(scores, p0)
