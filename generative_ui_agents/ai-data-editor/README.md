# AI Data Editor

Ask any question about your data in natural language. Get a live view from a real database. Edit inline — the agent generates the SQL, you confirm every write.

**Gen UI concept — agent as data layer.** Every dashboard is a set of pre-translated questions: someone decided what you can ask and how the answer comes back. This project removes the middleman. The agent sits between you and the database, translating intent to SQL in both directions — reads to render, writes to persist. Human-in-the-loop isn't decorative here; it's the trust model that makes writes possible at all.

---

## How It Works

1. **Ask a question** — "Show me all enterprise accounts with MRR over $5,000"
2. **Agent generates SQL** — translates natural language to a SELECT query
3. **Generative UI renders results** — the frontend picks the right component (table, card, or metrics) based on the data shape
4. **Edit inline** — "Change Acme Corp's status to Churned"
5. **Agent proposes the mutation** — generates an UPDATE, shows you the SQL and a before/after diff
6. **You confirm or reject** — the write only executes after explicit approval
7. **Database updates** — agent runs the parameterized query and re-renders the updated row

## Trust Model

Reads are open — the agent generates SELECT queries against a read-only database connection. Writes are gated:

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
| Database | SQLite (seeded with 50 SaaS accounts, usage metrics, invoices) |
| LLM | OpenAI (configurable via env) |
| Protocol | AG-UI (state streaming) |

### CopilotKit Features

- **Generative UI** — the frontend picks DataTable, SummaryCard, or MetricRow based on query result shape. MutationPreview renders for write confirmations. (A2UI declarative rendering is scaffolded but not yet wired up.)
- **Shared State** — query results and pending mutations sync bidirectionally between agent and UI via `useAgent`.
- **Human-in-the-Loop** — structural, not decorative. The two-step write flow (propose → confirm → execute) maps directly to CopilotKit's interrupt model.
- **AG-UI Protocol** — standard agent-to-UI communication. Swap the database backend without touching the frontend.

## Prerequisites

- Node.js 20+
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (or pip) for Python deps
- [OpenAI API Key](https://platform.openai.com/api-keys)

## Getting Started

1. Install dependencies:

```bash
cd generative_ui_agents/ai-data-editor
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
- "Show me all enterprise accounts with their MRR and status"
- "Which accounts have overdue invoices?"
- "What's the average MRR by account type?"
- "Show me the top 10 accounts by API call usage in May 2026"

**Writes:**
- "Change Acme Corp's status to Churned"
- "Update the CSM for account 12 to Sarah Chen"
- "Set the MRR for HighFive to 8500"

## Seed Data

The demo database contains:
- **50 accounts** with name, type (Enterprise/Scale/Startup/Free), owner, CSM, status, MRR, and Salesforce ID
- **~740 usage rows** tracking API calls, storage, seats, and bandwidth across 5 months
- **~200 invoices** with amounts, statuses (Paid/Overdue/Draft/Void), and due dates

Data is seeded deterministically (fixed random seed) so the demo is reproducible.

## Using Your Own Database

The demo runs on SQLite with sample data. To connect to a real database:

1. Edit `agent/src/db.py` — swap the SQLite connection for your database (Postgres, MySQL, etc.)
2. Update `get_schema_context()` to introspect your schema
3. Remove or adjust `agent/src/seed.py`

The agent, trust model, and UI all work the same regardless of the database backend. The SQL generation adapts to whatever schema you provide.

## Built With

- [CopilotKit](https://github.com/CopilotKit/CopilotKit) — The frontend stack for agents & generative UI
- [AG-UI](https://github.com/ag-ui-protocol/ag-ui) — Agent-User Interaction protocol
- [LangGraph](https://www.langchain.com/langgraph) — Agent orchestration framework
