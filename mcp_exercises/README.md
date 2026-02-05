# MCP Exercises - Build Model Context Protocol Servers

A hands-on guide to building **Model Context Protocol (MCP)** servers from scratch using the official Python SDK. This directory contains step-by-step instructions and 4 reference MCP server implementations, plus a client example that connects to them.

## What is MCP?

The **Model Context Protocol (MCP)** is an open standard created by Anthropic that provides a universal way to connect LLMs to external data sources, tools, and services. Think of it like a USB-C port for AI -- a single standardized interface that lets any LLM application access any compatible data source or tool.

MCP follows a client-server architecture:

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   LLM / Host     │     │   MCP Client     │     │   MCP Server     │
│  (Claude, GPT,   │◄───►│  (SDK handles    │◄───►│  (Your code -    │
│   Llama, etc.)   │     │   protocol)      │     │   tools, data)   │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

### MCP's Three Core Primitives

| Primitive | Purpose | Analogy |
|-----------|---------|---------|
| **Tools** | Expose executable functions the LLM can call | Like POST endpoints in a REST API |
| **Resources** | Provide read-only data to load into LLM context | Like GET endpoints in a REST API |
| **Prompts** | Define reusable interaction templates | Like pre-built query templates |

## Prerequisites

- Python 3.10+
- `pip` or `uv` package manager
- Node.js 18+ (for MCP Inspector testing tool)
- Basic understanding of Python async/await

## Project Structure

```
mcp_exercises/
├── README.md                        # This guide
├── 01_weather_mcp_server/           # Weather lookup MCP server
│   ├── server.py
│   ├── requirements.txt
│   └── README.md
├── 02_calculator_mcp_server/        # Scientific calculator MCP server
│   ├── server.py
│   ├── requirements.txt
│   └── README.md
├── 03_file_search_mcp_server/       # File system search MCP server
│   ├── server.py
│   ├── requirements.txt
│   └── README.md
├── 04_notes_mcp_server/             # Notes & todo management MCP server
│   ├── server.py
│   ├── requirements.txt
│   └── README.md
└── 05_mcp_client_example/           # Python client that connects to MCP servers
    ├── client.py
    ├── requirements.txt
    └── README.md
```

---

## Step-by-Step Guide: Building Your First MCP Server

### Step 1: Install the MCP Python SDK

```bash
# Using pip
pip install "mcp[cli]"

# Or using uv (recommended)
uv add "mcp[cli]"
```

### Step 2: Create the Server File

Create a new Python file (e.g., `server.py`) and import the MCP server class:

```python
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server with a name
mcp = FastMCP("My First MCP Server")
```

The `FastMCP` class is the high-level interface that handles all protocol details, message routing, and connection management for you.

### Step 3: Define Tools

Tools are functions the LLM can call to perform actions or computations. Use the `@mcp.tool()` decorator:

```python
@mcp.tool()
def greet(name: str) -> str:
    """Generate a greeting for the given name."""
    return f"Hello, {name}! Welcome to MCP."

@mcp.tool()
def add_numbers(a: float, b: float) -> float:
    """Add two numbers together and return the result."""
    return a + b
```

Key points about tools:
- The **docstring** becomes the tool's description (shown to the LLM)
- **Type hints** define the parameter schema automatically
- Tools can be **sync or async**
- Tools can perform **side effects** (write files, make API calls, etc.)

### Step 4: Define Resources

Resources provide read-only data that can be loaded into the LLM's context:

```python
@mcp.resource("config://app-settings")
def get_app_settings() -> str:
    """Return current application settings."""
    return '{"theme": "dark", "language": "en", "version": "1.0"}'

@mcp.resource("file://documents/{name}")
def read_document(name: str) -> str:
    """Read a document by name."""
    documents = {
        "readme": "This is the README content.",
        "guide": "This is the user guide.",
    }
    return documents.get(name, f"Document '{name}' not found.")
```

Key points about resources:
- Resources use **URI templates** (e.g., `config://`, `file://`)
- They are **read-only** -- no side effects
- Dynamic resources use `{parameter}` placeholders in the URI
- The LLM can request resources to load context

### Step 5: Define Prompts

Prompts are reusable templates for common LLM interactions:

```python
@mcp.prompt()
def code_review(language: str, code: str) -> str:
    """Generate a code review prompt for the given code."""
    return f"""Please review the following {language} code for:
- Bugs and potential errors
- Performance issues
- Best practices and style

Code:
```{language}
{code}
```"""
```

### Step 6: Run the Server

Add the entry point to your server file:

```python
if __name__ == "__main__":
    # Run with stdio transport (for local MCP clients)
    mcp.run(transport="stdio")
```

Available transport options:
- `"stdio"` -- Standard input/output (most common, used by Claude Desktop, Cursor, etc.)
- `"streamable-http"` -- HTTP-based transport (for remote/web deployments)
- `"sse"` -- Server-Sent Events (legacy, use streamable-http instead)

### Step 7: Test with MCP Inspector

The MCP Inspector is an interactive tool for testing your server:

```bash
# Install and run the inspector
npx -y @modelcontextprotocol/inspector

# Then connect to your server in the Inspector UI
```

Alternatively, test directly from the command line:

```bash
# Run your server directly
python server.py

# Or with mcp CLI
mcp run server.py
```

### Step 8: Connect to an LLM Client

#### Option A: Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["/path/to/server.py"]
    }
  }
}
```

#### Option B: Programmatic Python Client

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["server.py"],
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()

        # List available tools
        tools = await session.list_tools()
        print(f"Available tools: {[t.name for t in tools.tools]}")

        # Call a tool
        result = await session.call_tool("greet", {"name": "World"})
        print(f"Result: {result.content[0].text}")
```

#### Option C: Using with agno Framework

```python
from agno.agent import Agent
from agno.tools.mcp import MCPTools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["server.py"],
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        mcp_tools = MCPTools(session=session)
        await mcp_tools.initialize()

        agent = Agent(
            tools=[mcp_tools],
            instructions="You are a helpful assistant.",
            markdown=True,
        )
        response = await agent.arun("Use the tools to help me.")
```

---

## Complete Example: Minimal MCP Server

Here's a complete, working MCP server in a single file:

```python
"""A minimal MCP server demonstrating all three primitives."""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Minimal Demo")


# --- Tools ---
@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


@mcp.tool()
def reverse_string(text: str) -> str:
    """Reverse a string."""
    return text[::-1]


# --- Resources ---
@mcp.resource("info://server-status")
def server_status() -> str:
    """Get the current server status."""
    return '{"status": "running", "version": "1.0.0"}'


# --- Prompts ---
@mcp.prompt()
def summarize(text: str, max_words: int = 50) -> str:
    """Create a summarization prompt."""
    return f"Summarize the following text in {max_words} words or less:\n\n{text}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
```

---

## Reference MCP Server Implementations

Each exercise builds on the concepts above with a fully working MCP server:

| # | Project | Description | Concepts Covered |
|---|---------|-------------|------------------|
| 01 | [Weather MCP Server](01_weather_mcp_server/) | Look up weather data for any city | Tools, async HTTP calls, API integration |
| 02 | [Calculator MCP Server](02_calculator_mcp_server/) | Scientific calculator with history | Tools, Resources, state management |
| 03 | [File Search MCP Server](03_file_search_mcp_server/) | Search and read files on the local filesystem | Tools, Resources, Prompts, file I/O |
| 04 | [Notes MCP Server](04_notes_mcp_server/) | Create, read, update, delete notes | Full CRUD, Resources, persistent state |
| 05 | [MCP Client Example](05_mcp_client_example/) | Python client connecting to any MCP server | Client SDK, tool discovery, tool calling |

---

## Advanced Concepts

### Async Tools

For I/O-bound operations (API calls, file reads), use async tools:

```python
@mcp.tool()
async def fetch_data(url: str) -> str:
    """Fetch data from a URL."""
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text
```

### Error Handling

Return meaningful errors so the LLM can recover:

```python
@mcp.tool()
def divide(a: float, b: float) -> str:
    """Divide two numbers."""
    if b == 0:
        return "Error: Division by zero is not allowed."
    return str(a / b)
```

### Structured Output with Pydantic

```python
from pydantic import BaseModel

class WeatherResult(BaseModel):
    city: str
    temperature: float
    unit: str
    description: str

@mcp.tool()
def get_weather(city: str) -> WeatherResult:
    """Get weather for a city."""
    return WeatherResult(
        city=city,
        temperature=22.5,
        unit="celsius",
        description="Partly cloudy",
    )
```

### Context and Progress Reporting

```python
from mcp.server.fastmcp import Context

@mcp.tool()
async def long_task(steps: int, ctx: Context) -> str:
    """Run a long task with progress updates."""
    for i in range(steps):
        await ctx.report_progress(progress=i + 1, total=steps)
        await ctx.info(f"Completed step {i + 1}/{steps}")
    return f"Completed {steps} steps"
```

### Lifespan Management (Database Connections, etc.)

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

@dataclass
class AppContext:
    db_connection: object

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage server lifecycle -- connect/disconnect resources."""
    db = await connect_to_database()
    try:
        yield AppContext(db_connection=db)
    finally:
        await db.disconnect()

mcp = FastMCP("DB Server", lifespan=app_lifespan)
```

---

## Useful Commands

| Command | Description |
|---------|-------------|
| `pip install "mcp[cli]"` | Install the MCP Python SDK |
| `mcp run server.py` | Run an MCP server |
| `mcp dev server.py` | Run with hot-reload for development |
| `npx @modelcontextprotocol/inspector` | Launch the MCP Inspector for testing |
| `mcp install server.py` | Install server into Claude Desktop |

## Resources

- [MCP Official Documentation](https://modelcontextprotocol.io/)
- [MCP Python SDK (GitHub)](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Python SDK Docs](https://modelcontextprotocol.github.io/python-sdk/)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Anthropic MCP Course](https://anthropic.skilljar.com/introduction-to-model-context-protocol)
- [Real Python MCP Tutorial](https://realpython.com/python-mcp/)

## License

This project is part of [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) and is licensed under the Apache License 2.0.
