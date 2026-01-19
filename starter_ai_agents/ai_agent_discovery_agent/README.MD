## 🔍 AI Agent Discovery

This Streamlit app is an AI-powered agent discovery tool that helps you find and compare AI agents across multiple registries. It uses the Registry Broker API to search NANDA, MCP, Virtuals, A2A, and ERC-8004 agents in one place.

### Features
- Search AI agents across 5+ registries with a single query
- Get AI-powered recommendations using GPT-4o or local Llama
- View detailed agent information including capabilities and endpoints
- Browse available categories and registries
- Works with both cloud (OpenAI) and local (Ollama) LLMs

### Supported Registries
- **NANDA** - MIT's Network for AI Networked Digital Agents
- **MCP** - Model Context Protocol servers
- **Virtuals** - Virtuals Protocol on-chain agents
- **A2A** - Google's Agent-to-Agent protocol
- **ERC-8004** - Ethereum standard for on-chain agents

### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/starter_ai_agents/ai_agent_discovery_agent
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Get your OpenAI API Key (for cloud version)

- Sign up for an [OpenAI account](https://platform.openai.com/) and obtain your API key.

4. Run the Streamlit App

```bash
streamlit run agent_discovery.py
```

For local LLM usage (with Ollama):
```bash
ollama pull llama3.2
streamlit run local_agent_discovery.py
```

### How it Works?

The AI Agent Discovery app has two main components:
- **Registry Search:** Queries the Registry Broker API to find agents matching your search across multiple registries (NANDA, MCP, Virtuals, A2A, ERC-8004).
- **AI Analysis:** Uses GPT-4o (cloud) or Llama (local) to analyze the search results and provide intelligent recommendations based on your use case.

### Local vs Cloud Version

- **agent_discovery.py**: Uses OpenAI's GPT-4o for high-quality agent recommendations (requires OpenAI API key)
- **local_agent_discovery.py**: Uses Ollama for local LLM inference without sending data to external APIs (requires Ollama to be installed and running)

### API Reference

This app uses the [Registry Broker API](https://hol.org/registry/docs):
- `GET /api/v1/search` - Search agents across all registries
- `GET /api/v1/agents/{uaid}` - Get agent details
- `GET /api/v1/search/facets` - Get available categories and registries
