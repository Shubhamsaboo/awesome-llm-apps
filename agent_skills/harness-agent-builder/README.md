# Harness Agent Builder

An agent skill that turns "build me an agent that X" into a working, durable
backend agent on an engine of reusable workers, where the agent loop,
streaming, transcripts, model routing, scheduling, and REST come from
installed workers instead of application code.

Give your coding agent this skill and it knows how to:

- Stand up the engine and the harness worker set, and verify them before
  writing code
- Scaffold a one-file Node agent (`scripts/scaffold_agent.py`, offline and
  deterministic) that registers `<name>::run` on the bus, wires the
  completed-turn listener, and binds a cron or HTTP trigger
- Resolve models at runtime from the router catalog instead of hardcoding
  one; provider keys stay in the router worker, never in code
- Grant the agent functions (`web::fetch`, sub-agent spawning, ...) through
  the harness's fail-closed allow list, including the sub-agent subset rule
- Debug the wire with field-tested gotchas: unordered event delivery,
  fast-reply streaming, oversized-transcript failures, zombie workers

## Install

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/harness-agent-builder
```

Then ask your coding agent things like:

```text
Build a durable agent that checks my RSS feeds every morning and writes
a digest.
```

```text
Wire my summarizer script into the harness so other agents can call it.
```

## Layout

```
harness-agent-builder/
├── SKILL.md                     # The workflow: verify, decide, scaffold, customize, test
├── scripts/scaffold_agent.py    # Deterministic generator: agent.js + package.json
└── references/
    ├── wire-contracts.md        # Turn-loop send / completed / spawn schemas
    ├── gotchas.md               # Field-tested failure modes and fixes
    └── workers.md               # Dependency workers and what each provides
```

The scaffolder makes no network calls and refuses to overwrite existing
files. Workers on the bus are language-agnostic (the installed ones are
mostly Rust); the scaffolded business-logic worker uses the Node SDK, so it
needs Node 20+ and a running engine with the harness worker. SKILL.md walks
through both.
