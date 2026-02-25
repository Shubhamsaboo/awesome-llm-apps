"""Multi-MCP Agent Forge - Specialized agents with MCP tool routing.

Each agent connects to different MCP servers based on its domain expertise.
This demonstrates the pattern of routing queries to specialized agents
rather than giving one agent access to all tools.

Inspired by: https://github.com/WeberG619/cadre-ai
"""

import asyncio
import os
from dataclasses import dataclass, field
from typing import Optional

import streamlit as st
from anthropic import Anthropic

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
            "Be specific. Reference line numbers. Suggest fixes with code."
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
            "Provide remediation steps for each issue."
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
            "Always cite your sources. Distinguish facts from opinions."
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
            "Reference AIA standards for document organization."
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


def run_agent(client: Anthropic, agent: Agent, query: str, history: list) -> str:
    """Run a query through a specific agent using Claude."""
    messages = history + [{"role": "user", "content": query}]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=agent.system_prompt,
        messages=messages,
    )

    return response.content[0].text


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

            client = Anthropic(api_key=api_key)
            with st.spinner(f"{agent.name} is thinking..."):
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
