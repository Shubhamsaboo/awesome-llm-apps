# MCP Client Example

A Python client that connects to any MCP server via stdio transport. Use this to test your MCP servers interactively or to understand how MCP clients work.

## Features

- Automatically discovers all tools, resources, and prompts from the server
- Interactive command-line interface for calling tools and reading resources
- Works with any MCP server that uses stdio transport
- Displays tool parameters and descriptions

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### Connect to one of the exercise servers

```bash
# Connect to the calculator server
python client.py --server "python ../02_calculator_mcp_server/server.py"

# Connect to the notes server
python client.py --server "python ../04_notes_mcp_server/server.py"

# Connect to the weather server
python client.py --server "python ../01_weather_mcp_server/server.py"
```

### Discovery-only mode (no interactive prompt)

```bash
python client.py --server "python ../02_calculator_mcp_server/server.py" --discover-only
```

### Interactive commands

Once connected, use these commands:

```
mcp> tools                                          # List available tools
mcp> resources                                      # List available resources
mcp> call add {"a": 5, "b": 3}                     # Call a tool with arguments
mcp> call get_current_weather {"city": "London"}    # Call weather tool
mcp> read calculator://history                      # Read a resource
mcp> prompt solve_equation {"equation": "2x + 5 = 15"}  # Get a prompt
mcp> quit                                           # Exit
```

## How It Works

The client demonstrates the core MCP client flow:

1. **Spawn the server** -- starts the MCP server as a subprocess using `StdioServerParameters`
2. **Create a session** -- establishes a `ClientSession` over stdio pipes
3. **Initialize** -- performs the MCP protocol handshake
4. **Discover** -- calls `list_tools()`, `list_resources()`, `list_prompts()`
5. **Interact** -- calls `call_tool()`, `read_resource()`, `get_prompt()` based on user input

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(command="python", args=["server.py"])

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        # Now you can call tools, read resources, etc.
```
