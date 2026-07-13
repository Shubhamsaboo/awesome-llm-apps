"""
Eval-First RAG — a RAG app that scores its own answers.

Most RAG demos stop at "retrieve + generate". This one adds the layer that
matters in production: after every answer it runs an evaluation pass that scores
retrieval confidence and answer groundedness, then flags the dangerous failure
mode standard RAG misses — a confident answer that the retrieved context does
NOT support (a "confident hallucination").

Built by Ruthwik Arepelly (https://github.com/Ruthwik-Data) — eval-first AI PM.
"""

import json
import os

import numpy as np
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # optional: read OPENAI_API_KEY from a local .env

EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

# A small built-in corpus of REAL, public financial facts so the app runs with
# zero setup. Figures are Apple's reported FY2024 results (fiscal year ended
# Sept 28, 2024) — stated as facts, not reproduced document prose.
SAMPLE_DOC = """Apple Inc. - FY2024 financial summary (fiscal year ended September 28, 2024).
Reported figures from Apple's public annual results.

Total revenue (net sales) for FY2024 was $391.0 billion, up about 2% from $383.3 billion in FY2023.
Services revenue reached a record $96.2 billion.
Total company gross margin was 46.2%.
Net income for FY2024 was $93.7 billion.
Research and development expense was $31.4 billion.
Apple returned cash to shareholders through share buybacks and dividends, and paid a quarterly cash dividend of $0.25 per share.
"""


def chunk_text(text, size=60, overlap=15):
    """Word-based chunking with overlap so sentence context is preserved."""
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunks.append(" ".join(words[i : i + size]))
        i += size - overlap
    return [c for c in chunks if c.strip()]


def embed(client, texts):
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return np.array([d.embedding for d in resp.data], dtype=np.float32)


def top_k(query_vec, doc_vecs, k=3):
    q = query_vec / (np.linalg.norm(query_vec) + 1e-9)
    d = doc_vecs / (np.linalg.norm(doc_vecs, axis=1, keepdims=True) + 1e-9)
    sims = d @ q
    idx = np.argsort(sims)[::-1][:k]
    return idx, sims[idx]


def generate_answer(client, question, context, strict=True):
    if strict:
        instruction = (
            "Answer the question using ONLY the context below. "
            "If the answer is not in the context, reply exactly: 'Not found in context.'"
        )
    else:
        # "Loose" mode: the model may answer from general knowledge — this is how
        # confident hallucinations happen, and how this app catches them.
        instruction = (
            "Answer the question. Use the context if relevant; otherwise answer "
            "from your general knowledge. Always give a concrete answer."
        )
    prompt = f"{instruction}\n\nContext:\n{context}\n\nQuestion: {question}"
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return resp.choices[0].message.content.strip()


def evaluate(client, question, answer, context):
    """LLM-as-judge groundedness check. Returns {score, verdict, reason}."""
    rubric = (
        "You are a strict RAG evaluator. Given a QUESTION, an ANSWER, and the "
        "CONTEXT the answer was supposed to be grounded in, decide how well the "
        "answer is SUPPORTED BY THE CONTEXT. Do not reward fluent wording. "
        "Return JSON: {\"groundedness\": 0.0-1.0, \"verdict\": one of "
        "['grounded','honest_refusal','confident_hallucination'], \"reason\": short}. "
        "Rules: if the answer says it cannot find the info, verdict='honest_refusal' "
        "and groundedness=1.0 (refusing when unsupported is correct). If the answer "
        "makes a specific claim not supported by the context, verdict="
        "'confident_hallucination' and groundedness<=0.3."
    )
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": rubric},
            {
                "role": "user",
                "content": f"QUESTION:\n{question}\n\nANSWER:\n{answer}\n\nCONTEXT:\n{context}",
            },
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    try:
        return json.loads(resp.choices[0].message.content)
    except (json.JSONDecodeError, TypeError):
        return {"groundedness": None, "verdict": "unknown", "reason": "eval parse failed"}


# ------------------------------- UI -------------------------------
st.set_page_config(page_title="Eval-First RAG", page_icon="🧪")
st.title("🧪 Eval-First RAG")
st.caption(
    "A RAG app that scores its own answers — flags confident hallucinations, "
    "not just retrieves and generates."
)

with st.sidebar:
    st.header("Setup")
    api_key = st.text_input(
        "OpenAI API key", type="password", value=os.getenv("OPENAI_API_KEY", "")
    )
    mode = st.radio(
        "Grounding mode",
        ["Strict (context only)", "Loose (answer freely)"],
        help="Loose lets the model answer from general knowledge — the fastest way "
        "to see a confident hallucination get caught.",
    )
    strict = mode.startswith("Strict")
    audit_answer = st.text_area(
        "Audit an answer (optional)",
        help="Paste ANY answer to score it against the retrieved context — a "
        "deterministic way to watch the evaluator catch a wrong answer. "
        "Leave empty to evaluate the model's own answer.",
        placeholder="e.g. Apple reported FY2024 revenue of $450.0 billion.",
    )
    st.markdown("**Corpus** (edit to test your own):")
    doc = st.text_area("Document", SAMPLE_DOC, height=240)
    st.markdown(
        "**Strict mode:** *What was Apple's FY2024 revenue?* → grounded · "
        "*How much did Apple spend on marketing?* → honest refusal.\n\n"
        "**Loose mode:** *What was Tesla's FY2024 revenue?* → the model answers "
        "from memory, ungrounded in this doc → ⚠️ confident hallucination."
    )

question = st.text_input("Ask a question about the document")

if st.button("Run") and question:
    if not api_key:
        st.error("Add your OpenAI API key in the sidebar.")
        st.stop()

    client = OpenAI(api_key=api_key)
    with st.spinner("Retrieving, answering, and evaluating..."):
        chunks = chunk_text(doc)
        doc_vecs = embed(client, chunks)
        q_vec = embed(client, [question])[0]
        idx, sims = top_k(q_vec, doc_vecs, k=3)
        retrieved = [chunks[i] for i in idx]
        context = "\n\n".join(retrieved)
        if audit_answer.strip():
            answer = audit_answer.strip()
        else:
            answer = generate_answer(client, question, context, strict=strict)
        report = evaluate(client, question, answer, context)

    st.subheader("Answer")
    st.write(answer)

    st.subheader("🔬 Evaluation")
    verdict = report.get("verdict", "unknown")
    grounded = report.get("groundedness")
    top_sim = float(sims[0]) if len(sims) else 0.0

    c1, c2 = st.columns(2)
    c1.metric("Retrieval confidence", f"{top_sim:.2f}")
    c2.metric("Groundedness", "—" if grounded is None else f"{grounded:.2f}")

    labels = {
        "grounded": ("✅ Grounded", "Answer is supported by the retrieved context."),
        "honest_refusal": ("✅ Honest refusal", "Correctly declined — info isn't in the context."),
        "confident_hallucination": (
            "⚠️ Confident hallucination",
            "Answer makes a claim the context does NOT support. This is the dangerous case.",
        ),
        "unknown": ("❓ Unknown", "Evaluator could not parse a verdict."),
    }
    title, desc = labels.get(verdict, labels["unknown"])
    (st.error if verdict == "confident_hallucination" else st.success)(f"**{title}** — {desc}")
    if report.get("reason"):
        st.caption(f"Judge: {report['reason']}")

    with st.expander("Retrieved context (top 3 chunks + similarity)"):
        for i, sim in zip(idx, sims):
            st.markdown(f"**sim {sim:.2f}** — {chunks[i]}")
