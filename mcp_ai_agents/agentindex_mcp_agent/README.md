# 🔍 AgentIndex MCP Agent - AI Agent Discovery

A simple MCP agent that discovers and recommends AI agents for any task using [AgentIndex](https://agentcrawl.dev), which indexes 39,000+ agents across GitHub, npm, PyPI, HuggingFace, and MCP registries.

## Features
- 🔍 Natural language search across 39,000+ AI agents
- 🏷️ Filter by category, protocol, and quality score
- 🤖 MCP and A2A protocol support
- 📊 Ranked results with quality scores

## Getting Started

### Prerequisites
```bash
pip install agentcrawl
```

### Run the Agent
```bash
python agentindex_mcp_agent.py
```

### Example Usage
Ask the agent:
- "Find me an agent that can translate documents"
- "What MCP agents can help with code review?"
- "Show me the best agents for data analysis"

## How It Works
The agent connects to AgentIndex's MCP server at `mcp.agentcrawl.dev/sse` and uses semantic search to find the most relevant agents for your query. Results are ranked by quality score and include invocation details.
