# ⚓ AnchorDoc Document Verification MCP Agent

A Streamlit AI agent that reads, cross-references, and deterministically verifies facts across long PDFs (such as 100+ page SEC 10-K filings, contracts, and technical specifications) over the **Model Context Protocol (MCP)** — **without embeddings, chunking pipelines, or a vector database**.

Powered by the open-source **[AnchorDoc MCP Server](https://github.com/ryanvii/AnchorDoc)** (`Apache-2.0`).

## Why Progressive MCP Navigation Instead of Flat Vector RAG?

Flat vector chunking often splits tables across chunks, misses footnote cross-references (`"See Note 7"`), and cannot detect subtle sign/period/unit errors. Instead, this agent connects to AnchorDoc's **4 zero-LLM, read-only MCP tools** over `stdio`:

1. **`doc_outline`** *(L0 Map)* — Inspects document structure, headings/subheadings, printed page ranges, and routing hints under a strict token cap.
2. **`doc_locate`** *(L1 Locator)* — Zero-LLM BM25 + structural heading + printed page-reference search to pinpoint exact pages.
3. **`doc_read`** *(L2 Anchored Reader)* — Reads targeted pages with stable line anchors (`p12:L07`) and follows cross-page continuation tables or footnotes.
4. **`doc_verify`** *(Deterministic Verifier)* — Checks verbatim quote grounding and recomputes numerical formulas via Python AST (`safe_calc`) so the LLM never guesses arithmetic.

## Features

- **Zero Vector DB / Zero Indexing LLM Calls**: Indexes 250-page PDFs locally in ~0.3s using Apache-2.0 `pypdfium2`.
- **Upload & Verify Any PDF/DOCX**: Files are scoped strictly to a session-isolated temporary `--root` directory.
- **Auditable Citations & Math**: Every answer includes page-level references and deterministic formula checks.
- **Built-in Query Presets**: Financial metric & margin checks, cross-page footnote audits, and clause/risk verification.

## Setup

### Requirements

- Python 3.10+
- OpenAI API Key (for the host Agno agent; the AnchorDoc MCP server itself makes zero LLM calls)

### Installation

1. Clone this repository and navigate to the app directory:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/mcp_ai_agents/anchordoc_mcp_agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the Streamlit app:
   ```bash
   streamlit run anchordoc_agent.py
   ```

4. In the sidebar, enter your **OpenAI API Key**, upload any PDF/DOCX file (e.g., an annual report or contract), pick a preset or write a custom question, and click **Run Verified Query**.
