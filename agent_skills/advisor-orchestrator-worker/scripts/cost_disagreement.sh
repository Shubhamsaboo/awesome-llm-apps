#!/usr/bin/env bash
# cost_disagreement.sh — cost of each resolution path for Papa tie-breaks
# Usage:
#   calc --advisor-input N --advisor-output N --advisor-model ID \
#        --orchestrator-input N --orchestrator-output N --orchestrator-model ID
#   parse <flash-response-file>
# stdout: JSON; exit 2 on malformed
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PRICING="${COST_PRICING:-$SCRIPT_DIR/../references/pricing.json}"

die() { echo "cost_disagreement: $*" >&2; exit 2; }

calc_usd() {
  python3 - "$PRICING" "$1" "$2" "$3" <<'PY'
import json, sys
from decimal import Decimal, ROUND_HALF_UP
pricing_path, model, inp, out = sys.argv[1:5]
inp, out = int(inp), int(out)
with open(pricing_path) as f:
    data = json.load(f)
models = data["models"]
m = models.get(model) or models.get(data.get("fallback_model", "gemini-3.5-flash"))
usd = (
    Decimal(inp) * Decimal(str(m["input_per_million"])) / Decimal(1_000_000)
    + Decimal(out) * Decimal(str(m["output_per_million"])) / Decimal(1_000_000)
)
print(str(usd.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)))
PY
}

cmd_calc() {
  local ai="" ao="" am="" oi="" oo="" om=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --advisor-input) ai="$2"; shift 2 ;;
      --advisor-output) ao="$2"; shift 2 ;;
      --advisor-model) am="$2"; shift 2 ;;
      --orchestrator-input) oi="$2"; shift 2 ;;
      --orchestrator-output) oo="$2"; shift 2 ;;
      --orchestrator-model) om="$2"; shift 2 ;;
      *) die "unknown calc arg: $1" ;;
    esac
  done
  [ -f "$PRICING" ] || die "pricing file not found: $PRICING"
  for v in ai ao am oi oo om; do
    [ -n "${!v}" ] || die "calc requires all --advisor-* and --orchestrator-* args"
  done
  local ausd ousd
  ausd=$(calc_usd "$am" "$ai" "$ao")
  ousd=$(calc_usd "$om" "$oi" "$oo")
  python3 - "$ausd" "$ousd" <<'PY'
import json, sys
from decimal import Decimal
a, o = Decimal(sys.argv[1]), Decimal(sys.argv[2])
delta = a - o
cheaper = "orchestrator" if o <= a else "advisor"
print(json.dumps({
    "advisor_path_usd": float(a),
    "orchestrator_path_usd": float(o),
    "delta_usd": float(delta.quantize(Decimal("0.0001"))),
    "cheaper_route": cheaper,
}, separators=(",", ":")))
PY
}

cmd_parse() {
  [ $# -eq 1 ] || die "usage: $0 parse <response-file>"
  [ -f "$1" ] || die "file not found: $1"
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
    print(f"cost_disagreement: invalid JSON: {e}", file=sys.stderr)
    sys.exit(2)
required = ("advisor_path_usd", "orchestrator_path_usd", "delta_usd", "cheaper_route")
missing = [k for k in required if k not in data]
if missing:
    print(f"cost_disagreement: missing keys: {', '.join(missing)}", file=sys.stderr)
    sys.exit(2)
if data["cheaper_route"] not in ("advisor", "orchestrator"):
    print("cost_disagreement: cheaper_route must be advisor|orchestrator", file=sys.stderr)
    sys.exit(2)
print(json.dumps(data, separators=(",", ":")))
PY
}

cmd="${1:-}"
shift || true
case "$cmd" in
  calc) cmd_calc "$@" ;;
  parse) cmd_parse "$@" ;;
  *)
    echo "usage: $0 calc --advisor-input N --advisor-output N --advisor-model ID \\" >&2
    echo "            --orchestrator-input N --orchestrator-output N --orchestrator-model ID" >&2
    echo "       $0 parse <response-file>" >&2
    exit 2
    ;;
esac
