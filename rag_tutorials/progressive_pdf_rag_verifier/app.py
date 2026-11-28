"""Streamlit UI for Progressive PDF RAG & Deterministic Claim Verification.

Tab 1: LLM Agent Mode (OpenAI / OpenAI-compatible endpoint) with progressive
       tool-call trace and automatic deterministic verification.
Tab 2: Zero-API-Key Mode for structural outline exploration, BM25 search,
       bounded page reading, and live quote/number/formula verification.
"""

from __future__ import annotations

import json
import os

import streamlit as st
from openai import OpenAI

from agent import ProgressivePDFAgent
from claim_verifier import verify_formula, verify_number, verify_quote
from pdf_navigator import PDFDocumentIndex, build_sample_financial_pdf

st.set_page_config(
    page_title="Progressive PDF RAG & Verifier",
    page_icon="📑",
    layout="wide",
)

st.title("📑 Progressive PDF RAG & Deterministic Verifier")
st.caption(
    "No vector DB · Zero-LLM structural indexing · Token-bounded progressive reading · "
    "Deterministic quote, number & AST formula verification"
)


@st.cache_data(show_spinner=False)
def _load_index(pdf_bytes: bytes, filename: str) -> PDFDocumentIndex:
    return PDFDocumentIndex.from_bytes(pdf_bytes, name=filename)


with st.sidebar:
    st.header("1. Document Source")
    uploaded = st.file_uploader("Upload a PDF", type=["pdf"])
    use_sample = st.button("Load Sample PDF (Acme FY2025)", use_container_width=True)

    if use_sample:
        st.session_state["sample_active"] = True
    if uploaded is not None:
        st.session_state["sample_active"] = False

    st.divider()
    st.header("2. LLM Settings (Optional)")
    st.caption("Only needed for Tab 1 (Ask & Verify Agent). Tab 2 works with zero API key.")
    api_key = st.text_input(
        "API Key",
        type="password",
        value=os.getenv("OPENAI_API_KEY", ""),
        placeholder="sk-...",
    )
    base_url = st.text_input(
        "Base URL (optional)",
        value=os.getenv("OPENAI_BASE_URL", ""),
        placeholder="https://api.openai.com/v1",
    )
    model = st.text_input("Model", value=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    max_steps = st.slider("Max tool-call steps", min_value=2, max_value=12, value=8)

# Resolve active PDF
index: PDFDocumentIndex | None = None
if uploaded is not None:
    index = _load_index(uploaded.getvalue(), uploaded.name)
elif st.session_state.get("sample_active", True):
    index = _load_index(build_sample_financial_pdf(), "acme_fy2025_report.pdf")

assert index is not None
col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("Active PDF", index.name)
col_m2.metric("Pages Indexed", index.num_pages)
col_m3.metric("Outline Sections", len(index.outline))

tab_agent, tab_offline = st.tabs(
    ["🤖 Ask & Verify (LLM Agent)", "🔬 Zero-API-Key Explorer & Verifier"]
)

with tab_agent:
    st.subheader("Progressive Navigation + Deterministic Verification Agent")
    default_q = (
        "What was Acme Robotics' FY2025 gross margin, and what is the maximum Net Debt/EBITDA "
        "covenant? Verify all numbers and calculations against the source PDF."
    )
    question = st.text_area("Ask a question about the PDF", value=default_q, height=90)
    run_btn = st.button("Run Agent", type="primary")

    if run_btn:
        if not api_key.strip():
            st.warning(
                "Enter an OpenAI-compatible API key in the sidebar to run the LLM agent, "
                "or switch to Tab 2 to test progressive navigation and verification with zero API key."
            )
        elif not question.strip():
            st.warning("Please enter a question.")
        else:
            client = OpenAI(api_key=api_key.strip(), base_url=base_url.strip() or None)
            agent = ProgressivePDFAgent(
                index=index,
                client=client,
                model=model.strip() or "gpt-4o-mini",
                max_steps=max_steps,
            )
            with st.spinner("Navigating outline, reading targeted pages, and verifying claims..."):
                res = agent.ask(question.strip())

            st.markdown("### Answer")
            st.markdown(res.answer)

            c1, c2, c3 = st.columns(3)
            c1.metric("Pages Read", f"{len(res.pages_read)} / {index.num_pages}")
            c2.metric("Agent Steps", res.steps_used)
            verified_ok = sum(1 for v in res.verifications if v.get("status") == "verified")
            c3.metric("Deterministic Checks", f"{verified_ok} / {len(res.verifications)} verified")

            if res.verifications:
                st.markdown("### Deterministic Verification Checks")
                for v in res.verifications:
                    status = v.get("status", "unverified")
                    label = f"[{status.upper()}] ({v.get('kind')}) {v.get('detail')}"
                    if status == "verified":
                        st.success(label)
                    else:
                        st.error(label)

            with st.expander(f"Progressive Tool-Call Trace ({len(res.trace)} calls)"):
                for step in res.trace:
                    st.markdown(f"**Step {step.step} — `{step.tool}`**")
                    st.code(json.dumps(step.arguments, indent=2, ensure_ascii=False), language="json")
                    st.json(step.result)

with tab_offline:
    left, right = st.columns([1, 1])

    with left:
        st.subheader("1. Structural Outline & BM25 Search")
        outline_data = index.get_outline()
        for sec in outline_data["sections"]:
            indent = "　" * max(0, sec["level"] - 1)
            st.markdown(
                f"{indent}**{sec['section_id']}** {sec['title']} "
                f"`p.{sec['start_page']}–{sec['end_page']}`"
            )

        st.divider()
        search_q = st.text_input("BM25 Search Query", value="Net Debt EBITDA covenant")
        if search_q.strip():
            search_res = index.search_pages(search_q.strip(), top_k=4)
            if not search_res["hits"]:
                st.info("No lexical hits found for this query.")
            for hit in search_res["hits"]:
                st.markdown(f"**Page {hit['page']}** (`score={hit['score']}`) · *{hit['section']}*")
                st.caption(hit["snippet"])

        st.divider()
        page_to_read = st.number_input(
            "Inspect Exact Page (1-based)",
            min_value=1,
            max_value=max(1, index.num_pages),
            value=min(3, index.num_pages),
            step=1,
        )
        page_payload = index.read_pages([int(page_to_read)])
        if page_payload["content"]:
            st.text_area(
                f"Page {page_to_read} Text",
                value=page_payload["content"][0]["text"],
                height=220,
            )

    with right:
        st.subheader("2. Deterministic Claim Verifier (Zero API Key)")
        mode = st.radio("Verification Type", ["Quote", "Number", "Formula"], horizontal=True)

        if mode == "Quote":
            q_page = st.number_input("Cited Page", min_value=1, max_value=index.num_pages, value=1)
            q_text = st.text_area(
                "Claimed Verbatim Quote",
                value="All factory deployments met our 99.4% uptime SLA while reducing unit assembly cost by 14.5% year-over-year.",
                height=90,
            )
            if st.button("Verify Quote"):
                vr = verify_quote(index, q_text, int(q_page))
                (st.success if vr.status == "verified" else st.error)(vr.detail)
                st.json(vr.to_dict())

        elif mode == "Number":
            n_page = st.number_input("Cited Page", min_value=1, max_value=index.num_pages, value=3)
            n_val = st.number_input("Claimed Numeric Value", value=480.0, format="%.4f")
            if st.button("Verify Number"):
                vr = verify_number(index, float(n_val), int(n_page))
                (st.success if vr.status == "verified" else st.error)(vr.detail)
                st.json(vr.to_dict())

        else:
            p1, p2 = st.columns(2)
            if p1.button("Preset: Valid Gross Margin (40%)"):
                st.session_state["f_expr"] = "(revenue - cogs) / revenue * 100"
                st.session_state["f_ops"] = json.dumps(
                    {"revenue": {"value": 480.0, "page": 3}, "cogs": {"value": 288.0, "page": 3}},
                    indent=2,
                )
                st.session_state["f_res"] = 40.0
            if p2.button("Preset: Hallucinated Margin Trap (45%)"):
                st.session_state["f_expr"] = "(revenue - cogs) / revenue * 100"
                st.session_state["f_ops"] = json.dumps(
                    {"revenue": {"value": 480.0, "page": 3}, "cogs": {"value": 288.0, "page": 3}},
                    indent=2,
                )
                st.session_state["f_res"] = 45.0

            f_expr = st.text_input(
                "Symbolic Formula",
                value=st.session_state.get("f_expr", "(revenue - cogs) / revenue * 100"),
            )
            f_ops = st.text_area(
                "Page-Cited Operands (JSON)",
                value=st.session_state.get(
                    "f_ops",
                    json.dumps(
                        {"revenue": {"value": 480.0, "page": 3}, "cogs": {"value": 288.0, "page": 3}},
                        indent=2,
                    ),
                ),
                height=130,
            )
            f_claimed = st.number_input(
                "Claimed Result",
                value=float(st.session_state.get("f_res", 40.0)),
                format="%.4f",
            )
            if st.button("Verify Formula"):
                try:
                    ops_dict = json.loads(f_ops)
                except json.JSONDecodeError as exc:
                    st.error(f"Invalid operands JSON: {exc}")
                else:
                    vr = verify_formula(index, f_expr, ops_dict, float(f_claimed))
                    (st.success if vr.status == "verified" else st.error)(vr.detail)
                    st.json(vr.to_dict())
