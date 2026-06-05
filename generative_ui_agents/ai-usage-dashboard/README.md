# AI Usage Dashboard

Ask any question about your usage data in natural language. Get a live dashboard from a real database. Edit values inline or via chat -- the agent generates the SQL, you confirm every write.

**Gen UI concept -- agent as data layer.** Every dashboard is a set of pre-translated questions: someone decided what you can ask and how the answer comes back. This project removes the middleman. The agent sits between you and the database, translating intent to SQL in both directions -- reads to render, writes to persist. Human-in-the-loop isn't decorative here; it's the trust model that makes writes possible at all.

---

## How It Works

1. **Ask a question** -- "Show me my usage this month" or "How many tokens did I use on gpt-4o?"
2. **Agent generates SQL** -- translates natural language to a SELECT query
3. **Canvas renders results** -- the `CanvasDashboard` component picks the right layout (table, metric cards, grouped summary, detail card) based on the data shape via agent state
4. **Edit inline or via chat** -- click a field to edit, or type "Change my plan to Team"
5. **Agent proposes the mutation** -- generates an UPDATE, shows you the SQL and a before/after diff
6. **You confirm or reject** -- the write only executes after explicit approval
7. **Database updates** -- agent runs the parameterized query and re-renders the updated row

## Trust Model

Reads are open -- the agent generates SELECT queries against a read-only database connection. Writes are gated:

- **Statement allowlist**: only UPDATE and INSERT. No DELETE, DROP, ALTER, or TRUNCATE.
- **Primary key scoping**: every UPDATE must include a WHERE clause targeting a specific row.
- **Parameterized queries**: values are never interpolated into SQL strings.
- **Diff preview**: before execution, you see the table, row, column, old value, and new value.
- **Human-in-the-loop**: every write requires your explicit confirmation.

## Architecture

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, TailwindCSS 4 |
| Agent | LangGraph (Python), CopilotKit Middleware |
| Database | SQLite (1 account, ~137K usage events, 6 invoices, 3 entitlements, 2 alerts) |
| LLM | OpenAI (configurable via env) |
| Protocol | AG-UI (state streaming) |

### CopilotKit Features

- **State-Driven Rendering** -- agent state (`query_result`, `pending_mutation`) drives the canvas via `useAgent`. The `CanvasDashboard` component renders tables, metric cards, grouped summaries, or detail cards based on the query result shape.
- **Shared State** -- query results and pending mutations sync bidirectionally between agent and UI via `useAgent`.
- **Human-in-the-Loop** -- structural, not decorative. The two-step write flow (propose -> confirm -> execute) uses `useHumanInTheLoop` to gate every mutation.
- **AG-UI Protocol** -- standard agent-to-UI communication. Swap the database backend without touching the frontend.

## Prerequisites

- Node.js 18+
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (or pip) for Python deps
- [OpenAI API Key](https://platform.openai.com/api-keys)

## Getting Started

1. Install dependencies:

```bash
cd generative_ui_agents/ai-usage-dashboard
npm install
```

2. Set your API key:

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=...
```

3. Start the app:

```bash
npm run dev
```

This starts both the Next.js frontend (port 3000) and the LangGraph agent (port 8123). The database is automatically seeded on first run.

## Example Prompts

**Reads:**
- "Show me my usage this month"
- "How many tokens did I use on gpt-4o?"
- "What's my total cost by model?"
- "Show me all invoices"
- "Am I close to any usage limits?"

**Writes:**
- "Update my company email to team@acme.com"
- "Change the 90% alert threshold to 85%"

## Seed Data

The demo database contains:
- **1 account** (Acme AI, Pro plan)
- **~137K usage events** tracking token usage across 5 models (gpt-4o, gpt-4o-mini, claude-sonnet-4, claude-haiku, gemini-2.5-flash) over 6 months
- **6 invoices** with base + overage billing
- **3 entitlements** (ai_completions, document_processing, custom_models)
- **2 alerts** (80% and 90% thresholds on ai_completions)

Data is seeded deterministically (fixed random seed) so the demo is reproducible.

## Using Your Own Database

The demo runs on SQLite with sample data. To connect to a real database:

1. Edit `agent/src/db.py` -- swap the SQLite connection for your database (Postgres, MySQL, etc.)
2. Update `get_schema_context()` to introspect your schema
3. Remove or adjust `agent/src/seed.py`

The agent, trust model, and UI all work the same regardless of the database backend. The SQL generation adapts to whatever schema you provide.

## Built With

- [CopilotKit](https://github.com/CopilotKit/CopilotKit) -- The frontend stack for agents & generative UI
- [AG-UI](https://github.com/ag-ui-protocol/ag-ui) -- Agent-User Interaction protocol
- [LangGraph](https://www.langchain.com/langgraph) -- Agent orchestration framework
