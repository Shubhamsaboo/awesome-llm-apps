# 🌍 Earth Memory Geospatial Agent

A Streamlit app that lets you ask place-based questions and get signed geospatial facts using [emem](https://github.com/Vortx-AI/emem), a public MCP server.

## Features

- 🗺️ Query any place on Earth by name, address, or coordinates
- 📏 Get elevation, surface water, vegetation, and land cover data
- 🔏 Every fact comes with a signed CID and receipt for verification
- 🌊 Assess flood risk using real geospatial signals, not web search or model guesses

## Setup

### Requirements

- Python 3.10+
- OpenAI API key

### Installation

```bash
cd mcp_ai_agents/emem_geospatial_agent
pip install -r requirements.txt
```

### Running the App

```bash
streamlit run emem_agent.py
```

1. Enter your OpenAI API key in the sidebar
2. Type a place name (e.g. "Helsinki-Vantaa Airport, Finland")
3. Pick a query type or write your own
4. Click "Run Query"

No emem API key or signup is needed. The MCP endpoint is public.

### Example Queries

**Elevation**
- "What is the elevation at Helsinki-Vantaa Airport?"
- "Check elevation for downtown Miami, Florida"

**Flood risk**
- "Does Helsinki-Vantaa Airport have surface water or flood signals?"
- "Is downtown New Orleans at flood risk?"

**Land cover**
- "What is the land cover around Lake Erie, Ohio?"
- "Has vegetation changed near the Amazon river?"

**Signed evidence**
- "Give me signed geospatial facts for downtown San Francisco"
- "What evidence supports a flood risk assessment for Miami Beach?"

## How it works

The agent connects to emem's public MCP endpoint (`https://emem.dev/mcp`) using Streamable HTTP transport. When you ask a question, the AI agent calls emem tools to resolve your place, recall geospatial data, and return signed facts with content-addressed CIDs. No data is guessed. Every answer is backed by verifiable evidence.
