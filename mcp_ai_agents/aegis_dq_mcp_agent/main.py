"""Aegis DQ MCP Agent — agentic data quality validation with LLM diagnosis."""

import asyncio
import os
from pathlib import Path

import streamlit as st
from mcp_agent.agents.agent import Agent
from mcp_agent.app import MCPApp
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

from setup_demo_db import setup_demo_db

RULES_PATH = str(Path(__file__).parent / "sample_rules.yaml")
DB_PATH = "/tmp/aegis_demo.duckdb"

st.set_page_config(page_title="Aegis DQ Agent", page_icon="🛡️", layout="wide")

st.markdown("<h1>🛡️ Aegis DQ MCP Agent</h1>", unsafe_allow_html=True)
st.markdown(
    "Ask the agent to validate your data, diagnose failures, and propose SQL fixes — "
    "powered by [Aegis DQ](https://github.com/aegis-dq/aegis-dq) via MCP."
)

with st.sidebar:
    st.markdown("### 🗄️ Demo Dataset")
    st.markdown("A sample `orders` table is pre-loaded with **intentional data quality issues**:")
    st.markdown("- ❌ Negative order amount")
    st.markdown("- ❌ NULL customer_id")
    st.markdown("- ❌ Invalid status (`refunded`)")
    st.markdown("- ❌ Duplicate order_id")
    st.markdown("- ❌ NULL amount")
    st.markdown("---")
    st.markdown("### 💬 Example Prompts")
    st.markdown("**Run validation**")
    st.code(f"Run the rules at {RULES_PATH} against DuckDB with no LLM and tell me what failed.", language=None)
    st.markdown("**Audit trail**")
    st.code("Show me the last 5 validation runs.", language=None)
    st.markdown("**Search decisions**")
    st.code("Search the audit trail for anything about null customer IDs.", language=None)
    st.markdown("---")
    st.caption("Built with [Aegis DQ](https://aegis-dq.dev) + [MCP-Agent](https://github.com/lastmile-ai/mcp-agent)")

# Seed the demo database on first load
if "db_ready" not in st.session_state:
    setup_demo_db(DB_PATH)
    st.session_state.db_ready = True

query = st.text_area(
    "Your Question",
    placeholder=f"Run the rules at {RULES_PATH} against DuckDB with no LLM and tell me what failed.",
    height=100,
)

# Session state init
if "initialized" not in st.session_state:
    st.session_state.initialized = False
    st.session_state.mcp_app = MCPApp(name="aegis_dq_agent")
    st.session_state.mcp_context = None
    st.session_state.mcp_agent_app = None
    st.session_state.agent = None
    st.session_state.llm = None
    st.session_state.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state.loop)
    st.session_state.is_processing = False
    st.session_state.last_result = None


async def setup_agent():
    if not st.session_state.initialized:
        try:
            st.session_state.mcp_context = st.session_state.mcp_app.run()
            st.session_state.mcp_agent_app = await st.session_state.mcp_context.__aenter__()

            st.session_state.agent = Agent(
                name="aegis-dq-agent",
                instruction="""You are a data quality expert powered by Aegis DQ tools.

Your job is to help users validate their data, understand failures, and propose fixes.

When asked to run validation:
1. Call run_validation with the provided rules_path, warehouse="duckdb", no_llm=True for fast checks
2. Parse the JSON result and present failures clearly — group by severity
3. For each failure explain: what rule failed, which table/column, and what the issue means

When asked about past runs:
1. Call list_runs to get recent run IDs
2. Use get_run_report to retrieve full details

When asked to search:
1. Use search_decisions with relevant keywords

Always present results in clear markdown with tables where appropriate.
Highlight CRITICAL and HIGH severity failures prominently.""",
                server_names=["aegis-dq"],
            )

            await st.session_state.agent.initialize()
            st.session_state.llm = await st.session_state.agent.attach_llm(OpenAIAugmentedLLM)
            st.session_state.initialized = True
        except Exception as e:
            return f"Error during initialization: {str(e)}"
    return None


async def run_agent(message: str) -> str:
    if not os.getenv("OPENAI_API_KEY") and not os.path.exists(
        os.path.join(os.path.dirname(__file__), "mcp_agent.secrets.yaml")
    ):
        return (
            "⚠️ No LLM credentials found. Either set `OPENAI_API_KEY` in your environment, "
            "or copy `mcp_agent.secrets.yaml.example` to `mcp_agent.secrets.yaml` and add your key."
        )
    try:
        error = await setup_agent()
        if error:
            return error
        result = await st.session_state.llm.generate_str(
            message=message,
            request_params=RequestParams(use_history=True, maxTokens=8000),
        )
        return result
    except Exception as e:
        return f"Error: {str(e)}"


def start_run():
    st.session_state.is_processing = True


col1, col2 = st.columns([1, 4])
with col1:
    st.button(
        "🚀 Run",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.is_processing or not query.strip(),
        on_click=start_run,
    )
with col2:
    if st.session_state.is_processing:
        st.info("Agent is working…")

if st.session_state.is_processing:
    with st.spinner("Running Aegis DQ agent…"):
        result = st.session_state.loop.run_until_complete(run_agent(query))
    st.session_state.last_result = result
    st.session_state.is_processing = False
    st.rerun()

if st.session_state.last_result:
    st.markdown("### Results")
    st.markdown(st.session_state.last_result)
else:
    st.info(
        "👆 Enter a prompt above to get started. "
        f"The demo database is ready at `{DB_PATH}` with 10 orders rows including data quality issues."
    )

st.markdown("---")
st.markdown(
    "Built with [Aegis DQ](https://aegis-dq.dev) · "
    "[MCP-Agent](https://github.com/lastmile-ai/mcp-agent) · "
    "[Streamlit](https://streamlit.io)"
)
