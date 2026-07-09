# 🧠 Advisor Executor Worker

**One model is a bottleneck. A team with one brain, twenty hands, and a board advisor is not.**

This skill turns your coding agent into the orchestrator of a three-tier model team:

- **Workers** — the cheapest model that passes verification, dispatched as stateless parallel API calls. Each one sees a single self-contained brief and nothing else.
- **Orchestrator** — your agent. Owns the hot path: frame, plan, delegate, verify, synthesize. Never does worker-level work itself.
- **Advisor** — the strongest reasoning model you can reach, consulted exactly where judgment matters: plan review before dispatch, taste pass before delivery, and mid-loop only at commitment boundaries (contradicting results, double failures, structural plan changes).

The economics are the point: parallel cheap generation where volume wins, expensive judgment only where it changes a decision. Budgeted — 20 worker calls, 5 consults — so a run can't quietly burn a hole in your API bill.

## What makes it hold together

- **Stateless worker briefs** ([references/worker-brief.md](references/worker-brief.md)) — every dispatch carries its full inputs and acceptance criteria inline. No shared context, no context leaks, no "as discussed above."
- **Verification before synthesis** — every result is judged against its own acceptance criteria: PASS, FIX (redispatched with the named failure), or ESCALATE. Partial passes are never silently accepted.
- **The advisor is a critic, not an executor** ([references/advisor-consult.md](references/advisor-consult.md)) — it returns a verdict, ranked risks, and concrete fixes in under 300 words. Every note gets applied or explicitly rebutted, never dropped.
- **Models are knobs** — the defaults (Gemini Flash workers, Claude advisor, Codex orchestrator) were current in July 2026; the tier pattern is the durable part. Swap any role.

## Install

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/awesome_agent_skills/advisor-executor-worker
```

Or manually: copy this folder into your agent's skills dir (`~/.claude/skills/`, `~/.codex/skills/`, `~/.agents/skills/`).

**Requirements** (declared up front, per this repo's rules): workers call the Gemini API (`GEMINI_API_KEY`), the advisor uses the `claude` CLI, and tool-using workers optionally use the `agy` CLI. Missing pieces degrade gracefully — the orchestrator plays the missing role itself and says so.

## Use it

> "This is too big for one pass — orchestrate it across a model team."
> "Fan this out: research all 12 competitors in parallel and synthesize."
> "Run the advisor-worker loop on this."

The run ends with the deliverable, the plan, a per-subtask verification ledger, advisor notes applied and rejected, and remaining risks.

## Files

```
advisor-executor-worker/
├── SKILL.md                          # the orchestrator's loop, team, budgets, escalation rules
├── README.md                         # this file
├── references/worker-brief.md        # the stateless dispatch format workers receive
└── references/advisor-consult.md     # the consult format the advisor answers in
```

Evals live repo-side in `awesome_agent_skills/evals/advisor-executor-worker/` — you install only what runs.

Part of [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) · Apache-2.0 · Last verified: July 2026
