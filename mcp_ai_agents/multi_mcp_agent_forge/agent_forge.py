"""Multi-MCP Agent Forge - Specialized agents with MCP tool routing.

Each agent connects to different MCP servers based on its domain expertise.
This demonstrates the pattern of routing queries to specialized agents
rather than giving one agent access to all tools.

Inspired by: https://github.com/WeberG619/cadre-ai
"""

import asyncio
import json
import os
from contextlib import AsyncExitStack
from dataclasses import dataclass, field

import streamlit as st
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

st.set_page_config(
    page_title="Agent Forge - Multi-MCP Agents",
    page_icon="\u2692\ufe0f",
    layout="wide",
)


@dataclass
class Agent:
    """A specialized agent with its own system prompt and MCP server configs."""
    name: str
    description: str
    system_prompt: str
    icon: str = "\U0001f916"
    mcp_servers: list = field(default_factory=list)


# --- Agent Definitions ---
AGENTS = {
    "code_reviewer": Agent(
        name="Code Reviewer",
        description="Reviews code for bugs, anti-patterns, and maintainability",
        icon="\U0001f50d",
        system_prompt=(
            "You are an expert code reviewer. Analyze code for:\n"
            "- Bugs and logic errors\n"
            "- Anti-patterns and code smells\n"
            "- Performance issues\n"
            "- Security vulnerabilities\n"
            "- Readability and maintainability\n\n"
            "Be specific. Reference line numbers. Suggest fixes with code.\n"
            "Use the available tools to read files and fetch repository data."
        ),
        mcp_servers=[
            {"name": "github", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]},
            {"name": "filesystem", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]},
        ],
    ),
    "security_auditor": Agent(
        name="Security Auditor",
        description="Scans for OWASP Top 10, injection, XSS, secrets, and auth issues",
        icon="\U0001f6e1\ufe0f",
        system_prompt=(
            "You are a security auditor specializing in application security.\n"
            "Check for:\n"
            "- OWASP Top 10 vulnerabilities\n"
            "- Injection attacks (SQL, command, XSS)\n"
            "- Hardcoded secrets and credentials\n"
            "- Authentication and authorization flaws\n"
            "- Insecure dependencies\n\n"
            "Rate each finding: Critical / High / Medium / Low.\n"
            "Provide remediation steps for each issue.\n"
            "Use the available tools to fetch content and inspect repositories."
        ),
        mcp_servers=[
            {"name": "github", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]},
            {"name": "fetch", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-fetch"]},
        ],
    ),
    "researcher": Agent(
        name="Researcher",
        description="Researches topics, fetches web content, and synthesizes information",
        icon="\U0001f4da",
        system_prompt=(
            "You are a research assistant. Your job is to:\n"
            "- Fetch and analyze web content\n"
            "- Synthesize information from multiple sources\n"
            "- Provide citations and references\n"
            "- Summarize findings clearly\n\n"
            "Always cite your sources. Distinguish facts from opinions.\n"
            "Use the available tools to fetch web pages and save research notes."
        ),
        mcp_servers=[
            {"name": "fetch", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-fetch"]},
            {"name": "filesystem", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]},
        ],
    ),
    "bim_engineer": Agent(
        name="BIM Engineer",
        description="Works with building information models, Revit, and construction data",
        icon="\U0001f3d7\ufe0f",
        system_prompt=(
            "You are a BIM (Building Information Modeling) engineer.\n"
            "You specialize in:\n"
            "- Revit API and model manipulation\n"
            "- Construction document standards\n"
            "- Building code compliance\n"
            "- Clash detection and coordination\n"
            "- Detail library management\n\n"
            "When working with Revit, use the MCP bridge for direct model access.\n"
            "Reference AIA standards for document organization.\n"
            "Use the available tools to read and write project files."
        ),
        mcp_servers=[
            {"name": "filesystem", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]},
        ],
    ),
}


def classify_query(query: str) -> str:
    """Route a query to the best agent based on keywords."""
    query_lower = query.lower()

    security_keywords = ["security", "vulnerability", "owasp", "injection", "xss",
                         "csrf", "secret", "credential", "auth", "penetration"]
    code_keywords = ["review", "bug", "refactor", "code quality", "anti-pattern",
                     "lint", "test", "coverage", "pull request", "pr "]
    bim_keywords = ["revit", "bim", "wall", "floor plan", "sheet", "construction",
                    "building", "architecture", "detail", "annotation"]

    if any(kw in query_lower for kw in security_keywords):
        return "security_auditor"
    if any(kw in query_lower for kw in code_keywords):
        return "code_reviewer"
    if any(kw in query_lower for kw in bim_keywords):
        return "bim_engineer"
    return "researcher"


def mcp_tool_to_anthropic(tool) -> dict:
    """Convert an MCP tool definition to Anthropic's tool format."""
    return {
        "name": tool.name,
        "description": tool.description or "",
        "input_schema": tool.inputSchema,
    }


async def connect_mcp_servers(agent: Agent) -> tuple[AsyncExitStack, list[dict], dict[str, ClientSession]]:
    """Spawn MCP servers and collect their tools.

    Returns (exit_stack, tools_list, session_map) where session_map maps
    tool_name -> session for dispatching tool calls.
    """
    stack = AsyncExitStack()
    await stack.__aenter__()

    all_tools = []
    session_map = {}

    for srv_config in agent.mcp_servers:
        env = {**os.environ}
        if "env" in srv_config:
            env.update(srv_config["env"])

        params = StdioServerParameters(
            command=srv_config["command"],
            args=srv_config.get("args", []),
            env=env,
        )

        stdio_transport = await stack.enter_async_context(stdio_client(params))
        read_stream, write_stream = stdio_transport
        session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
        await session.initialize()

        result = await session.list_tools()
        for tool in result.tools:
            all_tools.append(mcp_tool_to_anthropic(tool))
            session_map[tool.name] = session

    return stack, all_tools, session_map


async def run_agent_async(client: Anthropic, agent: Agent, query: str, history: list) -> str:
    """Run a query through a specific agent with real MCP tool connections."""
    messages = history + [{"role": "user", "content": query}]

    if not agent.mcp_servers:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=agent.system_prompt,
            messages=messages,
        )
        return response.content[0].text

    stack, tools, session_map = await connect_mcp_servers(agent)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=agent.system_prompt,
            messages=messages,
            tools=tools,
        )

        # Agentic loop: handle tool calls until we get a final text response
        while response.stop_reason == "tool_use":
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            tool_results = []

            for tool_use in tool_use_blocks:
                session = session_map.get(tool_use.name)
                if session is None:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": f"Error: Unknown tool '{tool_use.name}'",
                        "is_error": True,
                    })
                    continue

                try:
                    result = await session.call_tool(tool_use.name, tool_use.input)
                    result_text = ""
                    for content in result.content:
                        if hasattr(content, "text"):
                            result_text += content.text
                        else:
                            result_text += str(content)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": result_text,
                    })
                except Exception as e:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": f"Error calling tool: {e}",
                        "is_error": True,
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=agent.system_prompt,
                messages=messages,
                tools=tools,
            )

        # Extract final text
        text_blocks = [b.text for b in response.content if hasattr(b, "text")]
        return "\n".join(text_blocks) if text_blocks else "No response generated."

    finally:
        await stack.aclose()


def run_agent(client: Anthropic, agent: Agent, query: str, history: list) -> str:
    """Sync wrapper around the async agent runner."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(run_agent_async(client, agent, query, history))
    finally:
        loop.close()


def main():
    st.markdown("# \u2692\ufe0f Agent Forge")
    st.markdown("**Specialized AI agents with MCP tool routing.** "
                "Each agent connects to different MCP servers based on its expertise.")

    # Sidebar
    with st.sidebar:
        st.header("\U0001f511 Configuration")
        api_key = st.text_input("Anthropic API Key", type="password",
                                help="Get yours at console.anthropic.com")
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key

        st.markdown("---")
        st.header("\U0001f916 Agents")
        for agent_id, agent in AGENTS.items():
            with st.expander(f"{agent.icon} {agent.name}"):
                st.markdown(f"**{agent.description}**")
                st.markdown(f"*System:* {agent.system_prompt[:100]}...")
                if agent.mcp_servers:
                    st.markdown("**MCP Servers:**")
                    for srv in agent.mcp_servers:
                        st.markdown(f"- `{srv['name']}`")

        st.markdown("---")
        st.markdown("Built with [cadre-ai](https://github.com/WeberG619/cadre-ai)")

    # Agent selection
    col1, col2 = st.columns([3, 1])
    with col2:
        mode = st.radio("Agent Selection", ["Auto-Route", "Manual"])
        if mode == "Manual":
            selected = st.selectbox(
                "Choose Agent",
                options=list(AGENTS.keys()),
                format_func=lambda x: f"{AGENTS[x].icon} {AGENTS[x].name}",
            )

    # Chat history per agent
    if "histories" not in st.session_state:
        st.session_state.histories = {k: [] for k in AGENTS}
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar=msg.get("avatar")):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask anything..."):
        if not api_key:
            st.error("Please enter your Anthropic API key in the sidebar.")
            return

        # Route to agent
        if mode == "Auto-Route":
            agent_id = classify_query(prompt)
        else:
            agent_id = selected

        agent = AGENTS[agent_id]

        # Show user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Show routing info
        with st.chat_message("assistant", avatar=agent.icon):
            st.caption(f"Routed to **{agent.icon} {agent.name}**")
            tools_info = ", ".join(s["name"] for s in agent.mcp_servers)
            st.caption(f"MCP servers: {tools_info}" if tools_info else "No MCP servers")

            client = Anthropic(api_key=api_key)
            with st.spinner(f"{agent.name} is connecting to MCP servers..."):
                response = run_agent(
                    client, agent, prompt,
                    st.session_state.histories[agent_id],
                )

            st.markdown(response)

        # Update history
        st.session_state.histories[agent_id].append(
            {"role": "user", "content": prompt}
        )
        st.session_state.histories[agent_id].append(
            {"role": "assistant", "content": response}
        )
        st.session_state.messages.append(
            {"role": "assistant", "content": response, "avatar": agent.icon}
        )


if __name__ == "__main__":
    main()
