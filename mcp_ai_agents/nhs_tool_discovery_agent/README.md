# 🔍 AI Tool Discovery Agent

An agent that helps developers and AI agents discover APIs, services, and tools ranked by agentic readiness. Uses the [Not Human Search](https://nothumansearch.ai) MCP server over streamable-HTTP transport — no Docker or local server setup required.

## Features

- **Natural Language Search**: Ask for tools in plain English (e.g., "Find payment APIs for AI agents")
- **Agentic Readiness Scores**: Every result is scored 0-100 based on 7 signals (llms.txt, OpenAPI, MCP, etc.)
- **Domain Analysis**: Check any domain's agentic readiness and which signals it supports
- **MCP Verification**: Verify whether a site has a working MCP endpoint via live JSON-RPC probe
- **Remote MCP Transport**: Connects directly to the cloud MCP server — no Docker needed

## How It Works

The agent connects to `https://nothumansearch.ai/mcp` using MCP's streamable-HTTP transport and gets access to these tools:

| Tool | Description |
|---|---|
| `search_agents` | Search 1,750+ sites by keyword, category, or minimum score |
| `check_score` | Get the full agentic readiness report for a specific domain |
| `get_stats` | Index-wide statistics (total sites, avg score, top categories) |
| `submit_site` | Submit a new URL for crawling and indexing |
| `verify_mcp` | Live JSON-RPC probe to verify any MCP endpoint |

## Setup

### Requirements

- Python 3.10+
- Anthropic API Key

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/mcp_ai_agents/nhs_tool_discovery_agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Get your Anthropic API key from [console.anthropic.com](https://console.anthropic.com)

### Running the App

```bash
streamlit run tool_discovery_agent.py
```

Enter your Anthropic API key in the sidebar and start searching.

### Example Queries

**Find services:**
- "Find payment APIs for AI agents"
- "What ecommerce platforms have MCP servers?"
- "Show me agent-ready weather data APIs"

**Check readiness:**
- "What's the agentic readiness score for stripe.com?"
- "Does github.com have an MCP server?"

**Explore the index:**
- "How many sites are indexed?"
- "Show me the top AI tools with MCP support"
