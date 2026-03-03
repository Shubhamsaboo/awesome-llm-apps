import asyncio
import os
import streamlit as st
from agno.agent import Agent
from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters

st.set_page_config(page_title="DeFi MCP Agent", page_icon="", layout="wide")

st.markdown("# DeFi MCP Agent")
st.markdown("Query crypto prices, wallet balances, gas fees, and DEX quotes using natural language.")

with st.sidebar:
    st.header("Configuration")

    openai_key = st.text_input("OpenAI API Key", type="password",
                               help="Required for the AI agent")
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key

    st.markdown("---")
    st.markdown("### Example Queries")
    example_queries = [
        "What is the current price of ETH?",
        "Show me the top 10 tokens by market cap",
        "What is the ETH balance of vitalik.eth?",
        "Get current gas prices on Ethereum",
        "Get a DEX quote for swapping 1 ETH to USDC",
        "Compare gas prices across all chains",
    ]
    for q in example_queries:
        st.code(q, language=None)


async def run_agent(query: str):
    """Run the DeFi MCP agent with the given query."""
    server_params = StdioServerParameters(
        command="node",
        args=["../defi-mcp/src/index.js"],
    )

    async with MCPTools(server_params=server_params) as mcp_tools:
        agent = Agent(
            name="DeFi Agent",
            instructions=[
                "You are a DeFi research assistant.",
                "Use the available MCP tools to fetch real-time crypto data.",
                "Format numbers clearly (prices with $, large numbers with commas).",
                "When showing wallet balances, include the USD value if possible.",
            ],
            tools=[mcp_tools],
            model="gpt-4o",
            markdown=True,
        )
        response = await agent.arun(query)
        return response.content


query = st.text_input("Ask about DeFi:", placeholder="e.g., What is the price of Bitcoin?")

if st.button("Run Query", type="primary", disabled=not query or not openai_key):
    if not openai_key:
        st.warning("Please enter your OpenAI API key in the sidebar.")
    elif query:
        with st.spinner("Querying DeFi data..."):
            result = asyncio.run(run_agent(query))
            st.markdown(result)
