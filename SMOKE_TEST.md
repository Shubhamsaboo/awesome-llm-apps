# Live API smoke test

**Status: BLOCKED** — `GEMINI_API_KEY` / `GOOGLE_API_KEY` and `ANTHROPIC_API_KEY` were not present in the agent shell environment when this was run (2026-07-10).

Per plan: do not open the upstream PR until a live smoke test passes or the contributor explicitly accepts a CI-only submission.

## Prerequisites

```bash
export PAPA_MODEL=gemini-3.1-pro-preview
export ESTIMATOR_MODEL=gemini-3.1-flash-lite
export GEMINI_API_KEY=...   # or GOOGLE_API_KEY
export ANTHROPIC_API_KEY=...  # scenario 2 only (Papa routes advisor)
```

## Scenario 1 — Simple 2-subtask research (orchestrator route)

**Goal:** Estimator JSON → user approves ceiling → Papa routes `orchestrator` → no Fable spend.

1. Frame: compare two note-taking apps (pricing + one weakness each).
2. Plan: 2 worker briefs, 1 Papa call at plan review, 0 advisor unless escalated.
3. Run Flash estimator (`references/cost-estimate.md` + `fallbacks.md`).
4. `scripts/parse_estimate.sh` on response text → `cost_tracker.sh init`.
5. Approve ceiling (e.g. $0.50).
6. Papa `plan review` → `scripts/parse_papa_route.sh` → expect `ROUTE: orchestrator`.
7. Dispatch 2 workers (stub or real), verify PASS, synthesize.
8. Papa `taste pass` → expect `orchestrator`.
9. `scripts/cost_tracker.sh status` — record token counts and final USD.

**Evidence to capture:** estimator JSON, Papa ROUTE/REASON lines, `status` output.

## Scenario 2 — Forced conflict (advisor route)

**Goal:** Contradictory worker outputs → Papa routes `advisor` at verify or taste pass.

1. Same frame; plan includes explicit conflict injection in worker briefs.
2. After workers return opposing claims, Papa `taste pass` with conflict summary.
3. Expect `ROUTE: advisor` → one Fable consult via `references/advisor-consult.md`.
4. Record advisor usage; `cost_tracker.sh status`.

**Evidence to capture:** Papa REASON citing conflict, advisor consult recorded.

## Scenario 3 — Budget kill

**Goal:** Low approved ceiling → mid-run `cost_tracker.sh check` exits 2.

1. Frame + plan for 3+ worker dispatches.
2. Estimator returns higher `estimated_usd`; user approves a **low** ceiling (e.g. $0.05).
3. `cost_tracker.sh init --approved-usd 0.05 --estimated-usd <estimate>`.
4. Record enough usage (or synthetic `record` calls) to exceed ceiling.
5. `scripts/cost_tracker.sh check` → exit 2; orchestrator stops and reports honestly.

**Evidence to capture:** `check` stderr, `status` showing over-ceiling state.

## CI-only verification (completed without live APIs)

All repo-side checks pass on branch `extend-advisor-orchestrator-papa-cost`:

```bash
python3 agent_skills/evals/tools/skill_lint.py agent_skills/advisor-orchestrator-worker --strict
python3 agent_skills/evals/tools/run_trigger_evals.py
python3 agent_skills/evals/tools/skill_scanner.py agent_skills
python3 agent_skills/evals/advisor-orchestrator-worker/test_cost_tracker.py
python3 agent_skills/evals/advisor-orchestrator-worker/test_parse_estimate.py
python3 agent_skills/evals/advisor-orchestrator-worker/test_parse_papa_route.py
```

Re-run live scenarios after exporting API keys, then replace this file's BLOCKED section with command transcripts and token numbers.
