# Live API smoke test

**Run:** 2026-07-10 · `smoke_run.sh` · full log: `SMOKE_TEST_RESULTS.txt`

## Summary

| Scenario | Status | Evidence |
|----------|--------|----------|
| CI gate (6 commands) | **PASS** | lint, trigger, scanner, 12+4+4 unit tests |
| Parser fixtures | **PASS** | `parse_estimate.sh`, `parse_papa_route.sh` |
| Scenario 4 — over-target advisory | **PASS** | `check` exit 0, `ADVISORY` printed, status shows over target |
| Scenarios 1–3 — live Gemini/Papa | **SKIP** | `GEMINI_API_KEY` / `GOOGLE_API_KEY` not in shell |

## Scenario 4 output (non-blocking cost control)

```
COST: $0.09 / $0.01 target | 11% of estimate | 200k in / 100k out
OVER TARGET by $0.08 (advisory)
ADVISORY: over target by $0.08 — trim briefs, batch waves, or defer optional consults
(check exit code: 0)
```

## Live API (blocked)

Export keys and re-run:

```bash
export GEMINI_API_KEY=...
export PAPA_MODEL=gemini-3.1-pro-preview
export ESTIMATOR_MODEL=gemini-3.1-flash-lite
./smoke_run.sh
```

Scenarios 1–3 will call Flash estimator, Papa conflict, and Papa disagreement paths.

## CI commands (all green)

```bash
python3 evals/tools/skill_lint.py advisor-orchestrator-worker --strict
python3 evals/tools/run_trigger_evals.py
python3 evals/tools/skill_scanner.py advisor-orchestrator-worker
python3 evals/advisor-orchestrator-worker/test_cost_tracker.py
python3 evals/advisor-orchestrator-worker/test_parse_estimate.py
python3 evals/advisor-orchestrator-worker/test_parse_papa_route.py
```
