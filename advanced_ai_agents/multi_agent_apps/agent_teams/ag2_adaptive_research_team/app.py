import os
import streamlit as st

from agents import DEFAULT_MODEL
from router import run_pipeline
from tools import build_local_index, load_documents

SEARXNG_BASE_URL = "https://searxng.site/search"


st.set_page_config(page_title="AG2 Adaptive Research Team", layout="wide")

st.title("AG2 Adaptive Research Team")
st.caption("Agent teamwork + agent-enabled routing, built with AG2")

with st.sidebar:
    st.header("API Configuration")
    api_key = st.text_input("OpenAI API Key", type="password")
    model = st.text_input("Model", value=DEFAULT_MODEL)
    web_enabled = st.toggle("Enable Web Fallback", value=True)
    st.markdown(
        "Web fallback uses a public SearxNG instance, which may be rate-limited."
    )

st.subheader("1. Upload Local Documents")
files = st.file_uploader(
    "Upload PDFs or text files",
    type=["pdf", "txt", "md"],
    accept_multiple_files=True,
)

st.subheader("2. Ask a Question")
question = st.text_area("Research question")

run_clicked = st.button("Run Research")

if run_clicked:
    if not api_key:
        st.error("Please provide your OpenAI API key.")
        st.stop()

    if not question.strip():
        st.error("Please enter a research question.")
        st.stop()

    os.environ["OPENAI_API_KEY"] = api_key

    documents = load_documents(files or [])
    local_index = build_local_index(documents)

    with st.spinner("Running the AG2 team..."):
        result = run_pipeline(
            question=question,
            local_chunks=local_index,
            api_key=api_key,
            model=model,
            web_enabled=web_enabled,
            searxng_base_url=SEARXNG_BASE_URL,
        )

    st.subheader("Routing Decision")
    st.json(result.get("triage", {}))

    st.subheader("Evidence")
    st.json(result.get("evidence", []))

    st.subheader("Verifier")
    st.json(result.get("verifier", {}))

    st.subheader("Final Answer")
    st.markdown(result.get("final_answer", ""))
