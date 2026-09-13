# Learning Plan — Awesome LLM Apps (OpenRouter, free models)

Goal: learn the repo hands-on using OpenRouter free models only. No paid OpenAI calls.
Branch: `feature/learn-openrouter` on https://github.com/tushar-hatwar/awesome-llm-apps_test
Rule: every agent gets venv + OpenRouter conversion + run + notes here.

## How to run anything here
```powershell
cd <agent-folder>
# first time only
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
# every run (CLI agents)
$env:PYTHONUTF8="1"
$env:OPENROUTER_API_KEY="sk-or-your-key-here"
.\venv\Scripts\python.exe <agent-file>.py
# every run (Streamlit agents)
.\venv\Scripts\python.exe -m streamlit run <app-file>.py --server.port <port>
```
Free-model notes: list at https://openrouter.ai/models?max_price=0 changes often.
`openrouter/free` auto-router is the most resilient default. Limits ~20 req/min.

## Progress

### Phase 1 — Starter agents (in progress)
- [x] `starter_ai_agents/ai_travel_agent/` — DONE (run on :8501)
  - OpenAIChat → OpenRouter, free-model selectbox (`travel_agent.py`).
  - Learned: Agent `description` (who it is) vs `instructions` (steps),
    Researcher → Planner sequential chaining, `SerpApiTools`, Streamlit `session_state`.
- [x] `starter_ai_agents/ai_reasoning_agent/` — DONE (CLI run)
  - OpenAIChat → OpenRouter via `$env:OPENROUTER_API_KEY`, default `openrouter/free`.
  - Fixed for agno 3.x: `reasoning=True` no longer exists → `tools=[ReasoningTools(...)]`.
  - Learned: thinking (tool-traced, 13.8s, auditable) vs non-thinking (direct, 6.5s);
    use thinking for multi-step/constraints, regular for simple facts.
- [x] `starter_ai_agents/web_scraping_ai_agent/` — DONE (scrape tested)
  - OpenAI gpt-4o/gpt-5 → OpenRouter via `ChatOpenAI(model_instance)` + free selectbox (`ai_scrapper.py`).
  - Installed Playwright Chromium. Launched on :8502, ran a real scrape successfully.
  - Learned: ScrapeGraphAI builds LLM via langchain `init_chat_model`; `model_instance`
    escape hatch lets any OpenAI-compatible endpoint (OpenRouter) plug in.
- [ ] `starter_ai_agents/mixture_of_agents/` — NEXT
- [ ] `starter_ai_agents/openai_research_agent/` — queued

### Phase 2 — Core skills (not started)
- [ ] `rag_tutorials/` — retrieval grounding (fixes hallucination seen in travel agent)
- [ ] `advanced_llm_apps/chat_with_X_tutorials` + `llm_apps_with_memory_tutorials`
- [ ] `ai_agent_framework_crash_course/`

### Phase 3 — Specialize (not started)
- [ ] `advanced_ai_agents/`
- [ ] `mcp_ai_agents/` and/or `voice_ai_agents/` (pick one track)

## Log
- 2026-09-11: travel agent on OpenRouter free models, ran :8501.
- 2026-09-13: reasoning agent converted + run (regular vs reasoning compared).
- 2026-09-13: fork `tushar-hatwar/awesome-llm-apps_test`, branch `feature/learn-openrouter`, pushed.
- 2026-09-13: web scraper converted + launched :8502, pushed. All servers stopped, logs cleaned.
- 2026-09-13: scrape tested OK. `LEARNING_PLAN.md` created to track progress.
