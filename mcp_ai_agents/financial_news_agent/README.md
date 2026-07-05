# 📈 Financial News MCP Agent

A Streamlit app that answers natural-language questions about the stock market using the [AlphaAI](https://alphai.io) MCP server through the Model Context Protocol (MCP). Every article AlphaAI returns is pre-analyzed at ingest with a **per-ticker relevance score (1-10)**, a category, and impact analysis, and SEC EDGAR **Form 4 insider filings** are surfaced as structured data.

**✨ Uses AlphaAI's hosted [MCP server](https://alphai.io/mcp) — Streamable HTTP + OAuth 2.1 — with a real free tier (no credit card).**

## Features

- **Natural Language Interface**: Ask about tickers, sectors, trending stories, or insider activity in plain English
- **Relevance-Scored News**: Results lead with the highest-relevance stories and surface the 1-10 score
- **SEC Form 4 Insider Data**: Ask about insider buying/selling, scored as structured events
- **MCP Integration**: Connects to a remote OAuth-protected MCP server via `mcp-remote`
- **Interactive UI**: Streamlit interface with example queries and custom input

## Setup

### Requirements

- Python 3.8+
- Node.js (provides `npx`, used to run [`mcp-remote`](https://www.npmjs.com/package/mcp-remote))
  - Install from [nodejs.org](https://nodejs.org/)
- OpenAI API Key
- A free AlphaAI account (created during the OAuth step — no credit card)

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/mcp_ai_agents/financial_news_agent
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Verify Node.js is available (for `npx mcp-remote`):
   ```bash
   node --version
   npx --version
   ```

4. Get your API key:
   - **OpenAI API Key**: Get from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

### Running the App

1. Start the Streamlit app:
   ```bash
   streamlit run financial_news_agent.py
   ```

2. In the app:
   - Enter your OpenAI API key in the sidebar
   - Type a query (or pick an example) and click **Run Query**
   - On the **first** run, a browser tab opens for AlphaAI OAuth — sign in or create a free account, and approve access. `mcp-remote` caches the token, so later runs skip this step.

## Example Queries

- "What's the latest news on NVDA?"
- "Show me today's top trending market stories"
- "Any recent SEC Form 4 insider buying in energy names?"
- "Summarize high-relevance news about Tesla this week"

## How It Works

1. `mcp-remote` bridges AlphaAI's remote Streamable-HTTP MCP server to a local stdio transport and runs the OAuth 2.1 handshake on first connect.
2. The [Agno](https://github.com/agno-agi/agno) agent (powered by OpenAI) loads the AlphaAI MCP tools — news search, trending, per-ticker feeds, single-article fetch, ticker discovery, and SEC Form 4 insider news.
3. The agent picks the right tools for your question, and AlphaAI returns relevance-scored, ticker-linked results.
4. Answers are rendered as markdown with the relevance signal surfaced.

## About AlphaAI

[AlphaAI](https://alphai.io) turns the financial-news firehose (GDELT + SEC EDGAR) into machine-readable signal for AI agents and trading bots. It's available as a REST API and an MCP server, with a free tier of 20 requests/min and 100/day on both. See the [MCP docs](https://alphai.io/mcp) and [developer guide](https://alphai.io/developers).
