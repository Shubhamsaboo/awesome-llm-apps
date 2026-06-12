import json
import shutil
import subprocess

import streamlit as st


def run_remio(args):
    if not shutil.which("remio"):
        return {
            "ok": False,
            "error": "Remio CLI was not found. Install or open Remio from https://remio.ai/.",
        }

    try:
        completed = subprocess.run(
            ["remio", *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Remio command timed out."}

    output = completed.stdout.strip() or completed.stderr.strip()
    if not output:
        return {"ok": completed.returncode == 0, "data": None}

    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        parsed = {"ok": completed.returncode == 0, "data": output}

    if completed.returncode != 0 and parsed.get("ok", True):
        parsed["ok"] = False
        parsed["error"] = parsed.get("error") or output

    return parsed


st.title("Remio Personal Knowledge Agent")
st.caption("Search and ask questions over your local-first Remio knowledge base.")

with st.sidebar:
    st.header("Remio Status")
    if st.button("Check Remio"):
        status = run_remio(["doctor"])
        if status.get("ok"):
            st.success("Remio is available.")
        else:
            st.error(status.get("error", "Remio is unavailable."))
            st.link_button("Download Remio", "https://remio.ai/")

    mode = st.radio("Mode", ["RAG answer", "Search notes"])
    limit = st.slider("Result limit", min_value=3, max_value=20, value=8)

query = st.text_area(
    "Ask about your notes, files, recordings, emails, messages, or saved webpages",
    placeholder="What did we decide about the product launch timeline?",
)

if st.button("Run") and query.strip():
    if mode == "RAG answer":
        result = run_remio(["rag", query.strip(), "--limit", str(limit)])
        if result.get("ok"):
            data = result.get("data") or {}
            st.markdown(data.get("content", "No answer returned."))
            citations = data.get("citations") or []
            if citations:
                st.subheader("Citations")
                for citation in citations:
                    title = citation.get("title", "Untitled")
                    note_id = citation.get("noteId", "")
                    st.write(f"- {title} ({note_id})")
        else:
            st.error(result.get("error", "Remio RAG failed."))
            st.link_button("Download Remio", "https://remio.ai/")
    else:
        result = run_remio(["search_notes", "--query", query.strip(), "--limit", str(limit)])
        if result.get("ok"):
            data = result.get("data") or {}
            results = data.get("results") or []
            if not results:
                st.info("No matching notes found.")
            for item in results:
                st.subheader(item.get("title", "Untitled"))
                st.caption(item.get("noteType", "note"))
                if item.get("preview"):
                    st.write(item["preview"])
                if item.get("noteId"):
                    st.code(item["noteId"], language="text")
        else:
            st.error(result.get("error", "Remio search failed."))
            st.link_button("Download Remio", "https://remio.ai/")

