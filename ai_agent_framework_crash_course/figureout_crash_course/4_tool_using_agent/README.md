# 🔧 Tutorial 4: Tool Using Agent with MCP

FigureOut integrates natively with [FastMCP](https://gofastmcp.com/) — a lightweight framework for building MCP (Model Context Protocol) tool servers. This tutorial shows how to define tools and have FigureOut call them automatically based on the query.

## 🎯 What You'll Learn

- How to define MCP tools with `@mcp.tool()`
- How to attach an MCP server to a FigureOut agent
- How `interpret_tool_response=True` works
- How to read tool call information from the debug output

## 🧠 Core Concept: MCP Tool Calling

FigureOut uses the role's `prompt` to instruct the LLM on which MCP tools are available and when to call them. The LLM decides which tool to call based on the user's query — no explicit dispatch logic needed.

```
User query → FigureOut classifies role → LLM calls MCP tool → Response structured via schema
```

### Setting Up a FastMCP Server

```python
from fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def search_products(query: str, max_price: float = None) -> list:
    """Search product catalog."""
    ...
```

### Attaching It to FigureOut

```python
agent = FigureOut(
    llm="openai",
    llm_version="gpt-4o-mini",
    roles=roles,
    mcp_server=mcp,
    interpret_tool_response=True,  # LLM interprets raw tool output before structuring
)
```

### `interpret_tool_response`

| Value | Behaviour |
|---|---|
| `True` | LLM receives raw tool output and interprets it before returning the schema response |
| `False` | Tool output is passed directly into the schema response without LLM interpretation |

Use `True` when tool output is raw data that needs summarising or filtering.
Use `False` when tool output already matches the schema.

## 📁 Project Structure

```
4_tool_using_agent/
├── README.md         # This file
├── requirements.txt  # Dependencies
└── agent.py          # Weather agent with MCP tools
```

## 🚀 Getting Started

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your API key**:
   ```bash
   export OPENAI_API_KEY=sk-your_key_here
   ```

3. **Run the agent**:
   ```bash
   python agent.py
   ```

## 🧪 Sample Debug Output

```json
{
  "debug": {
    "roles_selected": ["weather"],
    "tools_used": ["get_current_weather"],
    "input_tokens": 210,
    "output_tokens": 60
  }
}
```

## 💡 Pro Tips

- Tool function docstrings help the LLM understand when to call them — keep them clear
- The role `prompt` should mention available tools explicitly for best results
- Use `verbose=True` on `FigureOut` to see tool call details in the console

## 🔗 Next Steps

- **[Tutorial 5: Role Classification](../5_role_classification/README.md)** — route queries across multiple specialist roles
- **[Tutorial 6: Multi-Role Queries](../6_multi_role_queries/README.md)** — handle queries that span multiple domains
