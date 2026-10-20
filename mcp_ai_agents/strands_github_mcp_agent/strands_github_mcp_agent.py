"""GitHub MCP Agent built with Strands: a Streamlit app that explores a GitHub
repository in plain English. An agent built with the Strands Agents SDK connects
to the official GitHub MCP server over HTTP, discovers the server's tools, and
calls them to answer questions about issues, pull requests, and repository
activity.

SPDX-License-Identifier: Apache-2.0
"""
import os

import streamlit as st
from strands import Agent
from strands.models.openai import OpenAIModel
from strands.tools.mcp import MCPClient

# GitHub's official hosted MCP server. No local setup needed.
GITHUB_MCP_URL = "https://api.githubcopilot.com/mcp/"

st.set_page_config(page_title="🧶 GitHub MCP Agent with Strands", page_icon="🧶", layout="wide")

st.title("🧶 GitHub MCP Agent with Strands")
st.markdown(
    "Ask questions about a GitHub repository in plain English. The agent connects "
    "to the official GitHub MCP server, discovers its tools, and calls them to "
    "answer."
)

with st.sidebar:
    st.header("🔑 Configuration")

    # Widgets carry a key, so Streamlit keeps their values in session_state
    # across the reruns that every button click triggers.
    openai_key = st.text_input(
        "OpenAI API Key",
        type="password",
        key="openai_key",
        help="Used by the agent to reason and call the MCP tools.",
    )
    github_token = st.text_input(
        "GitHub Token",
        type="password",
        key="github_token",
        help="Create a token with repo scope at github.com/settings/tokens",
    )
    model_id = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o"], index=0, key="model_id")

    st.markdown("---")
    st.markdown("### How it works")
    st.markdown(
        "- Connects to GitHub's official hosted MCP server over HTTP\n"
        "- The Strands `MCPClient` lists the server tools at runtime\n"
        "- The agent (OpenAI model) picks and calls the GitHub tools, then answers"
    )

st.markdown("### Example questions")
examples = [
    "What issues are open and labeled bug in Shubhamsaboo/awesome-llm-apps?",
    "Which pull requests are waiting for review?",
    "Summarize the repository activity over the last month.",
]
for example in examples:
    st.markdown(f"- {example}")

col1, col2 = st.columns([3, 1])
with col1:
    repo = st.text_input(
        "Repository",
        value="Shubhamsaboo/awesome-llm-apps",
        key="repo",
        help="Format: owner/repo",
    )
with col2:
    query_type = st.selectbox(
        "Query type",
        ["Issues", "Pull Requests", "Repository Activity", "Custom"],
        key="query_type",
    )

query = st.text_area(
    "Your question",
    key="query",
    placeholder="What would you like to know about this repository?",
)


def run_github_agent(question: str, model_name: str, openai_api_key: str, gh_token: str) -> str:
    """Run an agent built with Strands, wired to the GitHub MCP server over HTTP."""
    model = OpenAIModel(
        client_args={"api_key": openai_api_key},
        model_id=model_name,
        params={"temperature": 0.2},
    )

    # Connect to GitHub's hosted MCP server. The Strands MCPClient builds the
    # streamable HTTP transport from the url and auth header.
    mcp_client = MCPClient(
        url=GITHUB_MCP_URL,
        headers={"Authorization": f"Bearer {gh_token}"},
    )

    # MCP tools must be used inside the client context.
    with mcp_client:
        tools = mcp_client.list_tools_sync()
        agent = Agent(
            model=model,
            tools=tools,
            system_prompt=(
                "You are a GitHub assistant. Answer questions about a repository "
                "using the GitHub tools. Stay with the facts the tools return, "
                "present numbers in a table when it helps, and link to the "
                "relevant GitHub pages. If the tools do not cover something, say "
                "so instead of guessing."
            ),
        )
        response = agent(question)
        return str(response)


if st.button("🚀 Ask", type="primary", use_container_width=True):
    if not openai_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
    elif not github_token:
        st.error("Please enter your GitHub token in the sidebar.")
    elif not query:
        st.error("Please enter a question.")
    else:
        full_query = query if repo in query else f"{query} in {repo}"
        with st.spinner("Connecting to the MCP server and reasoning..."):
            try:
                answer = run_github_agent(full_query, model_id, openai_key, github_token)
            except Exception as exc:  # surface setup errors to the user
                answer = f"Error: {exc}"
        st.markdown("### Answer")
        st.markdown(answer)
