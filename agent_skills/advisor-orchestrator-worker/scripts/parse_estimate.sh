#!/usr/bin/env bash
# parse_estimate.sh — validate cost estimator JSON from Flash response text
# Usage: scripts/parse_estimate.sh <response-file>
# stdout: compact JSON; exit 2 on malformed
set -euo pipefail

[ $# -eq 1 ] || { echo "usage: $0 <response-file>" >&2; exit 2; }
[ -f "$1" ] || { echo "parse_estimate: file not found: $1" >&2; exit 2; }

python3 - "$1" <<'PY'
import json, re, sys

text = open(sys.argv[1]).read().strip()
# strip optional markdown fences
m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
if m:
    text = m.group(1).strip()
try:
    data = json.loads(text)
except json.JSONDecodeError as e:
    print(f"parse_estimate: invalid JSON: {e}", file=sys.stderr)
    sys.exit(2)
required = ("estimated_usd", "breakdown", "worth_it", "recommendation")
missing = [k for k in required if k not in data]
if missing:
    print(f"parse_estimate: missing keys: {', '.join(missing)}", file=sys.stderr)
    sys.exit(2)
if not isinstance(data["breakdown"], list):
    print("parse_estimate: breakdown must be a list", file=sys.stderr)
    sys.exit(2)
if "optimizations" in data and not isinstance(data["optimizations"], list):
    print("parse_estimate: optimizations must be a list", file=sys.stderr)
    sys.exit(2)
print(json.dumps(data, separators=(",", ":")))
PY
