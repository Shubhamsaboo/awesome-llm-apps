#!/usr/bin/env bash
# cost_tracker.sh — runtime spend tracker for advisor-orchestrator-worker
# Requires: jq, python3. Pricing from references/pricing.json (COST_PRICING).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PRICING="${COST_PRICING:-$SCRIPT_DIR/../references/pricing.json}"
TRACKER="${COST_TRACKER:-}"

die() { echo "cost_tracker: $*" >&2; exit 2; }

require_tracker() {
  [ -n "$TRACKER" ] && [ -f "$TRACKER" ] || die "COST_TRACKER not set or missing; run init first"
}

require_pricing() {
  [ -f "$PRICING" ] || die "pricing file not found: $PRICING"
}

calc_usd() {
  local model="$1" inp="$2" out="$3"
  python3 - "$PRICING" "$model" "$inp" "$out" <<'PY'
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

cmd_init() {
  local approved="" estimated=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --approved-usd) approved="$2"; shift 2 ;;
      --estimated-usd) estimated="$2"; shift 2 ;;
      *) die "unknown init arg: $1" ;;
    esac
  done
  [ -n "$approved" ] || die "init requires --approved-usd"
  require_pricing
  if [ -z "$TRACKER" ]; then
    TRACKER=$(mktemp)
    export COST_TRACKER="$TRACKER"
  fi
  jq -n \
    --arg approved "$approved" \
    --arg estimated "${estimated:-$approved}" \
    '{approved_usd: $approved, estimated_usd: $estimated,
      total_input_tokens: 0, total_output_tokens: 0, total_usd: "0.0000",
      records: []}' > "$TRACKER"
  echo "$TRACKER"
}

cmd_record() {
  local tier="" inp="" out="" model=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --tier) tier="$2"; shift 2 ;;
      --input) inp="$2"; shift 2 ;;
      --output) out="$2"; shift 2 ;;
      --model) model="$2"; shift 2 ;;
      *) die "unknown record arg: $1" ;;
    esac
  done
  require_tracker
  require_pricing
  case "$tier" in
    worker|papa|advisor|estimator) ;;
    *) die "tier must be worker|papa|advisor|estimator" ;;
  esac
  [ -n "$inp" ] && [ -n "$out" ] && [ -n "$model" ] || die "record requires --input --output --model"
  local usd
  usd=$(calc_usd "$model" "$inp" "$out")
  local tmp
  tmp=$(mktemp)
  jq \
    --arg tier "$tier" \
    --argjson input "$inp" \
    --argjson output "$out" \
    --arg model "$model" \
    --arg usd "$usd" \
    '.total_input_tokens += $input
     | .total_output_tokens += $output
     | .total_usd = (
         ((.total_usd | tonumber) + ($usd | tonumber)) | tostring
       )
     | .records += [{tier: $tier, input: $input, output: $output, model: $model, usd: $usd}]' \
    "$TRACKER" > "$tmp" && mv "$tmp" "$TRACKER"
}

cmd_status() {
  require_tracker
  python3 - "$TRACKER" <<'PY'
import json, sys
from decimal import Decimal
t = json.load(open(sys.argv[1]))
actual = Decimal(t["total_usd"])
approved = Decimal(t["approved_usd"])
estimated = Decimal(t["estimated_usd"])
pct = (actual / estimated * 100) if estimated > 0 else Decimal(0)
remaining = approved - actual
print(
    "COST: $%s / $%s approved | %.0f%% of estimate | %dk in / %dk out"
    % (
        actual.quantize(Decimal("0.01")),
        approved.quantize(Decimal("0.01")),
        float(pct),
        t["total_input_tokens"] // 1000,
        t["total_output_tokens"] // 1000,
    )
)
if remaining < 0:
    print("OVER BUDGET by $%s" % (-remaining).quantize(Decimal("0.01")))
PY
}

cmd_check() {
  require_tracker
  python3 - "$TRACKER" <<'PY'
import json, sys
from decimal import Decimal
t = json.load(open(sys.argv[1]))
if Decimal(t["total_usd"]) > Decimal(t["approved_usd"]):
    sys.exit(2)
PY
}

cmd="${1:-}"
shift || true
case "$cmd" in
  init) cmd_init "$@" ;;
  record) cmd_record "$@" ;;
  status) cmd_status ;;
  check) cmd_check ;;
  *)
    echo "usage: COST_TRACKER=<file> COST_PRICING=<pricing.json> $0 init --approved-usd N [--estimated-usd N]" >&2
    echo "       $0 record --tier worker|papa|advisor|estimator --input N --output N --model ID" >&2
    echo "       $0 status | check" >&2
    exit 2
    ;;
esac
