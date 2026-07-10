# Cost Control

Two layers: **pre-flight estimate** (Flash LLM) and **runtime tracker**
(deterministic script). No arbitrary dispatch-count caps.

## Pre-flight (after Plan, before Papa gate #1)

1. Build the cost estimate brief per `references/cost-estimate.md`
2. Call Gemini Flash API (see `references/fallbacks.md` — cost estimator block)
3. Parse JSON; present tokens, USD, breakdown, `worth_it`, recommendation
4. Ask the user to approve a ceiling (default: estimated USD + 10% buffer, or
   their stated budget from frame)
5. Init tracker:

```bash
export COST_TRACKER=$(mktemp)
export COST_PRICING="$(dirname "$0")/../references/pricing.json"
# or absolute path to skill/references/pricing.json
scripts/cost_tracker.sh init \
  --approved-usd "$ceiling" \
  --estimated-usd "$estimate"
```

## Runtime (after every API call)

Record actual usage from response metadata (`usageMetadata` on Gemini,
`usage` on Anthropic). If missing, fallback chars/4 per ASIL.

```bash
scripts/cost_tracker.sh record --tier worker --input 1200 --output 800 \
  --model gemini-3.5-flash
scripts/cost_tracker.sh check || exit 2   # refuse if over approved ceiling
```

Run `check` before each worker wave, each Papa call, and each advisor consult.

## Status board

After each loop step, append cost line from:

```bash
scripts/cost_tracker.sh status
```

Example: `COST: $0.42 / $2.00 approved | 18% of estimate | 84k in / 31k out`

## Kill rules

- `check` exit 2 = over approved ceiling — stop, report actuals vs estimate,
  ask user to raise ceiling or abort. Never silent bleed.
- Failed `check` is not an excuse to skip verification or hand-patch failures.
- User-approved ceiling is the only hard stop; there is no hidden dispatch cap.

## Cleanup

```bash
scripts/cost_tracker.sh status   # include in final report
rm -f "$COST_TRACKER"
```
