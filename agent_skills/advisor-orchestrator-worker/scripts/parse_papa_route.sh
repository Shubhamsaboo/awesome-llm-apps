#!/usr/bin/env bash
# parse_papa_route.sh — parse Papa routing response
# Usage: scripts/parse_papa_route.sh <response-file>
# stdout: ROUTE=... and REASON=... lines; exit 2 on malformed
set -euo pipefail

[ $# -eq 1 ] || { echo "usage: $0 <response-file>" >&2; exit 2; }
[ -f "$1" ] || { echo "parse_papa_route: file not found: $1" >&2; exit 2; }

python3 - "$1" <<'PY'
import re, sys

text = open(sys.argv[1]).read()
route_m = re.search(r"ROUTE:\s*(advisor|orchestrator)\s*", text, re.I)
reason_m = re.search(r"REASON:\s*(.+)", text, re.I)
if not route_m or not reason_m:
    print("parse_papa_route: need ROUTE and REASON lines", file=sys.stderr)
    sys.exit(2)
route = route_m.group(1).lower()
reason = reason_m.group(1).strip()
if route not in ("advisor", "orchestrator"):
    print(f"parse_papa_route: invalid route: {route}", file=sys.stderr)
    sys.exit(2)
print(f"ROUTE: {route}")
print(f"REASON: {reason}")
PY
