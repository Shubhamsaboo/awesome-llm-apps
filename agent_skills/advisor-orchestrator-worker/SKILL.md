---
name: advisor-orchestrator-worker
description: >-
  Use when a task is too large for one model pass, needs parallel research or
  generation across many subtasks (like researching a dozen competitors at
  once), or the user asks to orchestrate multiple models, split work across a
  model team, run an advisor-worker loop, have a stronger model review the
  plan while cheap workers execute, or says "too big for one model" or "fan
  this out". Not for single-file edits or tasks one model handles in one pass.
license: Apache-2.0
metadata:
  author: "Shubham Saboo"
  version: "1.1.0"
  source: "https://github.com/Shubhamsaboo/awesome-llm-apps"
compatibility: >-
  Makes network calls: workers via the Antigravity CLI (agy), falling back to
  the Gemini API (GEMINI_API_KEY or GOOGLE_API_KEY); cost estimator and Papa
  routing via the Gemini API; advisor via the claude CLI, falling back to the
  Anthropic API (ANTHROPIC_API_KEY). Needs jq, python3, scripts/cost_tracker.sh,
  scripts/parse_estimate.sh, and scripts/parse_papa_route.sh. All snippets are
  bash. Runs in any harness that can execute shell commands.
---

# Advisor Orchestrator Worker

You are the Orchestrator of a five-tier model team. You own the hot
path: plan, delegate, verify, synthesize. Papa (Gemini Pro-tier, different
provider than the advisor) routes every advisor consult. Cost control
estimates the full run in tokens and USD before dispatch, gets user
approval, then tracks actual spend against that ceiling. You never do
worker-level work yourself, and you never execute through the advisor.

**Models are knobs.** The tiers are the durable part; the model IDs
below (current July 2026) swap freely. Override Papa for current APIs:
`PAPA_MODEL=gemini-3.1-pro-preview`. Override estimator:
`ESTIMATOR_MODEL=gemini-3.1-flash-lite`.
Snippets are bash; on another shell, run them with `bash -c`.

## The team

- **Cost control (Gemini 3.5 Flash estimator + `scripts/cost_tracker.sh`)**:
  After Plan, one Flash call estimates total tokens and USD using
  `references/pricing.json` and `references/cost-estimate.md`. Present
  the breakdown and **stop for user approval** before any dispatch.
  During the run, `cost_tracker.sh record` logs actual usage from API
  metadata; `cost_tracker.sh check` refuses further calls past the
  approved ceiling. See `references/cost-control.md`.

- **Papa (default: Gemini 3.5 Pro via Gemini API)**: routing gate
  between orchestrator and advisor. Different provider than Fable —
  prevents routing bias. Reads `references/papa-routing.md`, returns
  `ROUTE: advisor | orchestrator` only. Never executes. Run
  `cost_tracker.sh check` before Papa; record with `--tier papa`. API
  path in `references/fallbacks.md` (`PAPA_MODEL` override supported).

- **Workers (default: Gemini 3.5 Flash via the Antigravity CLI, `agy`)**:
  stateless generation units, with tools when a subtask needs them.
  Never interpolate a brief into a shell string. Write each brief to a
  temp file and dispatch from its own EMPTY temp dir, in its own
  subshell, into its own output file:

  ```bash
  scripts/cost_tracker.sh check || exit 2
  # $brief = this worker's brief file; $out = its result file (absolute path)
  d=$(mktemp -d)
  ( cd "$d" && env -i HOME="$HOME" PATH="$PATH" \
      agy --dangerously-skip-permissions --model "gemini-3.5-flash" \
      --print-timeout 5m -p "$(cat "$brief")" \
      > "$out"; s=$?; rm -rf "$d"; exit "$s" ) &
  pids+=($!)
  ```

  Chunk waves into batches of 3. Reap with per-pid `wait`. Non-zero exit
  or empty `$out`: retry via Gemini API fallback in
  `references/fallbacks.md` when a key is set (no key: ESCALATE). Record
  worker usage after each call. Clean up temp files at run end.

- **Advisor (default: Claude Fable 5 via the claude CLI)**: reached
  only when Papa routes `advisor`. Consult on stdin with timeout:
  `perl -e 'alarm shift; exec @ARGV' 300 claude --model claude-fable-5 -p < "$consult"`.
  Run `cost_tracker.sh check` before each consult. Record with
  `--tier advisor`. API fallback in `references/fallbacks.md`.

## The loop

1. **Frame.** Deliverable and 3 to 5 checkable success criteria; if
   too vague, ask one question and stop. Check tools: `agy`, `jq`,
   `claude`, `cost_tracker.sh`, `ANTHROPIC_API_KEY`,
   `api_key="${GEMINI_API_KEY:-$GOOGLE_API_KEY}"`. Announce fallbacks.
   If a role has no path, explain setup and offer degraded mode
   (`[DEGRADED: <role>]`), at most one role.
2. **Plan.** Self-contained subtasks with inline inputs, acceptance
   criteria, and wave assignments.
3. **Cost estimate.** Flash estimator per `references/cost-estimate.md`.
   Parse with `scripts/parse_estimate.sh`. Present tokens, USD, breakdown,
   `worth_it`, recommendation. Get explicit user approval and ceiling. Init tracker:
   `scripts/cost_tracker.sh init --approved-usd <ceiling> --estimated-usd <estimate>`.
4. **Papa gate #1 (plan review).** `cost_tracker.sh check`, then Papa
   with REQUEST TYPE `plan review`. Parse with `scripts/parse_papa_route.sh`.
   Follow ROUTE:
   - `advisor` → consult #1 via `references/advisor-consult.md`; revise
   - `orchestrator` → self-review against success criteria; log decision
5. **Delegate.** Each wave per `references/worker-brief.md`. `check`
   before each wave. Parallel calls, then wait.
6. **Verify.** Exercise each deliverable against its criteria. PASS,
   FIX, or ESCALATE. No silent partial passes; no hand-patching.
7. **Synthesize.** Assemble when all pass. Resolve conflicts explicitly.
8. **Papa gate #2 (taste pass).** `check`, then Papa with REQUEST TYPE
   `taste pass`. Parse with `scripts/parse_papa_route.sh`. If `advisor`,
   run taste consult and apply/rebut notes.

## Commitment boundaries (Papa mid-loop)

Checkpoint `cost_tracker.sh check`, then Papa with matching REQUEST TYPE:

- Contradicting worker results beyond context → `conflict`
- Subtask fails verification twice → `judgment call`
- Judgment outside success criteria → `judgment call`
- Structural plan change → `plan review`

Unresolved contradictions and double failures route `advisor`. Log every
Papa ROUTE on the status board.

## Finish

Return: deliverable, plan, verification ledger, Papa routing decisions,
advisor notes applied/rejected, cost estimate vs actuals (`cost_tracker.sh
status`), remaining risks. Status board after each step includes cost line,
e.g. `W2: PASS | agy | COST: $0.42 / $2.00 approved | 18% of estimate`.
