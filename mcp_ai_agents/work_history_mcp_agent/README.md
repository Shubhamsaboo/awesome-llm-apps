# Work-history retrieval through MCP

Learn a reusable pattern: expose an activity log through a small read-only MCP
server, apply explicit retrieval bounds, and ask a model to answer with source IDs.
The example runs with bundled fictional JSON data. No recorder, commercial
product, or account is needed for the local retrieval demo.

## What this teaches

1. Normalize records with an ID, timestamp, application, project, and text.
2. Expose one bounded search tool over stdio MCP.
3. Retrieve a project and time range before calling an LLM.
4. Preserve IDs, timestamps, result counts, and truncation information.
5. Separate observed actions, promises, missing evidence, and inference.

This uses deterministic retrieval followed by generation. It deliberately does
not let the model browse the filesystem or choose arbitrary tools. Search is
simple case-insensitive keyword matching, not vector search.

## Setup

Requires Python 3.10 or newer.

```bash
cd mcp_ai_agents/work_history_mcp_agent
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run locally without an LLM

```bash
python work_history_agent.py --inspect
python work_history_agent.py --inspect --search invitation
python -m unittest -v
```

The first command starts the MCP server as a child process, initializes the
protocol, and retrieves three Atlas records. Orion is excluded by the project
filter. The second retrieves two records containing “invitation”. The process
exits and closes the server after each query.

## Generate a grounded answer

```bash
cp .env.example .env
# Set OPENAI_API_KEY in .env, then:
python work_history_agent.py "What was promised, and has it shipped?"
```

A grounded answer should cite `evt-003` for the review commitment and state
that the log does not establish deployment. Model output is nondeterministic;
check its citations against the returned records. The example does not verify
claims automatically or prevent every prompt-injection attempt.

OpenAI is the default model provider. Set `OPENAI_BASE_URL`, `OPENAI_MODEL`, and
`OPENAI_API_KEY` for a compatible local endpoint. The retrieval demo needs no key.

## Use your own activity log

Set `ACTIVITY_FILE` to an absolute JSON path using the schema in `activity.json`.
IDs must be unique and timestamps must include a timezone. Set `--start`, `--end`,
and `--project` for your data; pass `--project ""` to search all projects.
The start bound is inclusive and the end bound is exclusive.

Possible sources include manually authored work logs, calendar exports, and
application events. Screenpipe is one optional capture source with a
[documented local API](https://docs.screenpi.pe/cli-reference) and
[MCP server](https://github.com/screenpipe/screenpipe/tree/main/packages/screenpipe-mcp).
A capture-source adapter must normalize its records to this example's schema;
this tutorial does not install or require Screenpipe.

## Limits and data flow

The MCP server reads only the configured JSON file and exposes no write tools.
The client retrieves at most 20 records, then sends those records and the
question to the configured LLM endpoint. Use `--inspect` to keep the demonstration
entirely local. For real data, remove unrelated private content before exporting.

A sparse log cannot establish exact time spent. The prompt tells the model not
to treat gaps between timestamps as durations. This example has no screenshots,
audio capture, embeddings, automatic ingestion, background monitoring, or
cross-user isolation. Add these only as separate, explicitly designed layers.
