"""
MCP Client Example
==================
A Python client that connects to any MCP server and demonstrates:
- Discovering tools, resources, and prompts
- Calling tools and reading resources
- Interactive chat loop with an LLM that uses MCP tools

Usage:
    # Connect to the calculator MCP server
    python client.py --server "python ../02_calculator_mcp_server/server.py"

    # Connect to any MCP server
    python client.py --server "python /path/to/server.py"
"""

import argparse
import asyncio
import json
import shlex
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def discover_capabilities(session: ClientSession) -> dict:
    """Discover and display all capabilities of the connected MCP server."""
    capabilities = {}

    # Discover tools
    print("\n--- Available Tools ---")
    try:
        tools_result = await session.list_tools()
        tools = tools_result.tools
        capabilities["tools"] = tools
        if tools:
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
                if tool.inputSchema and "properties" in tool.inputSchema:
                    for param, schema in tool.inputSchema["properties"].items():
                        param_type = schema.get("type", "any")
                        desc = schema.get("description", "")
                        print(f"      param: {param} ({param_type}) - {desc}")
        else:
            print("  (no tools available)")
    except Exception as e:
        print(f"  Error listing tools: {e}")

    # Discover resources
    print("\n--- Available Resources ---")
    try:
        resources_result = await session.list_resources()
        resources = resources_result.resources
        capabilities["resources"] = resources
        if resources:
            for resource in resources:
                print(f"  - {resource.uri}: {resource.description}")
        else:
            print("  (no resources available)")
    except Exception as e:
        print(f"  Error listing resources: {e}")

    # Discover prompts
    print("\n--- Available Prompts ---")
    try:
        prompts_result = await session.list_prompts()
        prompts = prompts_result.prompts
        capabilities["prompts"] = prompts
        if prompts:
            for prompt in prompts:
                print(f"  - {prompt.name}: {prompt.description}")
        else:
            print("  (no prompts available)")
    except Exception as e:
        print(f"  Error listing prompts: {e}")

    return capabilities


async def interactive_mode(session: ClientSession):
    """Run an interactive mode where users can call tools and read resources."""
    print("\n--- Interactive Mode ---")
    print("Commands:")
    print("  call <tool_name> <json_args>  - Call a tool")
    print("  read <resource_uri>           - Read a resource")
    print("  prompt <prompt_name> <args>   - Get a prompt")
    print("  tools                         - List tools")
    print("  resources                     - List resources")
    print("  quit                          - Exit")
    print()

    while True:
        try:
            user_input = input("mcp> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not user_input:
            continue

        parts = user_input.split(maxsplit=2)
        command = parts[0].lower()

        if command == "quit" or command == "exit":
            print("Goodbye!")
            break

        elif command == "tools":
            tools_result = await session.list_tools()
            for tool in tools_result.tools:
                print(f"  {tool.name}: {tool.description}")

        elif command == "resources":
            resources_result = await session.list_resources()
            for resource in resources_result.resources:
                print(f"  {resource.uri}: {resource.description}")

        elif command == "call":
            if len(parts) < 2:
                print("Usage: call <tool_name> <json_args>")
                print('Example: call add {"a": 5, "b": 3}')
                continue

            tool_name = parts[1]
            args = {}
            if len(parts) > 2:
                try:
                    args = json.loads(parts[2])
                except json.JSONDecodeError:
                    print(f"Error: Invalid JSON arguments: {parts[2]}")
                    continue

            try:
                result = await session.call_tool(tool_name, args)
                for content in result.content:
                    if hasattr(content, "text"):
                        try:
                            parsed = json.loads(content.text)
                            print(json.dumps(parsed, indent=2))
                        except json.JSONDecodeError:
                            print(content.text)
                    else:
                        print(content)
            except Exception as e:
                print(f"Error calling tool '{tool_name}': {e}")

        elif command == "read":
            if len(parts) < 2:
                print("Usage: read <resource_uri>")
                continue
            uri = parts[1]
            try:
                result = await session.read_resource(uri)
                for content in result.contents:
                    if hasattr(content, "text"):
                        try:
                            parsed = json.loads(content.text)
                            print(json.dumps(parsed, indent=2))
                        except json.JSONDecodeError:
                            print(content.text)
                    else:
                        print(content)
            except Exception as e:
                print(f"Error reading resource '{uri}': {e}")

        elif command == "prompt":
            if len(parts) < 2:
                print("Usage: prompt <prompt_name> <json_args>")
                continue
            prompt_name = parts[1]
            args = {}
            if len(parts) > 2:
                try:
                    args = json.loads(parts[2])
                except json.JSONDecodeError:
                    print(f"Error: Invalid JSON arguments: {parts[2]}")
                    continue

            try:
                result = await session.get_prompt(prompt_name, args)
                for message in result.messages:
                    if hasattr(message.content, "text"):
                        print(message.content.text)
                    else:
                        print(message.content)
            except Exception as e:
                print(f"Error getting prompt '{prompt_name}': {e}")

        else:
            print(f"Unknown command: {command}")
            print("Type 'quit' to exit or see commands above.")


async def main(server_command: str, interactive: bool = True):
    """Connect to an MCP server and explore its capabilities."""
    args = shlex.split(server_command)
    if not args:
        print("Error: Server command cannot be empty.")
        sys.exit(1)

    server_params = StdioServerParameters(
        command=args[0],
        args=args[1:] if len(args) > 1 else [],
    )

    print(f"Connecting to MCP server: {server_command}")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected successfully!")

            # Discover capabilities
            await discover_capabilities(session)

            # Enter interactive mode
            if interactive:
                await interactive_mode(session)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP Client Example")
    parser.add_argument(
        "--server",
        required=True,
        help='Server command to run (e.g., "python ../02_calculator_mcp_server/server.py")',
    )
    parser.add_argument(
        "--discover-only",
        action="store_true",
        help="Only discover capabilities, don't enter interactive mode",
    )
    args = parser.parse_args()

    asyncio.run(main(args.server, interactive=not args.discover_only))
