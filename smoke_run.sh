#!/usr/bin/env bash
# smoke_run.sh — local + live smoke for advisor-orchestrator-worker v1.1
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SKILL="$ROOT/advisor-orchestrator-worker"
EVALS="$ROOT/evals/advisor-orchestrator-worker"
export PAPA_MODEL="${PAPA_MODEL:-gemini-3.1-pro-preview}"
export ESTIMATOR_MODEL="${ESTIMATOR_MODEL:-gemini-3.1-flash-lite}"
export COST_PRICING="$SKILL/references/pricing.json"

pass() { echo "PASS  $*"; }
fail() { echo "FAIL  $*" >&2; exit 1; }
section() { echo ""; echo "=== $* ==="; }

section "CI gate (6 commands)"
python3 "$ROOT/evals/tools/skill_lint.py" "$SKILL" --strict
python3 "$ROOT/evals/tools/run_trigger_evals.py"
python3 "$ROOT/evals/tools/skill_scanner.py" "$SKILL"
python3 "$EVALS/test_cost_tracker.py"
python3 "$EVALS/test_parse_estimate.py"
python3 "$EVALS/test_parse_papa_route.py"
pass "all CI commands green"

section "Scenario 4 — over-target advisory (non-blocking)"
export COST_TRACKER
COST_TRACKER=$(mktemp)
"$SKILL/scripts/cost_tracker.sh" init --target-usd 0.01 --estimated-usd 0.80
"$SKILL/scripts/cost_tracker.sh" record --tier worker --input 200000 --output 100000 \
  --model gemini-3.5-flash
set +e
check_out=$("$SKILL/scripts/cost_tracker.sh" check 2>&1)
check_rc=$?
set -e
[ "$check_rc" -eq 0 ] || fail "check must exit 0 over target (got $check_rc)"
echo "$check_out" | grep -q ADVISORY || fail "check must print ADVISORY"
"$SKILL/scripts/cost_tracker.sh" status
pass "check advisory over target, exit 0"
rm -f "$COST_TRACKER"

section "Parser fixtures"
tmpdir=$(mktemp -d)
cat > "$tmpdir/estimate.txt" <<'JSON'
{"estimated_input_tokens":1200,"estimated_output_tokens":600,"estimated_usd":0.42,
 "breakdown":[{"tier":"workers","calls":2,"usd":0.10}],
 "worth_it":true,"recommendation":"Proceed with 2 workers.",
 "optimizations":[{"action":"merge briefs","estimated_savings_usd":0.05}]}
JSON
"$SKILL/scripts/parse_estimate.sh" "$tmpdir/estimate.txt" | jq -e . >/dev/null
cat > "$tmpdir/papa.txt" <<'TXT'
ROUTE: advisor
REASON: Worker A says 100 req/min, Worker B says 1000 req/min — needs advisor judgment.
TXT
"$SKILL/scripts/parse_papa_route.sh" "$tmpdir/papa.txt" | grep -q "ROUTE: advisor"
rm -rf "$tmpdir"
pass "parse_estimate + parse_papa_route fixtures"

api_key="${GEMINI_API_KEY:-${GOOGLE_API_KEY:-}}"
if [ -z "$api_key" ]; then
  section "Live API scenarios 1–3"
  echo "SKIP  GEMINI_API_KEY / GOOGLE_API_KEY not set"
  echo "SKIP  live estimator, Papa conflict, Papa disagreement"
  exit 0
fi

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

section "Scenario 1 — Flash estimator (live)"
estimate_brief="$tmpdir/estimate_brief.txt"
estimate_response="$tmpdir/estimate_response.json"
estimate_text="$tmpdir/estimate_text.txt"
cat > "$estimate_brief" <<'BRIEF'
You are the cost estimator. PLAN: 2 worker subtasks, 1 advisor plan review, 1 taste pass, 0 Papa.
PRICING: gemini-3.5-flash 0.15/0.60 per 1M; claude-fable-5 3/15 per 1M.
TASK: Compare Notion vs Obsidian pricing and one weakness each.
Respond ONLY with JSON: estimated_input_tokens, estimated_output_tokens, estimated_usd,
breakdown, worth_it, recommendation, optimizations (array).
BRIEF
model="$ESTIMATOR_MODEL"
( set -o pipefail
  jq -n --rawfile t "$estimate_brief" '{contents:[{parts:[{text:$t}]}]}' \
    | curl -sS --fail --max-time 120 \
      "https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent" \
      -H "x-goog-api-key: $api_key" -H "Content-Type: application/json" -d @- \
    | tee "$estimate_response" \
    | jq -r '.candidates[0].content.parts[0].text' ) > "$estimate_text"
"$SKILL/scripts/parse_estimate.sh" "$estimate_text"
inp=$(jq -r '.usageMetadata.promptTokenCount' "$estimate_response")
out=$(jq -r '.usageMetadata.candidatesTokenCount' "$estimate_response")
echo "Estimator tokens: in=$inp out=$out model=$model"
pass "live estimator + parse"

section "Scenario 2 — Papa conflict (live)"
routing="$tmpdir/routing.txt"
papa_response="$tmpdir/papa_response.json"
papa_text="$tmpdir/papa_text.txt"
cat > "$routing" <<'ROUTE'
REQUEST TYPE: conflict
TASK: API rate limit research for two note apps.
QUESTION: Worker A claims 100 req/min, Worker B claims 1000 req/min for same API. Who wins?
MATERIAL: A: "100/min per docs v1." B: "1000/min enterprise tier."
COST SNAPSHOT: COST: $0.10 / $0.50 target
Respond: ROUTE: advisor|orchestrator and REASON: one line.
ROUTE
papa_model="$PAPA_MODEL"
( set -o pipefail
  jq -n --rawfile r "$routing" \
    '{contents:[{parts:[{text:$r}]}], generationConfig:{maxOutputTokens:512}}' \
    | curl -sS --fail --max-time 120 \
      "https://generativelanguage.googleapis.com/v1beta/models/${papa_model}:generateContent" \
      -H "x-goog-api-key: $api_key" -H "Content-Type: application/json" -d @- \
    | tee "$papa_response" \
    | jq -r '.candidates[0].content.parts[0].text' ) > "$papa_text"
cat "$papa_text"
"$SKILL/scripts/parse_papa_route.sh" "$papa_text"
pin=$(jq -r '.usageMetadata.promptTokenCount' "$papa_response")
pout=$(jq -r '.usageMetadata.candidatesTokenCount' "$papa_response")
echo "Papa tokens: in=$pin out=$pout model=$papa_model"
pass "live Papa conflict + parse"

section "Scenario 3 — Papa advisor-orchestrator disagreement (live)"
cat > "$routing" <<'ROUTE'
REQUEST TYPE: advisor-orchestrator disagreement
TASK: Compare Notion vs Obsidian.
QUESTION: Advisor demands 8-app competitive matrix; orchestrator wants 2-app comparison only.
MATERIAL: Advisor: "scope too narrow, expand to 8 apps." Orchestrator: "success criteria say exactly 2 apps."
COST SNAPSHOT: COST: $0.20 / $1.00 target
Respond: ROUTE: advisor|orchestrator and REASON: one line.
ROUTE
( set -o pipefail
  jq -n --rawfile r "$routing" \
    '{contents:[{parts:[{text:$r}]}], generationConfig:{maxOutputTokens:512}}' \
    | curl -sS --fail --max-time 120 \
      "https://generativelanguage.googleapis.com/v1beta/models/${papa_model}:generateContent" \
      -H "x-goog-api-key: $api_key" -H "Content-Type: application/json" -d @- \
    | tee "$papa_response" \
    | jq -r '.candidates[0].content.parts[0].text' ) > "$papa_text"
cat "$papa_text"
"$SKILL/scripts/parse_papa_route.sh" "$papa_text"
pass "live Papa disagreement + parse"
