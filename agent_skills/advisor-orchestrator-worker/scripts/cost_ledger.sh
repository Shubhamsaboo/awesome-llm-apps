#!/usr/bin/env bash
# cost_ledger.sh — deterministic spend gate for advisor-orchestrator-worker
# Stdlib: jq required. No network. Persists counts in $COST_LEDGER (JSON).
set -euo pipefail

ledger="${COST_LEDGER:-}"

die() { echo "cost_ledger: $*" >&2; exit 2; }

require_ledger() {
  [ -n "$ledger" ] && [ -f "$ledger" ] || die "COST_LEDGER not set or missing; run init first"
}

init_ledger() {
  local workers=0 papa=0 consults=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --workers) workers="$2"; shift 2 ;;
      --papa) papa="$2"; shift 2 ;;
      --consults) consults="$2"; shift 2 ;;
      *) die "unknown init arg: $1" ;;
    esac
  done
  [ "$workers" -gt 0 ] || die "--workers must be > 0"
  [ "$papa" -gt 0 ] || die "--papa must be > 0"
  [ "$consults" -gt 0 ] || die "--consults must be > 0"
  if [ -z "$ledger" ]; then
    ledger=$(mktemp)
    export COST_LEDGER="$ledger"
  fi
  jq -n \
    --argjson w "$workers" --argjson p "$papa" --argjson c "$consults" \
    '{workers:{max:$w,used:0},papa:{max:$p,used:0},consults:{max:$c,used:0}}' \
    > "$ledger"
  echo "$ledger"
}

checkpoint() {
  local kind="${1:-}"
  require_ledger
  local key
  case "$kind" in
    worker) key="workers" ;;
    papa) key="papa" ;;
    consult) key="consults" ;;
    *) die "checkpoint kind must be worker|papa|consult" ;;
  esac
  local used max
  used=$(jq -r ".${key}.used" "$ledger")
  max=$(jq -r ".${key}.max" "$ledger")
  if [ "$used" -ge "$max" ]; then
    echo "REFUSED: ${kind} budget exhausted (${used}/${max})" >&2
    exit 2
  fi
  jq ".${key}.used += 1" "$ledger" > "${ledger}.tmp" && mv "${ledger}.tmp" "$ledger"
}

status_cmd() {
  require_ledger
  local wu wm pu pm cu cm
  wu=$(jq -r '.workers.used' "$ledger")
  wm=$(jq -r '.workers.max' "$ledger")
  pu=$(jq -r '.papa.used' "$ledger")
  pm=$(jq -r '.papa.max' "$ledger")
  cu=$(jq -r '.consults.used' "$ledger")
  cm=$(jq -r '.consults.max' "$ledger")
  echo "COST: workers ${wu}/${wm} | papa ${pu}/${pm} | consults ${cu}/${cm}"
}

cmd="${1:-}"
shift || true
case "$cmd" in
  init) init_ledger "$@" ;;
  checkpoint) checkpoint "$@" ;;
  status) status_cmd ;;
  *)
    echo "usage: COST_LEDGER=<file> $0 init --workers N --papa N --consults N" >&2
    echo "       $0 checkpoint worker|papa|consult" >&2
    echo "       $0 status" >&2
    exit 2
    ;;
esac
