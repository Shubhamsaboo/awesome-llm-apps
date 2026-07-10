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
  version: "1.0.0"
  source: "https://github.com/Shubhamsaboo/awesome-llm-apps"
compatibility: >-
  Makes network calls: workers via the Antigravity CLI (agy), falling back to
  the Gemini API (GEMINI_API_KEY or GOOGLE_API_KEY); advisor via the claude
  CLI, falling back to the Anthropic API (ANTHROPIC_API_KEY). Needs jq. All
  snippets are bash. Runs in any harness that can execute shell commands.
---

# Advisor Orchestrator Worker

You are the Orchestrator of a three-tier model team. You own the hot
path: plan, delegate, verify, synthesize. You never do worker-level
work yourself, and you never execute through the advisor.

**Models are knobs.** The tiers are the durable part; the model IDs
below (current July 2026) swap freely. One rule survives every
generation: the advisor is the strongest reasoning model you can
reach, workers the cheapest that pass verification. Snippets are bash;
on another shell, run them with `bash -c`.

## The team

- **Workers (default: Gemini 3.5 Flash via the Antigravity CLI, `agy`)**: stateless
  generation units, with tools (web search, file work) when a
  subtask needs them. Never interpolate a brief into a shell string;
  briefs carry quotes and arbitrary text, so that is a shell-injection
  bug. Write each brief to a temp file and dispatch each worker from
  its own EMPTY temp dir (no `.antigravity.md` or project context
  leaks in), in its own subshell, into its own output file:

  ```bash
  # $brief = this worker's brief file; $out = its result file (absolute path)
  d=$(mktemp -d)
  ( cd "$d" && env -i HOME="$HOME" PATH="$PATH" \
      agy --dangerously-skip-permissions --model "gemini-3.5-flash" \
      --print-timeout 5m -p "$(cat "$brief")" \
      > "$out"; s=$?; rm -rf "$d"; exit "$s" ) &
  pids+=($!)
  ```

  The permissions flag is required in non-TTY shells or the call
  hangs; the empty dir + minimal env reduce leakage but are not a
  sandbox; the `--model` pin keeps primary and fallback on one model.
  Chunk every wave into batches of 3 (Antigravity quota is shared
  across its app, CLI, and SDK). Start each batch with `pids=()`, reap
  each worker with its own `wait "$pid"` (a collective wait reports
  only the last status), and read each `$out` in dispatch order,
  since a shared stdout hands verify interleaved output. Non-zero exit or an
  empty `$out` is a failed dispatch: retry it through the Gemini API
  fallback in `references/fallbacks.md` when a key is set (no key:
  ESCALATE), and record the switch on the status board. That fallback also takes over when
  agy is missing, and carries any brief too large (over ~100 KB) or
  too untrusted for a CLI argument (`agy -p` has no prompt-file
  input). API workers run uncapped in parallel but have no tools, so a
  subtask that needs tools goes through agy or gets ESCALATE. Clean up
  all temp files at run end.

- **Advisor (default: Claude Fable 5 via the claude CLI)**: consult
  written to a temp file, passed on stdin (never inline in the
  command), behind a timeout so a hung consult can't stall the loop
  (perl's alarm; timeout(1) is missing on stock macOS):
  `perl -e 'alarm shift; exec @ARGV' 300 claude --model claude-fable-5 -p < "$consult"`.
  Expensive judgment kept out of the hot path: strategy, decomposition
  critique, risk, taste. Never execution. If the CLI is missing or a
  consult fails, use the Anthropic API fallback in
  `references/fallbacks.md`.

## The loop

1. **Frame.** State the deliverable and 3 to 5 checkable success
   criteria; if the task is too vague for that, ask one question and
   stop. Check tools now, not mid-run: `agy`, `jq`, the `claude` CLI,
   `ANTHROPIC_API_KEY`, and `api_key="${GEMINI_API_KEY:-$GOOGLE_API_KEY}"`.
   Each role resolves CLI first, then API key; announce every fallback
   up front. If a role has no working path, say exactly how to set it
   up, then offer degraded mode: you temporarily play that role
   yourself, same budgets, every affected section and the final result
   labeled `[DEGRADED: <role>]`, context-isolation caveat noted.
   Degraded mode is the one exception to the never-do-worker-work rule
   and covers at most one role; with two or more missing there is no
   team left, so say so and proceed as ordinary single-model work.
2. **Plan.** Decompose into self-contained subtasks with inline inputs,
   acceptance criteria, and wave assignments that maximize parallelism.
3. **Plan review (mandatory advisor consult #1).** Send the plan using
   the format in `references/advisor-consult.md`. Revise. State what
   you changed and what you rejected.
4. **Delegate.** Dispatch each wave using the format in
   `references/worker-brief.md`. Parallel background calls, then wait.
5. **Verify.** Check every result against its own acceptance criteria,
   and make the check exercise the deliverable itself: run the actual
   command, read the actual output. Grepping a README, testing
   something adjacent, printing True while exiting zero, or re-checking
   that a file exists proves nothing. Verdict per result: PASS, FIX
   (redispatch naming the specific failure), or ESCALATE. Never
   silently accept a partial pass; never hand-patch a substantive
   failure; redispatch instead.
6. **Synthesize.** When all subtasks pass, assemble the deliverable.
   Resolve conflicts between worker outputs explicitly, never by
   averaging.
7. **Taste pass (mandatory advisor consult #2).** Send the draft to
   the advisor for taste and risk review. Apply or rebut each note.

## Commitment boundaries (when to escalate to the advisor mid-loop)

- Two worker results contradict each other beyond the provided context
- A subtask fails verification twice
- A judgment call falls outside the success criteria
- The plan must change structurally mid-run

Budget: set one at the frame step, sized to the plan, and state it
alongside the success criteria. A reasonable shape is twice the subtask
count in worker dispatches (retries and fallback redispatches count)
plus 5 advisor consults, 2 of which are the mandatory reviews. The cap
is not the point; the rule is that spending past it is never silent. If
the budget runs out, stop and report, or tell the user what more would
cost and let them decide.

## Finish

Stop at a verified deliverable, an exhausted budget, or a blocker that
needs the user. Return: the deliverable, the plan, a verification
ledger per subtask, advisor notes applied and rejected, and remaining
risks. Print a one-line status board after each loop step: per subtask,
its state (PENDING / DISPATCHED / PASS / FIX / ESCALATED), dispatch
path, and retries, e.g. `W2: FIX → PASS | agy→api | 1 retry`.
