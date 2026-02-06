import asyncio
import os

import streamlit as st
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters

st.set_page_config(page_title="📧 Email MCP Agent", page_icon="📧", layout="wide")

st.markdown("# 📧 Email MCP Agent")
st.markdown(
    "Give your AI agent its own email address — create inboxes, send and receive emails, "
    "search threads, and manage attachments using natural language via "
    "[NornWeave](https://github.com/DataCovey/nornweave)."
)

# --- Sidebar: credentials and examples ---
with st.sidebar:
    st.header("🔑 Configuration")

    openai_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Required for the AI agent. Get one at platform.openai.com/api-keys",
    )
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key

    api_url = st.text_input(
        "NornWeave API URL",
        value="http://localhost:8000",
        help="URL of your running NornWeave server",
    )

    api_key = st.text_input(
        "NornWeave API Key",
        type="password",
        help="Optional API key if your NornWeave server requires auth",
    )

    st.markdown("---")
    st.markdown("### Example Queries")

    st.markdown("**Inboxes**")
    st.markdown('- Create an inbox called "Support Bot"')
    st.markdown("- List my inboxes")

    st.markdown("**Sending**")
    st.markdown('- Send an email to bob@example.com saying "Hello!"')
    st.markdown("- Reply to thread th_123 with a summary")

    st.markdown("**Reading & Search**")
    st.markdown("- Show me recent threads in inbox ibx_456")
    st.markdown('- Search for emails about "pricing" in inbox ibx_456')
    st.markdown("- List attachments in thread th_789")

    st.markdown("**Advanced**")
    st.markdown("- Wait for a reply in thread th_123")

# --- Main area ---
query = st.text_area(
    "What would you like to do?",
    placeholder="e.g., Create an inbox named 'Sales Agent' with username 'sales'",
)


async def run_email_agent(message: str) -> str:
    """Connect to NornWeave MCP server and run the agent."""
    env = {**os.environ, "NORNWEAVE_API_URL": api_url}
    if api_key:
        env["NORNWEAVE_API_KEY"] = api_key

    server_params = StdioServerParameters(
        command="nornweave",
        args=["mcp"],
        env=env,
    )

    async with MCPTools(server_params=server_params) as mcp_tools:
        agent = Agent(
            model=OpenAIChat(id="gpt-4o"),
            tools=[mcp_tools],
            instructions=(
                "You are an email assistant powered by NornWeave. You can:\n"
                "- Create inboxes (email addresses) for agents\n"
                "- Send emails (Markdown body auto-converts to HTML)\n"
                "- Search and list messages in inboxes and threads\n"
                "- List and retrieve attachments\n"
                "- Wait for replies in a thread\n\n"
                "Always confirm what you did after each action. "
                "Use markdown formatting for readability."
            ),
            markdown=True,
        )

        response = await asyncio.wait_for(agent.arun(message), timeout=120.0)
        return response.content


if st.button("🚀 Run", type="primary", use_container_width=True):
    if not openai_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
    elif not query:
        st.error("Please enter a query.")
    else:
        with st.spinner("Working on it..."):
            try:
                result = asyncio.run(run_email_agent(query))
                st.markdown("### Result")
                st.markdown(result)
            except asyncio.TimeoutError:
                st.error("Request timed out after 120 seconds.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- How it works (shown when idle) ---
if "result" not in dir():
    st.markdown(
        """
---

### How it works

1. **NornWeave** runs as a self-hosted API server that gives AI agents their own
   email addresses, with threading, Markdown parsing, and semantic search built in.
2. The **NornWeave MCP server** (`nornweave mcp`) exposes email operations
   as MCP tools: `create_inbox`, `send_email`, `search_email`, `list_messages`,
   `wait_for_reply`, `list_attachments`, and more.
3. This app connects an **OpenAI-powered agent** to those tools via the
   Model Context Protocol, so you can manage email entirely through conversation.

### Prerequisites

- A running NornWeave server (`pip install nornweave && nornweave api`)
- NornWeave MCP extras installed (`pip install nornweave[mcp]`)
- An OpenAI API key
"""
    )
