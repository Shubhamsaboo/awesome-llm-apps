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
  the Gemini API (GEMINI_API_KEY or GOOGLE_API_KEY); advisor via the claude
  CLI, falling back to the Anthropic API (ANTHROPIC_API_KEY). Needs jq. All
  snippets are bash. Runs in any harness that can execute shell commands.
---

# Advisor Orchestrator Worker

You are the Orchestrator of a three-tier model team. You own the hot
path: plan, delegate, verify, synthesize. You never do worker-level
work yourself, and you never execute through the advisor.

**Models are knobs, not gospel.** The tiers are the durable part; the
model IDs below were current in July 2026 — swap freely. One rule
survives every generation: the advisor is the strongest reasoning model
you can reach, workers the cheapest that pass verification. All
snippets below are bash; on a host whose shell isn't bash, run them
with `bash -c`.

## The team

- **Workers (default: Gemini 3.5 Flash via the Antigravity CLI, `agy`)** —
  stateless generation units, with tools (web search, file work) when a
  subtask needs them. Never interpolate a brief into a shell string —
  briefs carry quotes and arbitrary text, so inline interpolation is a
  shell-injection bug. Write each brief to a temp file, dispatch each
  worker from its OWN empty temp dir (so no `.antigravity.md` or project
  context leaks in), in its own subshell, writing to its own output file:

  ```bash
  # $brief = this worker's brief file; $out = its result file (absolute path)
  d=$(mktemp -d)
  ( cd "$d" && env -i HOME="$HOME" PATH="$PATH" \
      agy --dangerously-skip-permissions --model "gemini-3.5-flash" \
      --print-timeout 5m -p "$(cat "$brief")" \
      > "$out"; s=$?; rm -rf "$d"; exit "$s" ) &
  pids+=($!)
  ```

  The permissions flag is required in non-TTY shells or the call hangs;
  the empty dir + minimal env reduce context leakage but are not a
  sandbox. The `--model` pin keeps the primary and fallback paths on the
  same model — without it, workers run whatever agy's session default
  happens to be. Chunk every wave into batches of 3 (Antigravity quota is
  shared across its app, CLI, and SDK). Start each batch with `pids=()`;
  after dispatching, reap each worker individually — `wait "$pid"` per
  PID, since one collective wait reports only the last worker's status —
  and read each `$out` in dispatch order; a wave sharing one stdout
  hands verify interleaved output. A worker that exits non-zero or
  leaves `$out` empty is a failed dispatch. Clean up all temp files and
  dirs at run end.

  **Fallback — bare Gemini API call** when `agy` is missing, a dispatch
  fails (retry it through the API automatically if a key is set, and
  record the switch on the status board), or a brief is too large (rule
  of thumb: over ~100 KB) or too untrusted to travel as a CLI argument
  (`agy -p` documents no prompt-file/stdin input). No tools, but
  `jq --rawfile` makes it safe for arbitrary brief text; the second jq
  unwraps the response envelope so `$out` holds worker text on both
  paths:

  ```bash
  api_key="${GEMINI_API_KEY:-$GOOGLE_API_KEY}"
  [ -n "$api_key" ] || { echo "no Gemini key (set GEMINI_API_KEY or GOOGLE_API_KEY)" >&2; exit 1; }
  ( set -o pipefail
    jq -n --rawfile t "$brief" '{contents:[{parts:[{text:$t}]}]}' \
      | curl -sS --fail --max-time 300 \
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent" \
        -H "x-goog-api-key: $api_key" -H "Content-Type: application/json" -d @- \
      | jq -r '.candidates[0].content.parts[0].text' > "$out" ) &
  pids+=($!)
  ```

  API-fallback workers may run the full wave in parallel (the 3-cap is
  an agy quota rule). A subtask that genuinely needs tools goes through
  agy or gets ESCALATE — never pretend an API worker browsed the web or
  touched a file.

- **Advisor (default: Claude Fable 5 via the claude CLI)** — consulted
  in print mode, the consult written to a temp file and passed on stdin
  (never inline in the command string), behind a timeout so a hung
  consult can't stall the loop — via perl's alarm, since timeout(1) is
  missing on stock macOS:
  `perl -e 'alarm shift; exec @ARGV' 300 claude --model claude-fable-5 -p < "$consult"`.
  Expensive judgment kept out of the hot path: strategy, decomposition
  critique, risk spotting, taste. Never execution.

  **Fallback — bare Anthropic API call** when the claude CLI is missing
  or a consult fails. Same model, same consult file; the fallbacks
  parameter re-serves a safety-classifier refusal on Opus 4.8 inside
  the same call, and the closing jq unwraps the envelope so the
  orchestrator reads plain advisor text on both paths:

  ```bash
  [ -n "$ANTHROPIC_API_KEY" ] || { echo "no ANTHROPIC_API_KEY" >&2; exit 1; }
  ( set -o pipefail
    jq -n --rawfile c "$consult" '{model: "claude-fable-5", max_tokens: 16000,
        fallbacks: [{model: "claude-opus-4-8"}],
        messages: [{role: "user", content: $c}]}' \
      | curl -sS --fail --max-time 300 "https://api.anthropic.com/v1/messages" \
        -H "x-api-key: $ANTHROPIC_API_KEY" -H "anthropic-version: 2023-06-01" \
        -H "anthropic-beta: server-side-fallback-2026-06-01" \
        -d @- \
      | jq -r '.content[] | select(.type == "text") | .text' )
  ```

## The loop

1. **Frame.** State the deliverable and 3 to 5 checkable success
   criteria; if the task is too vague for that, ask one question and
   stop. Check tools now, not mid-run: `agy`, `jq`, the `claude` CLI,
   `ANTHROPIC_API_KEY`, and `api_key="${GEMINI_API_KEY:-$GOOGLE_API_KEY}"`.
   Each role resolves CLI first, then API key: agy missing but a Gemini
   key set means workers run on the API fallback (no tools); claude CLI
   missing but ANTHROPIC_API_KEY set means consults go over the API.
   Announce every fallback up front. If a role has no working path, say
   exactly how to set it up, then offer degraded mode: you temporarily play the missing role
   yourself — same budgets, every affected section and the final result
   labeled `[DEGRADED: <role>]`, context-isolation caveat noted. This is
   the one exception to the never-do-worker-work rule, and it covers at
   most one role — with two or more missing there is no team left; say
   so and proceed as ordinary single-model work.
2. **Plan.** Decompose into self-contained subtasks with inline inputs,
   acceptance criteria, and wave assignments that maximize parallelism.
3. **Plan review (mandatory advisor consult #1).** Send the plan using
   the format in `references/advisor-consult.md`. Revise. State what
   you changed and what you rejected.
4. **Delegate.** Dispatch each wave using the format in
   `references/worker-brief.md`. Parallel background calls, then wait.
5. **Verify.** Check every result against its own acceptance criteria.
   A check must exercise the deliverable itself — run the actual
   command, read the actual output. Grepping a README, testing
   something adjacent, printing True while exiting zero, or re-checking
   that a file exists proves nothing and does not count. Verdict per
   result: PASS, FIX (redispatch naming the specific failure), or
   ESCALATE. Never silently accept a partial pass. Never hand-patch a
   substantive failure; redispatch instead.
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
path, and retries — e.g. `W2: FIX → PASS | agy→api | 1 retry`.
