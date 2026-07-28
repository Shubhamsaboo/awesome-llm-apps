# 🏆 Lumify Sports Intelligence Agent

A terminal-based sports betting research agent that talks to the [Lumify](https://lumify.ai) MCP server using natural language - schedules, live scores, odds, line movement, public betting splits, and explainable AI bet confidence across MLB, NFL, NCAAF, NCAAB, NBA, NHL, tennis, and soccer.

## Features

- Ask for schedules, live scores, odds, and line movement in plain English
- Get explainable bet-confidence intelligence for a specific matchup (not a black-box pick - the reasoning behind it)
- Free cost estimation before spending credits (`estimate_cost` is always free)
- Remembers conversation context for multi-turn research sessions
- Connects to Lumify's hosted MCP server over Streamable HTTP - no local server to install

## Prerequisites

- Python 3.10+
- An OpenAI API key
- A Lumify API key

## Getting a Lumify API key

- **Fastest:** a free instant trial key, no signup - <https://lumify.ai/docs/ai> (100 credits, 14-day expiry)
- **Persistent:** create a free account for 1,000 starter credits - <https://lumify.ai/api-keys>

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/mcp_ai_agents/lumify_sports_intelligence_agent
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Set these as environment variables (or in a `.env` file in this folder):

- `LUMIFY_API_KEY`: Your Lumify API key
- `OPENAI_API_KEY`: Your OpenAI API key
- `LUMIFY_MCP_URL` (optional): Defaults to `https://lumify.ai/mcp`

## Usage

Run the agent interactively from the command line:

```bash
python lumify_sports_agent.py
```

Or pass a one-off question as arguments and get a single response:

```bash
python lumify_sports_agent.py "What NBA games are on tonight and what's the best bet?"
```

You can exit an interactive session at any time by typing `exit`, `quit`, or `bye`.

## Example Queries

- "What NHL games are scheduled today?"
- "What's the live score of the Celtics game right now?"
- "Give me the odds and line movement for tonight's Yankees game"
- "What's Lumify's bet confidence on the Chiefs vs Bills game, and why?"
- "How many credits would it cost to check odds and intelligence for 3 NFL games?"
- "Show me the public betting split on the Lakers game"

## How It Works

The agent connects to Lumify's hosted MCP server (`https://lumify.ai/mcp`, Streamable HTTP) using [Agno](https://github.com/agno-agi/agno)'s `MCPTools`, authenticating with your API key as a Bearer token. All 18 Lumify tools (`list_events`, `get_odds`, `get_intelligence`, `get_live_score`, `estimate_cost`, and more) load automatically - there are no per-tool wrappers to write or keep in sync as Lumify adds new sports or endpoints.

Each `tools/call` is metered the same as the equivalent REST call; `initialize`, `tools/list`, and `estimate_cost` are always free, and calls for data that isn't available yet (e.g. odds on a match that hasn't been priced) return `available: false` at no charge.
