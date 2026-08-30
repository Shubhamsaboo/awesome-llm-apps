# ⚡ Codebase Migration & Refactor Planner (LangGraph)

An AI-powered multi-agent codebase migration assistant built with **LangGraph** and **Streamlit** that plans file-by-file refactoring tasks, performs human-in-the-loop (HITL) risk review, fans out parallel refactoring workers, and aggregates complete diffs with visual risk charts.

## Features

- 🧠 **Planner Agent** — Analyzes a repository target and migration goal to generate an architectural strategy plus a file-by-file migration plan with risk levels (`Low`, `Medium`, `High`, `Critical`).
- 🛡️ **Human-in-the-Loop Approval Gate** — Pause execution via LangGraph `interrupt()` so engineers can inspect, review, and modify risk levels or file scopes in natural language before any code changes occur.
- 🛠️ **Parallel Refactor Workers** — Fan out simultaneously via LangGraph's `Send()` API — one worker per file in the plan — generating precise code diffs, breaking changes analysis, and recommended test cases.
- 📊 **Aggregator Agent** — Synthesizes all file diffs into a publication-ready Migration Guide & Report, auto-generating 1-2 data-driven matplotlib charts (embedded as base64 images).
- 🖥️ **Streamlit UI** — Sidebar API configuration, risk badges, interactive revision controls, markdown report rendering with embedded charts, and one-click `.md` download.
- ✅ **Query Validation** — Validates repository inputs and migration goals to block empty, unsafe, or destructive prompts before hitting LLMs.

## How to Run

1. **Clone the repository**

   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/advanced_ai_agents/multi_agent_apps/ai_codebase_migration_agent
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**

   ```bash
   streamlit run app.py
   ```

> **LLM Configuration:** Add your key to a `.env` file (see `.env.example`) or enter it in the app sidebar:
>
> ```env
> OPENAI_API_KEY=sk-your-key-here
> ```
>
> Defaults to `gpt-5-mini` for planning and the per-file workers, and `gpt-5.5` for the final report synthesis. Override with `MODEL_FAST` / `MODEL_PRO`, or point at any OpenAI-compatible provider by also setting `LLM_BASE_URL`.

## How It Works

```
Repo Target + Goal → Validator → Planner (Strategy + File Tasks) → HITL Approval → Parallel Refactor Workers → Aggregator → Migration Guide & Diffs
```

1. **Query Validator** verifies that both a valid repository path/URL and a substantive migration goal are provided.
2. **Planner Agent** (structured output) formulates a high-level migration strategy and breaks down changes into 3–6 file migration tasks with estimated risk levels.
3. **Plan Approval Gate** pauses the graph using LangGraph's `interrupt()` API to let developers review the risk matrix, request revisions in natural language, or approve execution.
4. **Parallel Refactor Workers** fan out via `Send()` API calls — one branch per file — to produce unified diffs, before/after snippets, and test cases.
5. **Aggregator Agent** synthesizes all refactoring diffs into a comprehensive report, chooses chart data (not executable code), renders visual risk charts using trusted Matplotlib templates, and outlines post-migration validation steps.

Session state is persisted using LangGraph's in-memory `MemorySaver`, allowing execution interrupts to survive Streamlit reruns seamlessly.

## Example Use Cases

- **Framework & Library Upgrades** — e.g. Pydantic v1 → v2 (`BaseModel`, `@validator` to `Field`, `@field_validator`), Flask 2 → 3, SQLAlchemy 1.4 → 2.0.
- **Language / Syntax Conversions** — e.g. Converting JavaScript files (`.js`) to TypeScript (`.ts`) with strict interfaces.
- **Async & Performance Refactoring** — e.g. Converting synchronous I/O and database handlers to `async`/`await`.
- **Deprecation Cleanups** — Replacing deprecated API patterns across multiple services safely.

## Technical Details

| Layer | Technology |
|---|---|
| Agent Graph | LangGraph (`Send()` fan-out, `interrupt()` HITL, `MemorySaver` checkpointer) |
| LLMs | Configurable (defaults: `gpt-5-mini` for fast steps, `gpt-5.5` for synthesis) |
| Charts | Validated data rendered by trusted Matplotlib templates (embedded base64 PNG data URIs) |
| UI | Streamlit |

## Dependencies

- `langgraph`
- `langgraph-checkpoint`
- `langchain` / `langchain-core` / `langchain-openai`
- `pydantic`
- `python-dotenv`
- `streamlit`
- `matplotlib`

## License

This project is part of the awesome-llm-apps collection and is available under the Apache-2.0 License.
