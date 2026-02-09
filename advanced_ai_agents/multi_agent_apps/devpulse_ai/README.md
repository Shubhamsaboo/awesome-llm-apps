## 🧠 DevPulseAI - Multi-Agent Signal Intelligence Pipeline

A reference implementation demonstrating a **multi-agent system** for aggregating, analyzing, and synthesizing technical signals from multiple developer-focused sources.

### Features

- **Multi-Source Signal Collection** - Aggregates data from GitHub, ArXiv, HackerNews, Medium, and HuggingFace
- **LLM-Powered Analysis** - Four specialized agents working in concert
- **Structured Intelligence Output** - Prioritized digest with actionable recommendations

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Signal Intelligence Pipeline                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐         │
│  │ GitHub │ │ ArXiv  │ │  HN    │ │ Medium │ │   HF   │ ← Data  │
│  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘         │
│      └──────────┴──────────┼──────────┴──────────┘               │
│       │             │             │                              │
│       └─────────────┼─────────────┘                              │
│                     ▼                                            │
│           ┌─────────────────┐                                    │
│           │ Signal Collector│   ← Agent 1: Ingestion            │
│           └────────┬────────┘                                    │
│                    ▼                                             │
│           ┌─────────────────┐                                    │
│           │ Relevance Agent │   ← Agent 2: Scoring (0-100)      │
│           └────────┬────────┘                                    │
│                    ▼                                             │
│           ┌─────────────────┐                                    │
│           │   Risk Agent    │   ← Agent 3: Security Assessment  │
│           └────────┬────────┘                                    │
│                    ▼                                             │
│           ┌─────────────────┐                                    │
│           │ Synthesis Agent │   ← Agent 4: Final Digest         │
│           └────────┬────────┘                                    │
│                    ▼                                             │
│           ┌─────────────────┐                                    │
│           │ Intelligence    │   ← Prioritized Output            │
│           │ Digest          │                                    │
│           └─────────────────┘                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Responsibilities

| Agent | Role | Output |
|-------|------|--------|
| **SignalCollectorAgent** | Aggregates & normalizes signals | Unified signal list |
| **RelevanceAgent** | Scores developer relevance (0-100) | Score + reasoning |
| **RiskAgent** | Identifies security/breaking changes | Risk level + concerns |
| **SynthesisAgent** | Produces final intelligence digest | Prioritized recommendations |

### How to Get Started

1. Clone the repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/multi_agent_apps/devpulse_ai
```

1. Install dependencies

```bash
pip install -r requirements.txt
```

1. Set your Gemini API key (optional for live mode)

```bash
export GOOGLE_API_KEY=your_api_key
```

1. Run the verification script (no API key needed)

```bash
python verify.py
```

1. Run the full pipeline (requires API key for LLM agents)

```bash
python main.py
```

### Streamlit Demo

A modern, interactive dashboard is included to visualize the multi-agent pipeline:

1. Launch the app:

```bash
streamlit run streamlit_app.py
```

1. Configure sources and signal counts in the sidebar.
2. Provide a Gemini API key (optional) to use full LLM intelligence.
3. View real-time progress as agents collaborate.

> **Note**: The default configuration is optimized for fast demo runs.

### Verification Script

The `verify.py` script tests the entire pipeline using **mock data only** - no network calls or API keys required:

```bash
python verify.py
```

Expected output:

```
[OK] DevPulseAI reference pipeline executed successfully
```

### Optional: n8n Automation

An n8n workflow is included for those who want to automate the pipeline:

- **Location**: `workflows/signal-intelligence-pipeline.json`
- **Import**: n8n → Settings → Import from File
- **Requires**: n8n instance + configured credentials

This is entirely optional - the Python implementation works standalone.

### Directory Structure

```
devpulse_ai/
├── adapters/
│   ├── github.py       # GitHub trending repos
│   ├── arxiv.py        # AI/ML research papers
│   ├── hackernews.py   # Tech news stories
│   ├── medium.py       # Tech blog RSS feeds
│   └── huggingface.py  # HuggingFace models
├── agents/
│   ├── __init__.py
│   ├── signal_collector.py
│   ├── relevance_agent.py
│   ├── risk_agent.py
│   └── synthesis_agent.py
├── workflows/
│   └── signal-intelligence-pipeline.json
├── main.py             # Full pipeline demo (CLI)
├── streamlit_app.py    # Interactive dashboard (UI)
├── verify.py           # Mock data verification
├── requirements.txt
└── README.md
```

### How It Works

1. **Signal Collection**: Adapters fetch data from GitHub, ArXiv, HackerNews, Medium, and HuggingFace
2. **Normalization**: SignalCollectorAgent unifies signals to a common schema
3. **Relevance Scoring**: RelevanceAgent rates each signal 0-100 for developer relevance
4. **Risk Assessment**: RiskAgent flags security issues and breaking changes
5. **Synthesis**: SynthesisAgent produces a prioritized intelligence digest

### Built With

- [Agno](https://github.com/agno-agi/agno) - Multi-agent framework
- [Google Gemini 1.5 Flash](https://ai.google.dev/) - LLM backbone
- [httpx](https://www.python-httpx.org/) - Async HTTP client
