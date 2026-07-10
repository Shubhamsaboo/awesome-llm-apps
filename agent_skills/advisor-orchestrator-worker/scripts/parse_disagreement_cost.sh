#!/usr/bin/env bash
# parse_disagreement_cost.sh — validate disagreement cost JSON for Papa briefs
# Usage: scripts/parse_disagreement_cost.sh <response-file>
set -euo pipefail

[ $# -eq 1 ] || { echo "usage: $0 <response-file>" >&2; exit 2; }
[ -f "$1" ] || { echo "parse_disagreement_cost: file not found: $1" >&2; exit 2; }

python3 - "$1" <<'PY'
import json, re, sys
from decimal import Decimal

text = open(sys.argv[1]).read().strip()
m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
if m:
    text = m.group(1).strip()
try:
    data = json.loads(text)
except json.JSONDecodeError as e:
    print(f"parse_disagreement_cost: invalid JSON: {e}", file=sys.stderr)
    sys.exit(2)

for side in ("orchestrator_path", "advisor_path"):
    if side not in data:
        print(f"parse_disagreement_cost: missing {side}", file=sys.stderr)
        sys.exit(2)
    p = data[side]
    for k in ("estimated_usd", "summary"):
        if k not in p:
            print(f"parse_disagreement_cost: {side} missing {k}", file=sys.stderr)
            sys.exit(2)

if "delta_usd" not in data or "cost_note" not in data:
    print("parse_disagreement_cost: missing delta_usd or cost_note", file=sys.stderr)
    sys.exit(2)

print(json.dumps(data, separators=(",", ":")))
PY
