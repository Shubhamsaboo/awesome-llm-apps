# 🔬 AI Deep Research Agent (LangGraph)

An AI-powered multi-agent research assistant built with **LangGraph** and **Streamlit** that turns a single query into a structured, cited research report — with human-in-the-loop plan approval and parallel web researchers.

## Features

- 🧠 **Planner Agent** — Generates a Problem Statement plus up to 5 independent research sub-tasks
- 👤 **Human-in-the-Loop Approval** — Review and revise the research plan in natural language before execution (LangGraph `interrupt`)
- 🔎 **Parallel Research Workers** — Up to 5 researchers fan out simultaneously via LangGraph's `Send()` API, each searching the web with Tavily
- 📊 **Aggregator Agent** — Synthesizes all findings into a publication-ready markdown report and auto-generates 1-3 matplotlib charts (embedded as base64 images)
- 🖥️ **Streamlit UI** — Sidebar API key configuration, live progress, markdown report with inline charts, and one-click `.md` download
- ✅ **Query Validation** — Rejects vague or inappropriate queries before hitting the LLM

## How to Run

1. **Clone the repository**

   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/multi_agent_apps/ai_deep_research_agent_langgraph
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**

   ```bash
   streamlit run app.py
   ```

> **LLM & Search Configuration:** Enter your credentials in the app sidebar, or add them to a `.env` file (see `.env.example`). The app supports DeepSeek, OpenAI, Anthropic, or any OpenAI-compatible custom endpoint:
>
> ```
> # LLM configuration
> LLM_API_KEY=your_key_here
> LLM_BASE_URL=https://api.deepseek.com
> MODEL_FAST=deepseek-v4-flash
> MODEL_PRO=deepseek-v4-pro
> 
> # Search Service
> TAVILY_API_KEY=your_key_here
> ```

## How It Works

```
Query → Validator → Planner (PS + sub-tasks) → HITL Approval → Parallel Researchers → Aggregator → Report
```

1. **Query Validator** checks that the query is a specific, safe research topic.
2. **Planner Agent** (structured output) writes a Problem Statement and up to 5 independent sub-tasks.
3. **Plan Approval** pauses the graph with a LangGraph `interrupt` and asks you to approve the plan or request revisions in natural language. Revisions loop back to the planner; approval continues.
4. **Parallel Researchers** fan out through LangGraph's `Send()` API — one branch per sub-task — each running a Tavily search-tool loop and producing a cited summary.
5. **Aggregator Agent** (tool-calling) synthesizes every research section into a cohesive markdown report, generating 1-3 matplotlib charts when the data supports them, and lists all cited sources.

Session checkpoints are persisted with LangGraph's in-memory `MemorySaver`, so the interrupt position survives Streamlit reruns.

## Usage

1. Launch the app with `streamlit run app.py`.
2. Enter your LLM provider configuration and Tavily API keys in the sidebar (or configure `.env`).
3. Type a research query, optionally filter search topics (News / Academic / Finance / Patents), and click **Start Research**.
4. Review the proposed plan and problem statement.
5. Click **Approve & Start Research**, or type a revision request (e.g. "add a trend analysis step") and click **Revise Plan**.
6. Watch the parallel researchers complete, then read or download the final report with charts and citations.

## Example Use Cases

- **Market Research** — competitive landscape, trends, and industry outlooks
- **Academic Research** — literature exploration across disciplines
- **Technology Evaluation** — emerging tech, benchmarks, and adoption barriers
- **Policy Analysis** — recent developments and their implications

## Technical Details

| Layer | Technology |
|---|---|
| Agent Graph | LangGraph (`Send()` fan-out, `interrupt` HITL, `MemorySaver`) |
| LLM | Configurable (defaults to `deepseek-v4-flash` / `deepseek-v4-pro`, supports OpenAI, Anthropic, or custom endpoints) |
| Web Search | Tavily API |
| Charts | Matplotlib (embedded base64 PNG data URIs) |
| UI | Streamlit |

## Dependencies

- langgraph
- langchain / langchain-core / langchain-openai
- tavily-python
- pydantic
- python-dotenv
- streamlit
- matplotlib

## License

This project is part of the awesome-llm-apps collection and is available under the Apache-2.0 License.
