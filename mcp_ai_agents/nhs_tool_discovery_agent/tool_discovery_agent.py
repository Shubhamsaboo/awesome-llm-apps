"""AI Tool Discovery Agent — find agent-ready APIs and services via MCP.

Connects to the Not Human Search MCP server (https://nothumansearch.ai/mcp)
over streamable-HTTP transport. The agent can search 1,750+ indexed sites,
check agentic readiness scores, and verify MCP endpoints — all through
natural language queries in a Streamlit UI.

Tools provided by Not Human Search MCP:
  - search_agents: keyword/category search ranked by agentic readiness score
  - check_score: get the agentic readiness report for a specific domain
  - get_stats: index-wide statistics
  - submit_site: submit a new URL for crawling
  - verify_mcp: live JSON-RPC probe of any MCP endpoint
"""

import asyncio
import json
import os

import streamlit as st
from anthropic import Anthropic
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

MCP_ENDPOINT = "https://nothumansearch.ai/mcp"

st.set_page_config(
    page_title="AI Tool Discovery Agent",
    page_icon="🔍",
    layout="wide",
)


def mcp_tool_to_anthropic(tool) -> dict:
    """Convert an MCP tool definition to Anthropic's tool format."""
    return {
        "name": tool.name,
        "description": tool.description or "",
        "input_schema": tool.inputSchema,
    }


async def run_agent_async(api_key: str, query: str) -> str:
    """Connect to the NHS MCP server and run a tool-augmented conversation."""
    client = Anthropic(api_key=api_key)

    async with streamablehttp_client(MCP_ENDPOINT) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Discover available tools
            result = await session.list_tools()
            tools = [mcp_tool_to_anthropic(t) for t in result.tools]

            system_prompt = (
                "You are an AI tool discovery assistant. You help developers and AI agents "
                "find APIs, services, and tools that are ready for agentic use.\n\n"
                "Use the available MCP tools to:\n"
                "- Search for agent-ready services by keyword or category\n"
                "- Check the agentic readiness score of specific domains\n"
                "- Verify whether a site has a working MCP endpoint\n"
                "- Get statistics about the indexed agentic web\n\n"
                "When presenting results:\n"
                "- Show the agentic score (0-100) for each result\n"
                "- Highlight key signals: llms.txt, OpenAPI, MCP, structured API\n"
                "- Use markdown tables for multi-result queries\n"
                "- Provide the domain URL so users can visit the service\n"
                "- Be concise but informative"
            )

            messages = [{"role": "user", "content": query}]

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
                tools=tools,
            )

            # Agentic loop — handle tool calls until we get a final text response
            while response.stop_reason == "tool_use":
                tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
                tool_results = []

                for tool_use in tool_use_blocks:
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
                    system=system_prompt,
                    messages=messages,
                    tools=tools,
                )

            text_blocks = [b.text for b in response.content if hasattr(b, "text")]
            return "\n".join(text_blocks) if text_blocks else "No response generated."


def main():
    st.markdown("# 🔍 AI Tool Discovery Agent")
    st.markdown(
        "**Find agent-ready APIs and services using natural language.** "
        "Powered by [Not Human Search](https://nothumansearch.ai) MCP server — "
        "1,750+ sites indexed and scored for agentic readiness."
    )

    with st.sidebar:
        st.header("🔑 Configuration")
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            help="Get yours at console.anthropic.com",
        )

        st.markdown("---")
        st.header("💡 Example Queries")

        st.markdown("**Find services**")
        st.markdown("- Find payment APIs for AI agents")
        st.markdown("- What ecommerce platforms have MCP servers?")
        st.markdown("- Show me agent-ready weather data APIs")

        st.markdown("**Check readiness**")
        st.markdown("- What's the agentic readiness score for stripe.com?")
        st.markdown("- Does github.com have an MCP server?")
        st.markdown("- Check if openai.com publishes llms.txt")

        st.markdown("**Explore the index**")
        st.markdown("- How many sites are indexed?")
        st.markdown("- What category has the highest average score?")
        st.markdown("- Show me the top AI tools with MCP support")

        st.markdown("---")
        st.caption(
            "This agent connects to the Not Human Search MCP server "
            "over streamable-HTTP — no Docker or local servers required."
        )

    query = st.text_area(
        "What tools or APIs are you looking for?",
        placeholder="e.g., Find payment APIs that AI agents can use",
    )

    if st.button("🚀 Search", type="primary", use_container_width=True):
        if not api_key:
            st.error("Please enter your Anthropic API key in the sidebar.")
            return
        if not query:
            st.error("Please enter a query.")
            return

        with st.spinner("Connecting to Not Human Search MCP server..."):
            try:
                result = asyncio.run(run_agent_async(api_key, query))
            except Exception as e:
                st.error(f"Error: {e}")
                return

        st.markdown("### Results")
        st.markdown(result)

    if "result" not in dir():
        st.markdown(
            """
            <div style="padding: 1.5rem; border-radius: 0.5rem;
                        background-color: #f0f2f6; margin-top: 1rem;">
            <h4>How it works</h4>
            <ol>
                <li>Enter your <strong>Anthropic API key</strong> in the sidebar</li>
                <li>Type a natural language query about tools or APIs you need</li>
                <li>The agent connects to the Not Human Search MCP server</li>
                <li>It searches 1,750+ indexed sites ranked by agentic readiness</li>
                <li>Results include scores, signals (llms.txt, OpenAPI, MCP), and links</li>
            </ol>
            <p><strong>Agentic readiness score (0-100)</strong> is based on 7 signals:
            llms.txt, ai-plugin.json, OpenAPI specs, structured APIs, MCP servers,
            robots.txt AI rules, and Schema.org markup.</p>
            <p><strong>No Docker required</strong> — this agent uses streamable-HTTP
            transport to connect directly to the remote MCP server.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
