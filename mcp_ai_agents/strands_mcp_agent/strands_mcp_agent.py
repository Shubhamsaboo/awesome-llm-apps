"""Strands MCP Agent: a Streamlit app that answers questions about the Strands
Agents SDK using a Strands agent connected to the Strands documentation MCP
server over stdio.

SPDX-License-Identifier: Apache-2.0
"""
import os

import streamlit as st
from mcp import StdioServerParameters, stdio_client
from strands import Agent
from strands.models.openai import OpenAIModel
from strands.tools.mcp import MCPClient

st.set_page_config(page_title="🧵 Strands MCP Agent", page_icon="🧵", layout="wide")

st.title("🧵 Strands MCP Agent")
st.markdown(
    "Ask questions about the Strands Agents SDK. The agent connects to the "
    "Strands documentation MCP server over stdio, discovers its tools, and "
    "calls them to answer."
)

with st.sidebar:
    st.header("🔑 Configuration")
    openai_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Used by the agent to reason and call MCP tools.",
    )
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key

    model_id = st.selectbox(
        "Model",
        ["gpt-4o-mini", "gpt-4o"],
        index=0,
    )

    st.markdown("---")
    st.markdown("### How it works")
    st.markdown(
        "- Runs the `strands-agents-mcp-server` locally with `uvx`\n"
        "- The Strands `MCPClient` connects over stdio and lists the server tools\n"
        "- The agent (OpenAI model) picks and calls `search_docs` and `fetch_doc`"
    )
    st.caption("Requires uv installed so that uvx can launch the MCP server.")

st.markdown("### Example questions")
examples = [
    "How do I connect a Strands agent to an MCP server over stdio?",
    "What transports does the Strands MCP client support?",
    "How do I use the OpenAI model provider in Strands?",
]
for example in examples:
    st.markdown(f"- {example}")

query = st.text_area(
    "Your question",
    placeholder="Ask about building agents with Strands...",
)


def run_strands_agent(question: str, model_name: str) -> str:
    """Run a Strands agent wired to the Strands docs MCP server over stdio."""
    if not os.getenv("OPENAI_API_KEY"):
        return "Error: OpenAI API key not provided."

    model = OpenAIModel(
        client_args={"api_key": os.environ["OPENAI_API_KEY"]},
        model_id=model_name,
        params={"temperature": 0.2},
    )

    # Launch the Strands documentation MCP server as a local subprocess.
    mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="uvx",
                args=["strands-agents-mcp-server"],
            )
        )
    )

    # MCP tools must be used inside the client context.
    with mcp_client:
        tools = mcp_client.list_tools_sync()
        agent = Agent(
            model=model,
            tools=tools,
            system_prompt=(
                "You are a helpful assistant for the Strands Agents SDK. "
                "Use the documentation tools to find accurate answers and cite "
                "the doc pages you used. If the docs do not cover something, "
                "say so instead of guessing."
            ),
        )
        response = agent(question)
        return str(response)


if st.button("🚀 Ask", type="primary", use_container_width=True):
    if not openai_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
    elif not query:
        st.error("Please enter a question.")
    else:
        with st.spinner("Connecting to the MCP server and reasoning..."):
            try:
                answer = run_strands_agent(query, model_id)
            except Exception as exc:  # surface setup errors to the user
                answer = f"Error: {exc}"
        st.markdown("### Answer")
        st.markdown(answer)
