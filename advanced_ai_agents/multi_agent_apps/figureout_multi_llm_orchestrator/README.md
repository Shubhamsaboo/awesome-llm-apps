# 🧩 FigureOut — Multi-LLM Orchestrator with MCP Tool Calling

A lightweight, modular orchestrator for building LLM workflows without framework bloat. FigureOut classifies incoming queries and dispatches them to the right role, returning a structured JSON response.

This demo is a conversational **Events & Sports Booking Assistant** backed by live MCP tool calls. Ask about concerts, sports, movies, comedy shows, theater, seat availability, or fees — FigureOut automatically routes each query to the right specialist role and calls the appropriate MCP tools.

## Demo

https://github.com/user-attachments/assets/b638644f-d9e7-404d-8978-1cd9ffebb308

## Features

- **Automatic Role Classification**: Queries are classified and dispatched to the most relevant specialist — no manual routing logic required
- **Live MCP Tool Calling**: 5 FastMCP tools (`get_events_by_artist`, `get_events_by_genre`, `get_events_by_type`, `get_seats`, `get_fees`) are called automatically based on the query
- **10 Specialist Roles**: Sports, Music, Festivals, Movies, Comedy, Theater, Family, Seat Selection, Add-ons, and Fees
- **6 LLM Providers**: Works with OpenAI, Google Gemini, Anthropic Claude, Meta (Llama), Mistral, and Groq — swap from the sidebar
- **Structured JSON Output**: Every role returns a schema-validated response, making results predictable and easy to render
- **Multi-Role Queries**: Up to 3 roles can handle a single query in parallel (e.g. "concerts and sports this weekend")
- **Debug Panel**: Toggle to see which role was selected, which tools were called, and token usage

## How It Works

1. **Query input**: User asks a question in the Streamlit chat interface
2. **Classification**: FigureOut's classifier selects the best-matching role (or falls back to `off_topic`)
3. **Tool dispatch**: The role's system prompt instructs the LLM to call the relevant MCP tools (e.g. `get_events_by_type` for sports queries)
4. **Structured response**: The LLM returns a JSON object matching the role's schema — events list, seat recommendations, fee breakdown, etc.
5. **Render**: The response is parsed and rendered with role attribution and tool call visibility

## Requirements

- Python 3.8+
- API key for at least one supported LLM provider

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/single_agent_apps/figureout_multi_llm_orchestrator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the Streamlit app:
   ```bash
   streamlit run app_mcp.py
   ```

2. Open your browser at `http://localhost:8501`

3. In the sidebar:
   - Select your LLM provider and model
   - Paste your API key
   - Optionally set your location and date range to filter events

4. Ask a question or click one of the example buttons

## Example Questions

**Event Discovery**
- "Find me any upcoming concerts"
- "Are there any sports events this weekend?"
- "Show me comedy shows"
- "What movies are playing?"
- "Find family-friendly events"

**Seats & Fees**
- "What are the best seats for event 1?"
- "What fees apply to event 1?"

## MCP Tools

| Tool | Description |
|---|---|
| `get_events_by_artist` | Search events by artist name |
| `get_events_by_genre` | Search events by genre |
| `get_events_by_type` | Search events by type (Concert, Sports, Movie, etc.) |
| `get_seats` | Get seat availability for an event, optionally filtered by tier |
| `get_fees` | Get fee breakdown for an event |

## Using FigureOut in Your Own Project

```python
import asyncio
from fastmcp import FastMCP
from figureout import FigureOut, RoleDefinition

mcp = FastMCP("my-server")

@mcp.tool()
def search_products(query: str) -> list:
    ...

agent = FigureOut(
    llm="openai",
    llm_version="gpt-4o-mini",
    roles={
        "product_search": RoleDefinition(
            prompt="You are a product search specialist.",
            schema='{"results": [{"name": str, "price": float}], "summary": str}',
            guideline="queries about finding or searching for products",
        ),
    },
    mcp_server=mcp,
    interpret_tool_response=True,
)

result = asyncio.run(agent.run("Find me a blue running shoe under $100"))
print(result)
```

Install only the provider you need:
```bash
pip install figureout[openai]   # OpenAI
pip install figureout[gemini]   # Google Gemini
pip install figureout[claude]   # Anthropic Claude
pip install figureout[all]      # All providers
```
