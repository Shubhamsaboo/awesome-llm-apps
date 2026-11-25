import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from textwrap import dedent

import streamlit as st
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.run.agent import RunOutput
from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters

st.set_page_config(
    page_title="⚓ AnchorDoc Verification MCP Agent",
    page_icon="⚓",
    layout="wide",
)

st.title("⚓ AnchorDoc Document Verification MCP Agent")
st.markdown(
    "Navigate long PDFs on demand, trace cross-page footnotes, and verify verbatim quotes "
    "and numerical calculations over **MCP** — with **no vector database** and **no embeddings**."
)

if "docs_dir" not in st.session_state:
    st.session_state.docs_dir = tempfile.mkdtemp(prefix="anchordoc_mcp_")

docs_dir = Path(st.session_state.docs_dir)

with st.sidebar:
    st.header("🔑 Configuration")
    openai_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Used by the host AI agent to orchestrate MCP tool calls",
    )
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key

    model_id = st.text_input(
        "Model ID",
        value="gpt-4o-mini",
        help="Any OpenAI-compatible chat model supporting tool calling",
    )

    st.markdown("---")
    st.header("📄 Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload PDF or DOCX files",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        help="Files are stored locally in a temporary folder mounted to the read-only AnchorDoc MCP server",
    )
    if uploaded_files:
        for uf in uploaded_files:
            target = docs_dir / Path(uf.name).name
            target.write_bytes(uf.getbuffer())

    saved_files = sorted(p.name for p in docs_dir.iterdir() if p.is_file())
    if saved_files:
        st.success(f"Loaded {len(saved_files)} document(s):")
        for name in saved_files:
            st.caption(f"• {name}")
    else:
        st.info("Upload at least one PDF or DOCX to begin.")

    st.markdown("---")
    st.markdown("### How It Works (4 Zero-LLM MCP Tools)")
    st.markdown(
        "1. `doc_outline` — Read the L0 structural map & page ranges\n"
        "2. `doc_locate` — Zero-LLM BM25 + heading/page-ref locator\n"
        "3. `doc_read` — Token-bounded page read with `p12:L07` anchors\n"
        "4. `doc_verify` — Deterministic quote check & Python AST math"
    )

col1, col2 = st.columns([2, 1])
with col1:
    selected_doc = st.selectbox(
        "Target Document",
        options=saved_files if saved_files else ["(upload a PDF in the sidebar)"],
    )
with col2:
    preset = st.selectbox(
        "Query Preset",
        [
            "Financial Metric & Margin Check",
            "Cross-Page Footnote Audit",
            "Clause / Risk Verification",
            "Custom",
        ],
    )

if preset == "Financial Metric & Margin Check":
    default_query = (
        f"In {selected_doc}, extract total revenue and gross profit for the latest two fiscal years, "
        "verify the exact verbatim source lines, and compute the gross margin change in percentage points."
    )
elif preset == "Cross-Page Footnote Audit":
    default_query = (
        f"In {selected_doc}, check whether any key income statement line item references a footnote "
        "(e.g., restructuring, tax, or debt note). Follow the cross-reference to the target page and summarize the impact with page citations."
    )
elif preset == "Clause / Risk Verification":
    default_query = (
        f"In {selected_doc}, locate termination, liability, or material risk clauses, quote the exact "
        "relevant passages with page numbers, and verify every quote before answering."
    )
else:
    default_query = ""

query = st.text_area(
    "Your Question",
    value=default_query,
    height=110,
    placeholder="Ask a multi-page question that requires exact citations or calculations...",
)


async def run_anchordoc_agent(message: str, root_dir: str, model_name: str) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        return "Error: OpenAI API key not provided."

    anchordoc_bin = shutil.which("anchordoc")
    if not anchordoc_bin:
        return (
            "Error: `anchordoc` CLI not found on PATH. "
            "Install dependencies with `pip install -r requirements.txt`."
        )

    server_params = StdioServerParameters(
        command=anchordoc_bin,
        args=["mcp", "--root", root_dir],
        env={**os.environ},
    )

    try:
        async with MCPTools(server_params=server_params) as mcp_tools:
            agent = Agent(
                model=OpenAIChat(id=model_name),
                tools=[mcp_tools],
                instructions=dedent(
                    """\
                    You are a rigorous document verification analyst backed by the AnchorDoc MCP server.
                    Always follow the progressive reading protocol:
                    1. Start with `doc_outline` to understand document structure and page count.
                    2. Use `doc_locate` to find candidate pages instead of guessing page numbers.
                    3. Call `doc_read` on the highest-signal pages and follow any cross-references
                       (such as "See Note 7" or continuation tables) before drawing conclusions.
                    4. Call `doc_verify` to deterministically verify verbatim quotes and recompute
                       any numerical formulas in Python AST — never rely on mental arithmetic.
                    5. Cite exact page numbers (e.g., `[p12]`) and clearly distinguish verified facts
                       from missing or insufficient evidence.
                    """
                ),
                markdown=True,
            )
            response: RunOutput = await asyncio.wait_for(agent.arun(message), timeout=180.0)
            return response.content or "No response returned by agent."
    except asyncio.TimeoutError:
        return "Error: Request timed out after 180 seconds."
    except Exception as exc:
        return f"Error: {exc}"


if st.button("🚀 Run Verified Query", type="primary", use_container_width=True):
    if not openai_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
    elif not saved_files:
        st.error("Please upload at least one PDF or DOCX file in the sidebar.")
    elif not query.strip():
        st.error("Please enter a question.")
    else:
        with st.spinner("Navigating document anchors and verifying evidence over MCP..."):
            result = asyncio.run(run_anchordoc_agent(query, str(docs_dir), model_id))
        st.markdown("### Verified Analysis")
        st.markdown(result)
