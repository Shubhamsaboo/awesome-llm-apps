import asyncio
import os
import streamlit as st
from textwrap import dedent
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.tools.mcp import MCPTools
from mcp.client.streamable_http import streamablehttp_client

st.set_page_config(page_title="Earth Memory Agent", page_icon="🌍", layout="wide")

st.markdown("<h1 class='main-header'>🌍 Earth Memory Agent</h1>", unsafe_allow_html=True)
st.markdown("Ask place-based questions and get signed geospatial facts from emem")

with st.sidebar:
    st.header("🔑 Authentication")

    openai_key = st.text_input("OpenAI API Key", type="password",
                              help="Required for the AI agent to interpret queries and format results")
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key

    st.markdown("---")
    st.markdown("### Example Queries")

    st.markdown("**Elevation**")
    st.markdown("- What is the elevation at Helsinki-Vantaa Airport?")
    st.markdown("- Check elevation for downtown Miami, Florida")

    st.markdown("**Flood risk**")
    st.markdown("- Does Helsinki-Vantaa Airport have surface water or flood signals?")
    st.markdown("- Is downtown New Orleans at flood risk?")

    st.markdown("**Land cover**")
    st.markdown("- What is the land cover around Lake Erie, Ohio?")
    st.markdown("- Has vegetation changed near the Amazon river?")

    st.markdown("**Signed evidence**")
    st.markdown("- Give me signed geospatial facts for downtown San Francisco")
    st.markdown("- What evidence supports a flood risk assessment for Miami Beach?")

    st.markdown("---")
    st.caption("emem is a public MCP server. No API key or signup needed for geospatial queries.")

place = st.text_input("Place", value="Helsinki-Vantaa Airport, Finland",
                      help="Any place name, address, or coordinates")

query_type = st.selectbox("Query Type", [
    "Elevation check", "Flood risk assessment", "Land cover analysis",
    "Signed geospatial facts", "Custom"
])

if query_type == "Elevation check":
    query_template = f"What is the elevation at {place}? Include any signed fact CIDs."
elif query_type == "Flood risk assessment":
    query_template = f"Check {place} for elevation and surface water signals relevant to flood risk. Include signed receipts."
elif query_type == "Land cover analysis":
    query_template = f"What is the land cover and vegetation status around {place}?"
elif query_type == "Signed geospatial facts":
    query_template = f"What signed geospatial facts are available for {place}? Return all fact CIDs and receipts."
else:
    query_template = ""

query = st.text_area("Your Query", value=query_template,
                     placeholder="What would you like to know about this place?")


async def run_emem_agent(message):
    if not os.getenv("OPENAI_API_KEY"):
        return "Error: OpenAI API key not provided"

    try:
        async with streamablehttp_client("https://emem.dev/mcp") as (read, write, _):
            async with MCPTools(read_stream=read, write_stream=write) as mcp_tools:
                agent = Agent(
                    tools=[mcp_tools],
                    instructions=dedent("""\
                        You are a geospatial research assistant. You help users understand
                        real-world places using signed geospatial facts from emem.
                        - Always include fact CIDs or receipts when available
                        - Present elevation, surface water, vegetation, and land cover data clearly
                        - Use markdown formatting for readability
                        - When assessing risk, cite the specific signals and evidence
                        - Be direct about what the data shows and what it does not
                    """),
                    markdown=True,
                )

                response: RunOutput = await asyncio.wait_for(agent.arun(message), timeout=120.0)
                return response.content

    except asyncio.TimeoutError:
        return "Error: Request timed out after 120 seconds"
    except Exception as e:
        return f"Error: {str(e)}"


if st.button("🚀 Run Query", type="primary", use_container_width=True):
    if not openai_key:
        st.error("Please enter your OpenAI API key in the sidebar")
    elif not query:
        st.error("Please enter a query")
    else:
        with st.spinner("Querying Earth memory..."):
            result = asyncio.run(run_emem_agent(query))

        st.markdown("### Results")
        st.markdown(result)

if "result" not in locals():
    st.markdown(
        """<div class='info-box'>
        <h4>How to use this app:</h4>
        <ol>
            <li>Enter your <strong>OpenAI API key</strong> in the sidebar (powers the AI agent)</li>
            <li>Enter a place name, address, or coordinates</li>
            <li>Select a query type or write your own</li>
            <li>Click 'Run Query' to see signed geospatial facts</li>
        </ol>
        <p><strong>How it works:</strong></p>
        <ul>
            <li>Uses <a href="https://github.com/Vortx-AI/emem">emem</a>, a public MCP server for signed geospatial facts</li>
            <li>AI Agent (powered by OpenAI) interprets your query and calls emem tools</li>
            <li>emem returns elevation, surface water, vegetation, land cover, and built-up context</li>
            <li>Every fact comes with a content-addressed CID and receipt for verification</li>
        </ul>
        </div>""",
        unsafe_allow_html=True
    )
