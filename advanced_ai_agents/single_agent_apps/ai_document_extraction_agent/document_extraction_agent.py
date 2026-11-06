"""KYNEX-style Document Extraction Agent — Streamlit Demo

Agentic schema-guided extraction from PDFs. Given any document and a
JSON Schema, the agent parses, plans, extracts, and iterates until the
schema is filled — no templates, no per-document tuning.

Ranked on the ExtractBench leaderboard:
https://github.com/run-llama/ExtractBench

Usage:
    streamlit run document_extraction_agent.py
"""

from __future__ import annotations

import base64
import io
import json
import re
import textwrap
from typing import Any

import pymupdf
import streamlit as st
from jsonschema import Draft7Validator
from openai import OpenAI

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="KYNEX Document Extraction Agent",
    page_icon="📄",
    layout="wide",
)

# ── Session state defaults ─────────────────────────────────────────────────────

for key, default in {
    "messages": [],
    "extracted": None,
    "iteration": 0,
    "pages_text": [],
    "schema": None,
    "status": "idle",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("📄 KYNEX Document Extraction")
    st.caption(
        "Agentic schema-guided extraction — "
        "[ExtractBench leaderboard](https://github.com/run-llama/ExtractBench)"
    )

    api_key = st.text_input("OpenAI API Key", type="password")
    model = st.selectbox("Model", ["gpt-5.4", "gpt-4o", "gpt-4.1", "gpt-4.1-mini"], index=0)
    max_iterations = st.slider("Max iterations", 1, 5, 3)

    st.divider()
    uploaded_pdf = st.file_uploader("Upload a PDF", type=["pdf"])
    schema_input = st.text_area(
        "JSON Schema (paste or use sample)",
        height=200,
        placeholder='{"type": "object", "properties": {...}}',
    )

    use_sample = st.checkbox("Use sample invoice schema")
    if use_sample:
        schema_input = json.dumps(
            {
                "type": "object",
                "properties": {
                    "invoice_number": {"type": ["string", "null"]},
                    "invoice_date": {"type": ["string", "null"]},
                    "due_date": {"type": ["string", "null"]},
                    "vendor_name": {"type": ["string", "null"]},
                    "vendor_address": {"type": ["string", "null"]},
                    "bill_to_name": {"type": ["string", "null"]},
                    "bill_to_address": {"type": ["string", "null"]},
                    "subtotal": {"type": ["number", "null"]},
                    "tax": {"type": ["number", "null"]},
                    "total_amount": {"type": ["number", "null"]},
                    "currency": {"type": ["string", "null"]},
                    "payment_terms": {"type": ["string", "null"]},
                    "line_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": ["string", "null"]},
                                "quantity": {"type": ["number", "null"]},
                                "unit_price": {"type": ["number", "null"]},
                                "amount": {"type": ["number", "null"]},
                            },
                        },
                    },
                },
            },
            indent=2,
        )

    run_btn = st.button("Extract", type="primary", disabled=not (uploaded_pdf and api_key))


# ── Helpers ────────────────────────────────────────────────────────────────────


def parse_pdf(pdf_bytes: bytes) -> list[dict]:
    """Parse PDF into per-page text + metadata."""
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text") or ""
        pages.append(
            {
                "page": i + 1,
                "text": text.strip(),
                "chars": len(text),
            }
        )
    doc.close()
    return pages


def null_skeleton(schema: dict) -> dict:
    """Build a null-filled skeleton from a JSON Schema."""
    out: dict = {}
    props = schema.get("properties") or {}
    for key in sorted(props):
        sub = props[key] or {}
        st_type = sub.get("type", "")
        if isinstance(st_type, list):
            non_null = [x for x in st_type if x != "null"]
            st_type = non_null[0] if non_null else ""
        if st_type == "object":
            out[key] = null_skeleton(sub)
        elif st_type == "array":
            out[key] = []
        else:
            out[key] = None
    return out


def count_nulls(obj: Any) -> tuple[int, int]:
    """Return (null_count, total_leaves)."""
    if isinstance(obj, dict):
        n, t = 0, 0
        for v in obj.values():
            cn, ct = count_nulls(v)
            n += cn
            t += ct
        return n, t
    if isinstance(obj, list):
        if not obj:
            return 1, 1
        n, t = 0, 0
        for v in obj:
            cn, ct = count_nulls(v)
            n += cn
            t += ct
        return n, t
    if obj is None:
        return 1, 1
    return 0, 1


def schema_field_list(schema: dict, prefix: str = "") -> list[str]:
    """Flat list of dotted field paths from a schema."""
    fields = []
    for key, sub in (schema.get("properties") or {}).items():
        path = f"{prefix}{key}" if not prefix else f"{prefix}.{key}"
        st_type = sub.get("type", "")
        if isinstance(st_type, list):
            non_null = [x for x in st_type if x != "null"]
            st_type = non_null[0] if non_null else ""
        if st_type == "object":
            fields.extend(schema_field_list(sub, path))
        elif st_type == "array" and "items" in sub:
            fields.append(f"{path}[]")
            items = sub["items"]
            if isinstance(items, dict) and items.get("type") == "object":
                fields.extend(schema_field_list(items, f"{path}[]."))
        else:
            fields.append(path)
    return fields


# ── Agent logic ────────────────────────────────────────────────────────────────


def build_document_context(pages: list[dict], max_chars: int = 80_000) -> str:
    """Concatenate page texts up to a char budget."""
    parts = []
    total = 0
    for p in pages:
        if total + p["chars"] > max_chars:
            remaining = max_chars - total
            parts.append(f"\n--- Page {p['page']} (truncated) ---\n{p['text'][:remaining]}")
            break
        parts.append(f"\n--- Page {p['page']} ---\n{p['text']}")
        total += p["chars"]
    return "".join(parts)


def extraction_prompt(
    schema: dict,
    document_text: str,
    current_output: dict | None,
    iteration: int,
    fields: list[str],
) -> list[dict]:
    """Build the extraction prompt for the LLM."""
    field_list = "\n".join(f"  - {f}" for f in fields)
    system = textwrap.dedent(f"""\
        You are a document extraction agent. Your task is to extract structured
        data from a document according to a JSON Schema.

        RULES:
        1. Return ONLY valid JSON matching the schema — no markdown, no explanation.
        2. For fields not found in the document, use null.
        3. For arrays, include ALL items found — do not truncate.
        4. Preserve exact values: numbers, dates, IDs — copy verbatim from the document.
        5. If a value is ambiguous, prefer the most specific match.

        SCHEMA FIELDS:
        {field_list}
    """)

    user_parts = [f"## Document ({len(document_text)} chars)\n{document_text}"]
    user_parts.append(f"\n## JSON Schema\n```json\n{json.dumps(schema, indent=2)}\n```")

    if current_output and iteration > 1:
        nulls, total = count_nulls(current_output)
        user_parts.append(
            f"\n## Previous extraction (iteration {iteration - 1}, {nulls}/{total} nulls)\n"
            f"```json\n{json.dumps(current_output, indent=2)}\n```\n\n"
            f"Review the document again. Fill in any null fields you can find. "
            f"For arrays, check if there are more items you missed. "
            f"Return the COMPLETE updated JSON."
        )
    else:
        user_parts.append(
            "\n\nExtract all data matching the schema from this document. "
            "Return ONLY the JSON object."
        )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n".join(user_parts)},
    ]


def call_llm(client: OpenAI, model: str, messages: list[dict]) -> str:
    """Call the LLM and return raw text."""
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.0,
        max_tokens=16_384,
    )
    return resp.choices[0].message.content or ""


def parse_json_response(text: str) -> dict | None:
    """Extract JSON from LLM response, stripping markdown fences."""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m2 = re.search(r"\{.*\}", text, re.DOTALL)
        if m2:
            try:
                return json.loads(m2.group())
            except json.JSONDecodeError:
                return None
    return None


def run_extraction(
    client: OpenAI,
    model: str,
    pages: list[dict],
    schema: dict,
    max_iters: int,
    status_container,
    log_container,
) -> dict:
    """Run the iterative extraction agent loop."""
    doc_text = build_document_context(pages)
    fields = schema_field_list(schema)
    current = null_skeleton(schema)

    for i in range(1, max_iters + 1):
        nulls_before, total = count_nulls(current)
        status_container.info(
            f"Iteration {i}/{max_iters} — {nulls_before}/{total} fields still null"
        )

        messages = extraction_prompt(schema, doc_text, current, i, fields)
        log_container.markdown(f"**Iteration {i}:** Sending {len(doc_text):,} chars to `{model}`...")

        raw = call_llm(client, model, messages)
        parsed = parse_json_response(raw)

        if parsed is None:
            log_container.warning(f"Iteration {i}: Failed to parse JSON response")
            continue

        current = parsed
        nulls_after, total = count_nulls(current)
        filled = nulls_before - nulls_after
        log_container.success(
            f"Iteration {i}: Filled {filled} fields "
            f"({nulls_after}/{total} still null)"
        )

        if nulls_after == 0:
            log_container.success("All fields filled — stopping early.")
            break

        if i > 1 and filled == 0:
            log_container.info("No improvement — stopping.")
            break

    return current


# ── Main UI ────────────────────────────────────────────────────────────────────

st.title("📄 KYNEX Document Extraction Agent")
st.markdown(
    "Upload any PDF + provide a JSON Schema. The agent iteratively extracts "
    "structured data, filling every field and every array record it can find."
)

if run_btn and uploaded_pdf and api_key:
    try:
        schema = json.loads(schema_input)
    except json.JSONDecodeError:
        st.error("Invalid JSON Schema — please fix and retry.")
        st.stop()

    pdf_bytes = uploaded_pdf.read()
    pages = parse_pdf(pdf_bytes)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Document")
        st.caption(f"{len(pages)} pages, {sum(p['chars'] for p in pages):,} chars")
        with st.expander("Page text", expanded=False):
            for p in pages[:20]:
                st.markdown(f"**Page {p['page']}** ({p['chars']} chars)")
                st.text(p["text"][:2000])

    with col2:
        st.subheader("Extraction")
        status = st.empty()
        log = st.container()

        client = OpenAI(api_key=api_key)
        result = run_extraction(
            client, model, pages, schema, max_iterations, status, log
        )

        nulls, total = count_nulls(result)
        pct = ((total - nulls) / total * 100) if total else 0
        status.success(f"Done — {total - nulls}/{total} fields filled ({pct:.0f}%)")

        st.subheader("Result")
        st.json(result)

        st.download_button(
            "Download JSON",
            data=json.dumps(result, indent=2, ensure_ascii=False),
            file_name="extraction_result.json",
            mime="application/json",
        )

elif not run_btn:
    st.info("Upload a PDF, paste a JSON Schema (or use the sample), and click **Extract**.")
