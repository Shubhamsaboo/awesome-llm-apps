# 🔭 AI Deep Research Agent Team with iii

A multi-agent deep research team built on the [iii engine](https://iii.dev). One orchestrator agent receives a research question, decides on its own how many researcher sub-agents the question needs, spawns them in parallel, cross-checks their findings against each other, and returns a JSON report where every key finding is backed by a URL a researcher actually fetched.

The interesting part is what this app does NOT contain. There is no agent framework, no LLM client, no API key handling, no HTTP server, and no database driver. The iii engine acts as a bus: every capability is a reusable worker that communicates through functions and triggers, and this app is one file of business logic that plugs into them.

| Capability | Who provides it |
|---|---|
| Agent loop (context, streaming, function dispatch, sub-agents) | `harness` worker |
| Model access (Anthropic, OpenAI, xAI, local llama.cpp, ...) | `llm-router` + `provider-*` workers |
| Web reading for researchers | `web` worker (`web::fetch`) |
| Report storage | `iii-state` worker (`state::set` / `state::get`) |
| REST endpoints (optional) | `http` worker |
| Tracing (every turn, spawn, and provider call as one waterfall) | iii console |

## How It Works

1. `research::start` sends one message to `harness::send` with a JSON output contract and a function policy that allows exactly two functions: `harness::spawn` and `web::fetch`.
2. The orchestrator model plans the research angles and calls `harness::spawn` once per angle. The number of researchers is the model's decision, based on the breadth of the question, not a hardcoded constant.
3. Each spawn parks the orchestrator turn until the child session resolves. Children run in parallel, each in its own session, and inherit only the functions the parent grants them (`web::fetch`, and deliberately not `harness::spawn`, so researchers cannot spawn more agents).
4. Researchers read pages with `web::fetch` in markdown mode and report back with citations.
5. The orchestrator cross-checks the researchers' findings, spawns a tie-breaker researcher if two of them disagree, and emits the final report as schema-validated JSON.
6. The app hears `harness::turn-completed`, stores the report in state, and resolves the caller.

Open the iii console at `http://localhost:3113` during a run to watch the whole tree live: the orchestrator turn, each researcher session, and every provider call in one correlated trace.

## Requirements

- Node.js 20+
- The iii engine with the `harness` worker
- At least one model provider configured in `llm-router`

The app itself holds no API keys. Credentials live in the `llm-router` worker, so any provider you configure there (Anthropic, OpenAI, xAI, a local model through llama.cpp) is available to the team without touching this code.

## Installation

Install and start the iii engine:

```bash
curl -fsSL https://install.iii.dev/iii/main/install.sh | sh
mkdir iii-app && cd iii-app
touch config.yaml
iii -c config.yaml
```

Add the harness from a second terminal in the same folder (this pulls every worker the loop needs: session-manager, context-manager, llm-router, web, state, queue, cron, and more):

```bash
cd iii-app
iii worker add harness console
```

Open `http://localhost:3113`, click the model picker, and configure a provider key. Then install the app:

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_ai_agents/multi_agent_apps/agent_teams/ai_deep_research_agent_team_iii
npm install
```

## Usage

Ask a question from the CLI:

```bash
node agent_team.js "Compare Bun and Deno in 2026: performance, Node.js compatibility, and production adoption."
```

The report prints as JSON:

```json
{
  "answer": "As of mid-2026, Bun (v1.3.14) and Deno (v2.9.3) have become mature alternatives to Node.js...",
  "key_findings": [
    "Deno's AWS Lambda cold starts are measurably faster than Node.js and Bun in Deno's own 2026 benchmarks...",
    "Bun's Node.js compatibility layer now passes the large majority of the Node test suite..."
  ],
  "sources": [
    { "url": "https://deno.com/blog/aws-lambda-coldstart-benchmarks", "title": "...", "used_for": "..." }
  ]
}
```

If several models are configured, pick one per run with `--model <id>` or set `RESEARCH_MODEL`. With a single configured model the app uses it automatically. The available ids come from `router::models::list`.

Run it as a resident worker instead, so other workers (or the console) can call it:

```bash
node agent_team.js --serve
```

In serve mode the app registers two functions on the bus: `research::start` (kick off a run, returns `{session_id}` immediately) and `research::report` (fetch the stored report by session id). If the `http` worker is installed (`iii worker add http`), the same functions are also exposed as REST endpoints:

```bash
curl -X POST http://localhost:3111/research \
  -H 'content-type: application/json' \
  -d '{"question": "What changed in React 20?"}'

curl http://localhost:3111/research/<session_id>
```

## Configuration

| Env var | Default | Meaning |
|---|---|---|
| `III_URL` | `ws://localhost:49134` | Engine WebSocket address |
| `RESEARCH_MODEL` | none | Model id; required only when several models are available |
| `RESEARCH_TIMEOUT_MS` | `600000` | Abort a run (and stop its turn) after this long |
