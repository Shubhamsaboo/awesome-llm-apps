# 🧵 Code Memory Agent

A Streamlit chat app that answers questions about your codebase and remembers the lessons your team teaches it. Ask where something is defined, who calls it or what a change touches. Tell it a rule ("`charge()` must run inside a transaction"), and the next question about that file, in any later session, comes back with the rule.

One agent, built with the [Strands Agents SDK](https://strandsagents.com), talks to one self-hosted MCP server:

| MCP server | Used for | Needs |
|---|---|---|
| [ClickHouse Loom](https://github.com/ClickHouse/loom) (`http://localhost:7777/mcp`) | A code index of your repository (definitions, callers, impact, search by meaning) and memories linked to the code they describe | A Loom install with your repository indexed. Apache-2.0, runs on your machine with Docker |

## What it does

- **Code questions:** "Where is `parse_config` defined?", "Who calls `charge`?", "What breaks if I change `Order.total`?" Answers cite `file:line` from the index.
- **Lessons:** "Remember: `charge()` must run inside a transaction." The agent saves the lesson in the repository's code namespace with the files it is about.
- **Recall:** before answering about a file, the agent reads the lessons saved about it and quotes the ones that apply, with their keys.

Loom links each lesson to the definitions it names in backticks and follows them as the code moves, is renamed or changes ([memories linked to code](https://clickhouse.github.io/loom/concepts/memory/#memories-linked-to-code)).

## Setup

You need Python 3.10+, Docker with Compose 2.20 or later, and an Anthropic API key.

1. Install Loom and index your repository. The [quickstart](https://clickhouse.github.io/loom/getting-started/quickstart/) boots the stack with one command, and [Index a repository](https://clickhouse.github.io/loom/getting-started/quickstart/#optional-index-a-repository-on-the-released-stack) adds your repository under a code namespace such as `code-myrepo`.
2. Run the app:

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...     # or type it in the sidebar
export LOOM_CODE_NAMESPACE=code-myrepo  # or type it in the sidebar
streamlit run code_memory_agent.py
```

3. In the sidebar, check the Loom server URL. Leave **Loom token** empty on the stock single-user install. On a deployment with sign-in, use a token that can write to the code namespace (`LOOM_API_KEY` also fills it).

## How it works

```
 chat ──> one Strands Agent ──> Loom MCP (/mcp?toolset=coding)
                                   │
            ┌──────────────────────┼─────────────────────────┐
     loom_code_symbol        loom_memory_set           loom_op → memory.for_file
     loom_code_callers       (save a lesson with       (the lessons saved
     loom_code_impact         the files it names)       about a file)
     loom_code_search
```

- `loom_client()` connects to Loom's MCP endpoint with the coding toolset and the token as a bearer header. `tool_filters` allow-list six tools; Loom serves more on the same connection.
- `build_agent()` returns a plain Strands `Agent` holding that client. The conversation stays in the agent between messages, and the status line shows which tools each answer used.
- `SYSTEM_PROMPT` tells the agent to pass the code namespace on every call, to report only what the tools returned, and to save a lesson only when you state one.

## Adapt it

- **Use another model provider:** `build_model()` is the only place that picks the provider. Return a different Strands model, for example `OpenAIModel(model_id=...)` from `strands.models.openai` (install `strands-agents[openai]`), and update the sidebar label.
- **Keep lessons per person:** save them in your own namespace instead of the code namespace, and tag them `repo:<id>` so Loom still links them to the code.
- **Use it from another agent:** import `build_agent()` from this file; the Streamlit code is only in `main()`.

## Limits

- The agent knows the code as of the last indexed commit. Uncommitted changes are not in the index.
- A lesson is linked to the code by a background worker, a few seconds after it is saved.
- Lessons are saved as the agent words them. Read the reply: it names the key, and you can fix or delete a lesson in the Loom dashboard.
