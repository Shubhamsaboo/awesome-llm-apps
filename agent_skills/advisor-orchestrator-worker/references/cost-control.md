# Cost Control

Cost control is **advisory, not a gate**. It helps the orchestrator and user
see spend, compare against the pre-flight estimate, and **burn fewer tokens**
— it never blocks dispatch, consults, or Papa on its own.

Two layers: **pre-flight estimate** (Flash LLM + optimizations) and **runtime
tracker** (`scripts/cost_tracker.sh`). No dispatch caps.

## Pre-flight (after Plan, before advisor plan review)

1. Build the brief per `references/cost-estimate.md`
2. Call Gemini Flash (see `references/fallbacks.md`)
3. Parse with `scripts/parse_estimate.sh`
4. Present tokens, USD, breakdown, `worth_it`, `recommendation`, and any
   `optimizations` — **apply cheap wins before dispatch** (merge subtasks,
   defer optional consults, trim brief size)
5. Init tracker with estimate as the soft target (user's stated budget from
   frame overrides if present):

```bash
export COST_TRACKER=$(mktemp)
export COST_PRICING="$(dirname "$0")/../references/pricing.json"
scripts/cost_tracker.sh init \
  --target-usd "${user_budget:-$estimate}" \
  --estimated-usd "$estimate"
```

Do **not** stop the loop for approval unless the user explicitly asked to
confirm spend at frame. Keep moving; optimize first.

## Runtime (after every API call)

Record actual usage from response metadata. Missing metadata → chars/4 fallback.

```bash
scripts/cost_tracker.sh record --tier worker --input 1200 --output 800 \
  --model gemini-3.5-flash
scripts/cost_tracker.sh check   # advisory only — always continues
```

Run `status` on the status board after each loop step. If `check` prints an
over-target advisory, consider: smaller briefs, fewer retries, batching waves,
skipping redundant consults when advisor and orchestrator already align — but
**do not** abandon verification or hand-patch failures to save money.

## Status board

```bash
scripts/cost_tracker.sh status
```

Example: `COST: $0.42 / $0.80 target | 52% of estimate | 84k in / 31k out`

## Soft targets only

- `target_usd` is a comparison line, not permission to run.
- Over target → log advisory, suggest optimizations, continue unless the user
  said stop at frame.
- Never silent bleed: always record and show actuals in the final report.

## Cleanup

```bash
scripts/cost_tracker.sh status   # include estimate vs actual + optimizations applied
rm -f "$COST_TRACKER"
```
