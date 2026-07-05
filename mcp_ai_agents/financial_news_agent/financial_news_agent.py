import asyncio
import os
from textwrap import dedent

import streamlit as st
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters

# AlphaAI's hosted MCP server — relevance-scored, ticker-linked financial news
# (GDELT + SEC EDGAR) exposed over Streamable HTTP with OAuth 2.1. We reach it
# through `mcp-remote`, the stdio<->remote bridge that also drives the one-time
# OAuth browser handshake and caches the token locally.
MCP_URL = "https://mcp.alphai.io/mcp"

st.set_page_config(page_title="📈 Financial News MCP Agent", page_icon="📈", layout="wide")

st.markdown("<h1 class='main-header'>📈 Financial News MCP Agent</h1>", unsafe_allow_html=True)
st.markdown(
    "Ask for market-moving news in plain English. Powered by the "
    "[AlphaAI](https://alphai.io) MCP server — every article is pre-scored for "
    "per-ticker relevance (1-10) and category, with SEC Form 4 insider filings as "
    "structured data — all via the Model Context Protocol."
)

with st.sidebar:
    st.header("🔑 Authentication")

    openai_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Required for the AI agent to interpret queries and format results",
    )
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key

    st.markdown("---")
    st.markdown("### 🔗 AlphaAI MCP server")
    st.caption(
        "No key to paste. On the first query a browser tab opens for AlphaAI "
        "OAuth — sign in or create a **free** account (no credit card). "
        "`mcp-remote` caches the token, so later runs skip the prompt."
    )
    st.markdown(
        "Free tier: **20 requests/min · 100/day**. "
        "Get an account at [alphai.io](https://alphai.io) · "
        "[MCP docs](https://alphai.io/mcp)"
    )

    st.markdown("---")
    st.markdown("### 💡 Example Queries")
    st.markdown("- What's the latest news on NVDA?")
    st.markdown("- Show me today's top trending market stories")
    st.markdown("- Any recent SEC Form 4 insider buying in energy names?")
    st.markdown("- Summarize high-relevance news about Tesla this week")

    st.markdown("---")
    st.caption("Tip: mention a ticker (e.g. AAPL, MSFT) for the sharpest results.")

query = st.text_area(
    "Your Query",
    value="What are the most relevant news stories on NVDA right now?",
    placeholder="What would you like to know about the market?",
)


async def run_financial_news_agent(message: str) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        return "Error: OpenAI API key not provided"

    # `mcp-remote` (npx) bridges the remote OAuth-protected MCP server to a local
    # stdio transport and handles the OAuth 2.1 flow on first connect.
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "mcp-remote", MCP_URL],
        env={**os.environ},
    )

    try:
        async with MCPTools(server_params=server_params) as mcp_tools:
            agent = Agent(
                tools=[mcp_tools],
                instructions=dedent("""\
                    You are a financial-news analyst assistant backed by the AlphaAI MCP server.
                    - Use the AlphaAI tools to fetch relevance-scored, ticker-linked news.
                    - Lead with the highest-relevance stories; mention the 1-10 relevance score.
                    - Group by ticker or category when it aids clarity.
                    - For insider questions, use the SEC Form 4 tools and report direction, role, and value.
                    - Be concise and factual; use markdown, and tables for numeric data.
                    - Do not invent tickers, prices, or figures beyond what the tools return.
                """),
                markdown=True,
            )
            response: RunOutput = await asyncio.wait_for(agent.arun(message), timeout=180.0)
            return response.content

    except asyncio.TimeoutError:
        return "Error: Request timed out after 180 seconds"
    except Exception as e:
        return f"Error: {str(e)}"


if st.button("🚀 Run Query", type="primary", use_container_width=True):
    if not openai_key:
        st.error("Please enter your OpenAI API key in the sidebar")
    elif not query:
        st.error("Please enter a query")
    else:
        with st.spinner("Fetching and analyzing financial news via the AlphaAI MCP server..."):
            result = asyncio.run(run_financial_news_agent(query))

        st.markdown("### Results")
        st.markdown(result)

if "result" not in locals():
    st.markdown(
        """<div class='info-box'>
        <h4>How to use this app:</h4>
        <ol>
            <li>Enter your <strong>OpenAI API key</strong> in the sidebar (powers the AI agent)</li>
            <li>Make sure <strong>Node.js</strong> is installed (needed for <code>npx mcp-remote</code>)</li>
            <li>Type a question about the market, or pick an example query</li>
            <li>Click 'Run Query' — on the first run a browser tab opens for AlphaAI OAuth (free account, no card)</li>
        </ol>
        <p><strong>How it works:</strong></p>
        <ul>
            <li>Connects to AlphaAI's hosted <strong>MCP server</strong> (Streamable HTTP + OAuth 2.1) via <code>mcp-remote</code></li>
            <li>The AI agent (OpenAI) interprets your query and calls the right AlphaAI tools — news search, trending, per-ticker feeds, SEC Form 4 insider news</li>
            <li>Every article is pre-analyzed at ingest with a 1-10 relevance score, a category, and per-ticker impact</li>
            <li>Results come back as readable markdown with the relevance signal surfaced</li>
        </ul>
        </div>""",
        unsafe_allow_html=True,
    )
