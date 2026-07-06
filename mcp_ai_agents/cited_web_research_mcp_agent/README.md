# Cited Web Research MCP Agent

A Streamlit app that answers research questions with current web sources.

Instead of showing raw search results, the model runs the research loop:

- plans searches from the user's question
- calls `web_search` through MCP
- chooses source URLs to inspect
- calls `web_fetch` through MCP
- writes a cited answer with evidence, limitations, and source links

## Features

- Streamlit interface for asking web research questions
- OpenAI model loop with MCP tool calling
- Real MCP tool discovery with `list_tools()`
- Source fetching before the final answer
- Expandable tool trace for debugging

## Setup

### Requirements

- Python 3.10+
- OpenAI API key
- Network access to the configured MCP server

### Installation

1. Clone this repository:

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/mcp_ai_agents/cited_web_research_mcp_agent
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Optionally create a local `.env` file:

```bash
cp .env.example .env
```

Then set `OPENAI_API_KEY` in `.env`, or paste the key into the Streamlit sidebar.

4. Run the app:

```bash
streamlit run cited_web_research_mcp_agent.py
```

## Usage

Ask a question that benefits from current web evidence, such as:

- What are the newest changes in Python packaging standards?
- Compare recent approaches to AI agent tool use and cite sources.
- What changed in browser automation for AI agents this month?

The app shows the answer first, with an expandable trace of the MCP calls the model made.

## How It Works

1. The app opens a Streamable HTTP MCP session.
2. It calls `list_tools()` and requires `web_search` and `web_fetch`.
3. It passes those tool schemas to the OpenAI chat model as callable tools.
4. When the model requests a tool call, the app dispatches it through the MCP session.
5. Tool results are returned to the model for follow-up searches, fetches, or final synthesis.

The default MCP server is:

```text
https://search.parallel.ai/mcp
```

You can point `MCP_SERVER_URL` at another MCP server if it exposes compatible `web_search` and `web_fetch` tools.

## Project Structure

```text
cited_web_research_mcp_agent.py  # Streamlit app and MCP/OpenAI tool loop
requirements.txt                 # Python dependencies
.env.example                     # Optional local environment template
README.md                        # Setup and usage guide
```
