# Cost Control

Cost control is deterministic. It runs as code, not as token generation.
Every worker dispatch, Papa routing call, and advisor consult passes through
the ledger before the shell command fires.

## Initialize at the frame step

After sizing the budget, init the ledger and export its path for the run:

```bash
ledger=$(mktemp)
export COST_LEDGER="$ledger"
scripts/cost_ledger.sh init \
  --workers "$max_workers" \
  --papa "$max_papa" \
  --consults "$max_consults"
```

Default caps if the plan does not specify otherwise:

| Kind | Formula |
|---|---|
| Workers | `2 × subtask_count` (retries and fallback redispatches count) |
| Papa | `subtask_count + 3` (plan gate, taste gate, one per commitment boundary) |
| Advisor consults | `5` (Papa may spend fewer by routing `orchestrator`) |

## Checkpoint before every call

```bash
scripts/cost_ledger.sh checkpoint worker   # before each worker dispatch
scripts/cost_ledger.sh checkpoint papa     # before each Papa consult
scripts/cost_ledger.sh checkpoint consult  # before each advisor consult
```

Exit `0` = proceed. Exit `2` = budget exhausted — stop the call, do not
silently retry on a different path. The orchestrator must either:

1. Report honestly with the ledger snapshot, or
2. Ask the user for a higher cap

## Ledger snapshot on the status board

After each loop step, print spend alongside subtask state:

```
COST: workers 4/8 | papa 2/6 | consults 1/5
```

## Kill rules

- Never spend past the cap silently.
- A failed checkpoint is not an excuse to hand-patch or skip verification.
- Retries and API-fallback redispatches consume the same worker slot.

## Cleanup

```bash
scripts/cost_ledger.sh status   # final snapshot for the report
rm -f "$COST_LEDGER"
```
