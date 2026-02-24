import asyncio
import os
import streamlit as st
from textwrap import dedent

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from mcp_agent.workflows.llm.augmented_llm import RequestParams

st.set_page_config(
    page_title="Scientific Research MCP Agent",
    page_icon="🔬",
    layout="wide",
)

st.markdown(
    "<h1 class='main-header'>🔬 Scientific Research MCP Agent</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "Search scientific papers and get structured experimental data from full-text studies using the BGPT MCP server."
)

with st.sidebar:
    st.markdown("### Example Queries")
    st.markdown("**Literature Search**")
    st.markdown("- Find papers about CRISPR gene editing efficiency")
    st.markdown("- Search for studies on mRNA vaccine immunogenicity")

    st.markdown("**Evidence Synthesis**")
    st.markdown("- Compare sample sizes across CAR-T therapy trials")
    st.markdown("- What methods are used to measure antibody responses?")

    st.markdown("**Deep Dives**")
    st.markdown("- Find papers with quality scores above 8 on checkpoint inhibitors")
    st.markdown("- Summarize the limitations reported in Alzheimer's drug trials")

app = MCPApp(name="scientific_research_agent")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


async def run_agent(query: str):
    async with app.run() as research_app:
        context = research_app.context
        agent = Agent(
            name="research_agent",
            instruction=dedent("""\
                You are a scientific research assistant with access to a database of
                scientific papers via the BGPT MCP server. When the user asks about
                a research topic:

                1. Search for relevant papers using the search_papers tool
                2. Analyze the structured results (methods, results, sample sizes, quality scores)
                3. Synthesize findings into a clear, evidence-based response
                4. Cite specific papers with their DOIs when available
                5. Highlight key quantitative findings and methodological details

                Always present results in a structured format. Note limitations and
                quality scores when relevant. If the free tier limit is reached,
                let the user know they can get an API key at https://bgpt.pro/mcp
            """),
            server_names=["bgpt"],
        )

        async with agent:
            llm = await agent.attach_llm(OpenAIAugmentedLLM)
            result = await llm.generate_str(
                message=query,
                request_params=RequestParams(model="gpt-4o-mini"),
            )
            return result


if prompt := st.chat_input("Ask about scientific research..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching scientific papers..."):
            response = asyncio.run(run_agent(prompt))
            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
