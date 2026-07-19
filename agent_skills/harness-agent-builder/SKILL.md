---
name: harness-agent-builder
description: >-
  Scaffolds and wires durable backend agents on a harness engine of reusable
  workers: engine and worker setup, turn-loop consumer code, completed-turn
  result handling, sub-agent spawning, cron and HTTP triggers, JSON output
  contracts, and runtime model resolution through a model router. Use when
  the user wants to build an agent backend on a harness or worker engine,
  wants an always-on scheduled or webhook-driven agent without writing a
  server, asks to turn a script into a durable agent with triggers, or wants
  business logic callable by other agents and workers.
license: Apache-2.0
metadata:
  author: "Rohit Ghumare"
  version: "1.0.0"
  source: "https://github.com/Shubhamsaboo/awesome-llm-apps"
compatibility: >-
  The scaffolder is offline (Python 3.8+, stdlib). Workers on the engine bus
  are language-agnostic (the installed ones are mostly Rust binaries); the
  scaffolded business-logic worker uses the Node SDK and needs Node 20+, a
  local engine over WebSocket (ws://localhost:49134), and the harness worker
  installed. Model credentials live in the engine's model-router worker,
  never in the generated code.
---

# Harness Agent Builder

A durable agent is not a framework project. The engine this skill targets is
a bus: reusable workers register functions and triggers, and an agent is one
small worker of business logic that asks the `harness` worker to run turns
for it. Streaming, transcripts, model routing, durability, scheduling, and
HTTP all come from workers that are installed, not written. Language is
invisible on the bus: the installed workers are mostly Rust binaries, SDKs
exist for Rust, Python, Node, and the browser, and the function id is the
only contract; this skill scaffolds the business-logic worker in Node. The
concrete engine underneath is [iii](https://iii.dev); every command below
runs against it.

## When to use

- The user asks to build, scaffold, or wire an agent backend on a harness or
  worker engine
- The user wants an always-on agent that runs on a schedule or an HTTP route
  without writing a server
- The user has business logic and wants it callable by other agents and
  workers on the bus
- An existing harness consumer misbehaves (results never arrive, spawns
  missing, turns failing) and the wire contract needs checking

## When not to use

- Orchestrating multiple LLM CLIs or model teams without an engine
- Generic cron jobs or Express servers that call a model SDK directly
- Hand-writing a worker in another SDK language (Rust, Python, browser);
  the same wire contracts apply but this scaffolder emits Node

## Step 1: Confirm the environment

The user needs a running engine with the harness worker. If they do not have
one, point them at the install guide at https://iii.dev and have them run,
in an empty folder:

```bash
mkdir iii-app && cd iii-app
touch config.yaml
iii -c config.yaml
```

Then from a second terminal in the same folder:

```bash
iii worker add harness console
```

One add installs the whole loop: session-manager (transcripts),
context-manager (token budgeting), llm-router plus the Anthropic and OpenAI
providers (models), web (fetch), iii-state (storage), queue, and cron. The
console at http://localhost:3113 is where a provider key gets configured;
the key is stored in the llm-router worker, so generated agents never hold
credentials. `iii worker add http` is only needed for REST routes.

Verify before writing code. The engine is the source of truth:

```bash
iii trigger engine::functions::list prefix=harness::
iii trigger router::models::list
```

If `harness::send` is missing or the model list is empty, stop and fix that
first; nothing below will work.

## Step 2: Gather four decisions

Ask for whatever is not already clear from the request:

1. **Job**: one paragraph of what the agent does; this becomes the system
   prompt.
2. **Trigger**: callable function only (other workers and agents invoke it),
   `cron` (6-field expression: sec min hour day month weekday), or `http`
   (POST route via the http worker).
3. **Functions**: which function ids the agent may call while reasoning,
   e.g. `web::fetch`. Empty means a pure chat loop; the harness denies
   everything not allow-listed.
4. **Output**: free `text`, or `json` with a schema the turn result must
   validate against.

Never pick a model for the user. The generated code resolves the model at
runtime from `router::models::list`, auto-selects only when exactly one
tool-capable model exists, and otherwise asks for an env override. Any
configured provider works.

## Step 3: Scaffold

Run from this skill directory:

```bash
python3 scripts/scaffold_agent.py \
  --name radar \
  --prompt "You are a dependency analyst. Read changelogs and grade risk." \
  --trigger cron --cron "0 0 9 * * *" \
  --allow web::fetch \
  --output json \
  --dir ./radar-agent
```

The scaffolder is offline and deterministic, refuses to overwrite existing
files, and emits `agent.js` plus `package.json`. The generated worker
registers `<name>::run` on the bus, wires the turn-completed listener, and
binds the requested trigger.

## Step 4: Customize the business logic

The generated file is a starting point, deliberately small. Typical edits:

- Replace the `OUTPUT_SCHEMA` stub with the real result shape
- Add deterministic pre-work in plain code before `harness::send` (read
  files, diff versions, build the task string); do not spend tokens on
  arithmetic
- Store results with `state::set { scope, key, value }` so other workers can
  read them
- For multi-agent behavior, add `harness::spawn` to the allow list and
  instruct spawning in the system prompt; read
  [references/wire-contracts.md](references/wire-contracts.md) first for the
  subset-policy rule

## Step 5: Verify against a live engine

```bash
cd <output-dir> && npm install
node agent.js "a small real task"
```

Watch the run as one correlated trace in the console at
http://localhost:3113. Then check the wire directly:

```bash
iii trigger <name>::run task="a small real task"
```

A turn that fails with `session::messages` or `invocation_stopped` errors,
results that never arrive, or spawns that seem missing are almost always one
of the documented wire gotchas; read
[references/gotchas.md](references/gotchas.md) before debugging blind.

## The contract in one paragraph

`harness::send { message, model, session_id?, options }` starts a durable
turn and returns `{ session_id, turn_id }` immediately. The result rides the
`harness::turn-completed` trigger as `{ session_id, turn_id, status,
result?, result_error? }`; consumers bind it and correlate by session or
turn id, never poll. `options.functions.allow` is fail-closed; `options.output`
constrains the result to text or schema-validated JSON; `session_id` reuse
is multi-turn memory. Full request and response shapes, the spawn subset
rule, and event-ordering guarantees are in
[references/wire-contracts.md](references/wire-contracts.md); dependency
workers and what each provides are in
[references/workers.md](references/workers.md).
