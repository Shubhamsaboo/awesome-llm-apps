# 🤝 Multi-Agent App with Shared Memory

A Streamlit application demonstrating **multi-agent coordination with shared memory** using [Aegis Memory](https://github.com/quantifylabs/aegis-memory). Three specialized agents (Researcher, Analyst, Writer) collaborate on tasks while maintaining scoped memory access.

## Features

- 🔄 **Multi-Agent Coordination**: Pipeline of specialized agents working together
- 🎯 **Scope-Aware Memory**: Private, agent-shared, and global memory scopes
- 🗳️ **Memory Voting**: Agents vote on memory usefulness (ACE pattern)
- 🔍 **Cross-Agent Queries**: Structured memory handoffs between agents
- 📊 **Real-time Dashboard**: Visualize memory flow between agents

## How it Works

```
User Query
    │
    ▼
┌─────────────────────────────────────┐
│  🔬 Researcher Agent                │
│  └─► Stores in SHARED memory        │
│      (visible to Analyst)           │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  📊 Analyst Agent                   │
│  ├─► Queries Researcher's memory    │
│  ├─► Votes on memory helpfulness    │
│  └─► Stores in SHARED memory        │
│      (visible to Writer)            │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  ✍️ Writer Agent                    │
│  ├─► Queries Analyst's memory       │
│  └─► Stores in GLOBAL memory        │
│      (visible to all)               │
└─────────────────────────────────────┘
```

## Getting Started

### Prerequisites

- Python 3.10+
- OpenAI API key
- Docker (for Aegis Memory server)

### Installation

1. Clone the repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_llm_apps/llm_apps_with_memory_tutorials/multi_agent_shared_memory
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Start the Aegis Memory server

```bash
docker run -d -p 8000:8000 quantifylabs/aegis-memory:latest
```

4. Run the app

```bash
streamlit run multi_agent_memory_app.py
```

## Memory Scopes Explained

| Scope | Description | Use Case |
|-------|-------------|----------|
| `private` | Only creating agent can access | Internal notes, drafts |
| `agent-shared` | Shared with specific agents | Handoffs between agents |
| `global` | All agents can access | Final outputs, team knowledge |

## Tech Stack

- **[Aegis Memory](https://github.com/quantifylabs/aegis-memory)** - Multi-agent memory engine
- **[OpenAI](https://openai.com/)** - LLM for agent reasoning
- **[Streamlit](https://streamlit.io/)** - Web UI framework

## License

Apache-2.0 License
