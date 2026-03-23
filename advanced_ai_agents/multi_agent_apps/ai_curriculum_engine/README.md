# 📚 AI Curriculum Engine (Plot Ark)

An agentic multi-step pipeline that generates **pedagogically grounded course modules** using Bloom's Taxonomy, real academic sources, and a LightRAG knowledge graph.

## Features

- 🔍 **Research Agent** — Tavily searches for real academic papers, video lectures, and expert articles before generating anything
- 🕸️ **Knowledge Graph Agent** — LightRAG builds a per-course concept graph from retrieved sources using hybrid retrieval
- ✍️ **Curriculum Agent** — GPT-4o-mini generates structured modules with Bloom's Taxonomy-aligned objectives, resources, and assessments
- 🎯 **Level-aware** — Beginner/Intermediate/Advanced maps to Bloom's levels 1-2 / 3-4 / 5-6 automatically
- ⬇️ **Export** — Download full curriculum as JSON

## How It Works

```
User Input (topic + level + audience)
        │
        ▼
[Agent 1] Tavily Research
  → searches academic, video, news domains
  → returns up to 12 real, deduplicated sources
        │
        ▼
[Agent 2] LightRAG Knowledge Graph
  → ingests source content
  → builds entity-relationship graph per course
  → hybrid query extracts key concepts
        │
        ▼
[Agent 3] GPT-4o-mini Curriculum Generation
  → Bloom's Taxonomy constraints by level
  → grounded in real sources + graph context
  → outputs structured JSON (modules, objectives, resources, assessments)
        │
        ▼
Streamlit UI — module cards, source panel, JSON export
```

## Installation

```bash
# Clone the repo
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_ai_agents/multi_agent_apps/ai_curriculum_engine

# Install dependencies
pip install -r requirements.txt

# Set API keys (or enter them in the sidebar)
export OPENAI_API_KEY=your_openai_key
export TAVILY_API_KEY=your_tavily_key

# Run
streamlit run ai_curriculum_engine.py
```

## Usage

1. Enter your **OpenAI** and **Tavily** API keys in the sidebar
2. Fill in: course topic, target audience, learner level, number of modules
3. Click **Generate Curriculum**
4. Watch the three agents work in sequence
5. Download the result as JSON

## Example Output

**Topic:** Introduction to Machine Learning Ethics
**Level:** Intermediate | **Audience:** Undergraduate CS students | **Modules:** 5

| Module | Title | Bloom's Focus |
|--------|-------|---------------|
| 1 | Foundations of AI Ethics | Apply (L3) |
| 2 | Bias and Fairness in ML Systems | Analyze (L4) |
| 3 | Privacy, Consent, and Data Governance | Analyze (L4) |
| 4 | Accountability and Explainability | Apply (L3) |
| 5 | Designing Ethical ML Pipelines | Analyze (L4) |

## Tech Stack

- [LightRAG](https://github.com/HKUDS/LightRAG) — Knowledge graph construction and retrieval
- [Tavily](https://tavily.com) — Real-time academic and web research
- [OpenAI GPT-4o-mini](https://platform.openai.com) — Curriculum generation
- [Streamlit](https://streamlit.io) — UI

## Part of Plot Ark

This tutorial extracts the core engine from **[Plot Ark](https://github.com/Schlaflied/Plot-Ark)**, an open-source agentic curriculum platform for higher education with a full React + Flask + PostgreSQL stack, xAPI learning analytics, and knowledge graph visualization.
