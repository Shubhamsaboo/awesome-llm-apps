# AI Deep Research Agent

A deep research assistant that plans, searches the web, writes to a virtual filesystem, and renders each tool call as a live card in a workspace pane. Built with [CopilotKit](https://github.com/CopilotKit/CopilotKit), [Deep Agents](https://docs.copilotkit.ai/integrations/langgraph/deep-agents), [AG-UI](https://github.com/ag-ui-protocol/ag-ui), and [Tavily](https://www.tavily.com/) on top of Next.js + LangGraph (Python).

https://github.com/user-attachments/assets/68d5729f-91f9-4fd9-a579-cd1a8f4aad8d

**Gen UI concept — tool-rendered components with a sidecar workspace.** The Deep Agent emits four tools — `write_todos`, `write_file`, `read_file`, and `research` — and each one renders inline as a status card in the chat while updating a parallel workspace pane (plan, files, expandable tool results). Local React state mirrors the agent's filesystem via `useDefaultTool` rather than `useCoAgent`, sidestepping a Python `Dict` ↔ TypeScript `Array` type mismatch.

## Prerequisites

- Node.js 18+
- Python 3.12+
- [OpenAI API Key](https://platform.openai.com/api-keys)
- [Tavily API Key](https://app.tavily.com/home)
- [uv](https://docs.astral.sh/uv/) (or pip) for Python deps

## Getting Started

1. Install Node dependencies:

```bash
npm install
```

2. Install Python dependencies for the agent:

```bash
cd agent
uv venv && source .venv/bin/activate
uv pip install -e .
cd ..
```

Or with pip:

```bash
cd agent
python -m venv .venv && source .venv/bin/activate
pip install -e .
cd ..
```

3. Copy `.env.example` to `.env` in both the root and `agent/` directories, then fill in `OPENAI_API_KEY` and `TAVILY_API_KEY`.

4. Start the agent (terminal 1):

```bash
cd agent
uv run python main.py
```

5. Start the frontend (terminal 2):

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and ask the assistant to research any topic.

## Architecture

```
[User asks research question]
        ↓
Next.js Frontend (CopilotChat + Workspace)
        ↓
CopilotKit Runtime → LangGraphHttpAgent
        ↓
Python Backend (FastAPI + AG-UI)
        ↓
Deep Agent (research_assistant)
    ├── write_todos        (planning, built-in)
    ├── write_file         (filesystem, built-in)
    ├── read_file          (filesystem, built-in)
    └── research(query)
            └── internal Deep Agent [thread-isolated]
                    └── internet_search (Tavily)
```

## Environment Variables

| Variable                   | Required | Default                 | Description                                         |
| -------------------------- | -------- | ----------------------- | --------------------------------------------------- |
| `OPENAI_API_KEY`           | Yes      | -                       | [Get API key](https://platform.openai.com/api-keys) |
| `TAVILY_API_KEY`           | Yes      | -                       | [Get API key](https://app.tavily.com/home)          |
| `OPENAI_MODEL`             | No       | `gpt-5.5`               | Model to use (`gpt-5.5`)                            |
| `LANGGRAPH_DEPLOYMENT_URL` | No       | `http://localhost:8123` | Backend URL                                         |
| `SERVER_HOST`              | No       | `0.0.0.0`               | Backend host                                        |
| `SERVER_PORT`              | No       | `8123`                  | Backend port                                        |

## Learn more

- [Deep Agents documentation](https://docs.copilotkit.ai/integrations/langgraph/deep-agents)
- [Building Frontends for Deep Agents](https://www.copilotkit.ai/blog/how-to-build-a-frontend-for-langchain-deep-agents-with-copilotkit)
- [CopilotKit documentation](https://docs.copilotkit.ai)
- [Tavily documentation](https://docs.tavily.com/welcome)

## License

Upstream license applies — see [`CopilotKit/CopilotKit`](https://github.com/CopilotKit/CopilotKit).
