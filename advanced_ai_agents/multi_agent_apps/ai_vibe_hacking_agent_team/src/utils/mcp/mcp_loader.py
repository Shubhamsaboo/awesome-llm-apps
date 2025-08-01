import json
from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio

async def load_mcp_tools(agent_name=None):
    with open("mcp_config.json", "r") as f:
        config = json.load(f)

    if agent_name:
        selected_agents = {agent: config[agent] for agent in agent_name if agent in config}
    else:
        selected_agents = config

    tools = []

    for agent_name, servers in selected_agents.items():
        if not servers:
            continue

        for server_name, server_config in servers.items():
            if "transport" not in server_config:
                server_config["transport"] = "streamable_http" if "url" in server_config else "stdio"

            client = MultiServerMCPClient({server_name: server_config})
            current_tools = await client.get_tools() if client else []

            if current_tools:
                tools.extend(current_tools)

    return tools if tools else []