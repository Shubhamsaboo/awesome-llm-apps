# AI Knowledge Explorer

Drop files — documents or source code — into a chatbot. The agent extracts entities, concepts, and relationships (or modules, classes, functions, and dependencies), then renders an interactive knowledge graph you can explore.

Click a node to see details. Double-click to expand it — the agent extracts sub-concepts (or sub-components for code) and adds them to the graph. Ask questions in chat to navigate.

## How It Works

1. **Drop files** — drag documents (`.txt`, `.md`, `.json`, `.csv`) or code files (`.py`, `.ts`, `.js`, `.java`, `.go`, `.rs`, and more) onto the canvas
2. **Agent extracts** — the LLM identifies structure: entities and concepts for text, modules and functions for code
3. **Graph renders** — nodes and edges appear as the agent processes each file
4. **You explore** — click nodes, expand them, ask questions, steer the agent

## Architecture

- **Shared state**: The knowledge graph (nodes + edges) lives in agent state and syncs bidirectionally via CopilotKit v2
- **Generative UI**: Each tool call produces visible changes — new nodes, new edges, expanded detail
- **Human-in-the-loop**: Click to select, double-click to expand, chat to steer

### Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, TailwindCSS 4 |
| Agent | LangGraph (Python), CopilotKit Middleware |
| Graph | react-force-graph-2d |
| LLM | OpenAI (configurable via env) |
| Protocol | AG-UI (state streaming) |

## Prerequisites

- Node.js 18+
- Python 3.12
- [uv](https://docs.astral.sh/uv/) — the agent's Python dependencies are managed with uv, and `npm install` runs `uv sync` automatically. Install it with `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS/Linux) or `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` (Windows). uv fetches Python 3.12 for you if it isn't already installed.

## Setup

```bash
# 1. Install dependencies (also runs `uv sync` for the Python agent)
npm install

# 2. Set your API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Start the app
npm run dev
```

This starts both the Next.js frontend (port 3000) and the LangGraph agent (port 8125). On Windows the same `npm` scripts run the `.bat` equivalents under `scripts/`.

## Example Content

Two built-in example sets let you try both modes — click the buttons on the empty state to load them instantly.

**Documents** — 3 markdown files about AI agents:
- `what-are-agents.md` — defines agents, core components (LLM, tools, memory, planning)
- `agent-frameworks.md` — compares LangGraph, CrewAI, AutoGen, CopilotKit
- `agent-challenges.md` — hallucination, tool reliability, evaluation, cost, security

Expected graph: ~15-22 nodes, ~20-33 edges covering the AI agent ecosystem.

**Codebase** — 3 Python files forming a FastAPI auth system:
- `auth.py` — JWT token creation, password hashing, TokenService class
- `routes.py` — login, register, refresh endpoints, dependency injection
- `models.py` — SQLAlchemy User, Post, AuditLog models

Expected graph: ~20 nodes showing modules, classes, functions, and their imports/calls/extends relationships.

## Agent Tools

| Tool | Purpose |
|---|---|
| `extract_knowledge` | Parse documents or code, extract entities/concepts/relationships or modules/classes/functions |
| `find_connections` | Discover deeper links between existing nodes |
| `expand_node` | Deep-dive into a node — adds sub-concepts and detail |

## Project Structure

```
ai-knowledge-explorer/
├── agent/                    # Python LangGraph agent
│   ├── main.py               # Agent entry point
│   └── src/
│       ├── state.py           # KnowledgeState schema
│       └── tools.py           # extract, connect, expand tools
├── src/                       # Next.js frontend
│   ├── app/
│   │   ├── page.tsx           # Main page (chat + graph canvas)
│   │   ├── layout.tsx         # CopilotKit v2 provider
│   │   └── api/
│   │       ├── copilotkit/    # CopilotKit runtime route
│   │       └── upload/        # File upload endpoint
│   ├── components/
│   │   ├── KnowledgeGraph.tsx  # Force-directed graph visualization
│   │   ├── NodeDetail.tsx      # Detail panel on node select
│   │   └── ToolReasoning.tsx   # Tool call status indicators
│   ├── hooks/
│   │   ├── use-knowledge-ui.tsx
│   │   └── use-suggestions.tsx
│   └── lib/
│       ├── types.ts            # KnowledgeNode, KnowledgeEdge types
│       └── example-content.ts  # Built-in example documents and code
├── package.json
└── .env.example
```
