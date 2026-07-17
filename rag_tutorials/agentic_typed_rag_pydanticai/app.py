"""Streamlit interface for typed, cited, self-refusing RAG."""

from __future__ import annotations

import asyncio
import os
from pathlib import PurePath

import streamlit as st
from dotenv import load_dotenv

from agent import Answer, RagDependencies, answer_question, model_for_provider
from rag import (
    HashingEmbeddingBackend,
    InMemoryVectorStore,
    OpenAIEmbeddingBackend,
    default_embedding_backend,
    fetch_url_text,
    ingest_pdf,
)


load_dotenv()

st.set_page_config(
    page_title="Typed Agentic RAG",
    page_icon="📎",
    layout="wide",
)


def run_async(awaitable):
    """Run one async operation from Streamlit's synchronous script."""
    return asyncio.run(awaitable)


def selected_embedding_backend(mode: str):
    if mode == "OpenAI":
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OpenAI embeddings require OPENAI_API_KEY")
        return OpenAIEmbeddingBackend()
    if mode == "Local hashing":
        return HashingEmbeddingBackend()
    return default_embedding_backend()


async def build_knowledge_base(files, docs_url: str, embedding_mode: str):
    """Build a fresh vector store from the current source selection."""
    store = InMemoryVectorStore(selected_embedding_backend(embedding_mode))
    indexed = []

    for uploaded_file in files:
        source = PurePath(uploaded_file.name).name
        chunk_count = await ingest_pdf(store, source, uploaded_file.getvalue())
        indexed.append((source, chunk_count))

    if docs_url:
        text = fetch_url_text(docs_url)
        chunk_count = await store.add_document(docs_url, text)
        indexed.append((docs_url, chunk_count))

    return store, indexed


def render_answer(answer: Answer) -> None:
    """Render either a grounded answer card or a clear refusal state."""
    if answer.answered:
        st.markdown(answer.text)
        st.progress(answer.confidence)
        st.caption(f"Answer confidence: {answer.confidence:.0%}")
        st.markdown("**Citations**")
        for citation in answer.citations:
            label = f"{citation.source} | {citation.chunk_id}"
            with st.expander(label):
                st.code(citation.quoted_span, language=None)
    else:
        st.warning(answer.text, icon="🛑")
        st.progress(answer.confidence)
        st.caption(f"Best retrieval similarity: {answer.confidence:.0%}")


if "rag_store" not in st.session_state:
    st.session_state.rag_store = None
if "indexed_sources" not in st.session_state:
    st.session_state.indexed_sources = []
if "answer_history" not in st.session_state:
    st.session_state.answer_history = []


with st.sidebar:
    st.header("Model settings")
    configured_model = os.getenv("RAG_MODEL", "").strip()
    prefer_anthropic = (
        configured_model.startswith("anthropic:")
        if configured_model
        else bool(os.getenv("ANTHROPIC_API_KEY")) and not os.getenv("OPENAI_API_KEY")
    )
    provider = st.selectbox(
        "Answer provider",
        ["OpenAI", "Anthropic"],
        index=1 if prefer_anthropic else 0,
    )
    key_name = "OPENAI_API_KEY" if provider == "OpenAI" else "ANTHROPIC_API_KEY"
    if os.getenv(key_name):
        st.success(f"{key_name} loaded", icon="🔑")
    else:
        st.warning(f"Set {key_name} in .env before asking a question.")

    configured_matches_provider = configured_model.startswith(provider.casefold())
    model_name = st.text_input(
        "Pydantic AI model",
        value=(
            configured_model
            if configured_matches_provider
            else model_for_provider(provider)
        ),
        key=f"model-name-{provider.casefold()}",
        help="Use the provider:model format accepted by Pydantic AI.",
    )
    embedding_mode = st.selectbox(
        "Embeddings",
        ["Auto", "OpenAI", "Local hashing"],
        help="Auto uses OpenAI when its key is set, otherwise a local lexical fallback.",
    )
    min_relevance = st.slider(
        "Refusal threshold",
        min_value=0.05,
        max_value=0.60,
        value=0.20,
        step=0.01,
        help="Questions below this retrieval score are refused before an LLM call.",
    )

    st.divider()
    if st.session_state.rag_store is not None:
        store = st.session_state.rag_store
        st.metric("Indexed chunks", store.count)
        st.caption(f"Embeddings: {store.embedding_backend.name}")
        if st.button("Clear knowledge base", use_container_width=True):
            st.session_state.rag_store = None
            st.session_state.indexed_sources = []
            st.session_state.answer_history = []
            st.rerun()


st.title("📎 Typed Agentic RAG")
st.write(
    "Upload evidence, ask a question, and get a validated answer with exact quotes. "
    "Weak retrieval produces a refusal instead of a guess."
)

source_column, status_column = st.columns([3, 2])
with source_column:
    st.subheader("1. Add sources")
    uploaded_files = st.file_uploader(
        "PDF documents",
        type=["pdf"],
        accept_multiple_files=True,
    )
    docs_url = st.text_input(
        "Documentation URL",
        placeholder="https://example.com/docs",
        help="Optional. HTML and plain-text pages up to 2 MB are supported.",
    ).strip()
    build_clicked = st.button(
        "Build knowledge base",
        type="primary",
        disabled=not uploaded_files and not docs_url,
    )

with status_column:
    st.subheader("Index status")
    if st.session_state.indexed_sources:
        for source, chunks in st.session_state.indexed_sources:
            st.success(f"{source}: {chunks} chunks", icon="✅")
    else:
        st.info("Add at least one PDF or docs URL to begin.")

if build_clicked:
    with st.spinner("Extracting, chunking, and embedding sources..."):
        try:
            store, indexed_sources = run_async(
                build_knowledge_base(uploaded_files or [], docs_url, embedding_mode)
            )
        except Exception as exc:
            st.error(f"Could not build the knowledge base: {exc}")
        else:
            st.session_state.rag_store = store
            st.session_state.indexed_sources = indexed_sources
            st.session_state.answer_history = []
            st.rerun()

st.divider()
st.subheader("2. Ask the indexed sources")

for item in st.session_state.answer_history:
    with st.chat_message("user"):
        st.markdown(item["question"])
    with st.chat_message("assistant"):
        render_answer(Answer.model_validate(item["answer"]))

question = st.chat_input(
    "Ask a question about the indexed sources",
    disabled=st.session_state.rag_store is None,
)
if question:
    if not os.getenv(key_name):
        st.error(f"Set {key_name} before asking a question.")
    else:
        deps = RagDependencies(
            store=st.session_state.rag_store,
            min_relevance=min_relevance,
            top_k=4,
        )
        with st.spinner("Retrieving evidence and validating the answer..."):
            try:
                selected_model = model_name.strip() or model_for_provider(provider)
                answer = run_async(
                    answer_question(question, deps, model=selected_model)
                )
            except Exception as exc:
                st.error(f"The agent could not answer: {exc}")
            else:
                st.session_state.answer_history.append(
                    {"question": question, "answer": answer.model_dump()}
                )
                st.rerun()
