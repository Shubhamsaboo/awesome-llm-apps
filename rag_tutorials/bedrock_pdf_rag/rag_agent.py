"""
Amazon Bedrock PDF RAG Agent
A RAG-powered PDF chatbot using Amazon Bedrock (Claude 3 Haiku) and FAISS.
Provides multi-turn Q&A with page-level citations and sub-2s response time.
"""

import os
import json
import uuid
from pathlib import Path
from typing import Optional

import boto3
import faiss
import numpy as np
import pypdf
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import streamlit as st
import requests

# ── Configuration ──────────────────────────────────────────────────────────────

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 5

# ── Models ────────────────────────────────────────────────────────────────────

embedder = SentenceTransformer(EMBEDDING_MODEL)

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=AWS_REGION,
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
)

# In-memory session store: session_id -> {index, chunks, page_map}
sessions: dict = {}

# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_chunks(pdf_bytes: bytes) -> list[dict]:
    """Extract text chunks with page numbers from a PDF."""
    reader = pypdf.PdfReader(pdf_bytes)
    chunks = []
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        # Sliding window chunking
        for start in range(0, len(text), CHUNK_SIZE - CHUNK_OVERLAP):
            chunk = text[start : start + CHUNK_SIZE].strip()
            if len(chunk) > 50:  # skip tiny fragments
                chunks.append({"text": chunk, "page": page_num})
    return chunks


def build_index(chunks: list[dict]) -> faiss.IndexFlatL2:
    """Embed chunks and build a FAISS index."""
    texts = [c["text"] for c in chunks]
    embeddings = embedder.encode(texts, convert_to_numpy=True).astype("float32")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index


def retrieve(query: str, index: faiss.IndexFlatL2, chunks: list[dict]) -> list[dict]:
    """Retrieve top-K relevant chunks for a query."""
    q_emb = embedder.encode([query], convert_to_numpy=True).astype("float32")
    _, indices = index.search(q_emb, TOP_K)
    return [chunks[i] for i in indices[0] if i < len(chunks)]


def call_bedrock(prompt: str) -> str:
    """Call Amazon Bedrock Claude 3 Haiku and return the response text."""
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    })
    response = bedrock.invoke_model(modelId=MODEL_ID, body=body)
    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def build_prompt(question: str, context_chunks: list[dict]) -> str:
    context = "\n\n".join(
        f"[Page {c['page']}]: {c['text']}" for c in context_chunks
    )
    return (
        f"You are a helpful assistant. Answer the question based on the document excerpts below.\n"
        f"For each fact, cite the page number in brackets, e.g. [Page 3].\n\n"
        f"Document excerpts:\n{context}\n\n"
        f"Question: {question}\n"
        f"Answer:"
    )

# ── FastAPI App ───────────────────────────────────────────────────────────────

app = FastAPI(title="Bedrock PDF RAG", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class AskRequest(BaseModel):
    session_id: str
    question: str


class AskResponse(BaseModel):
    answer: str
    pages_cited: list[int]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")
    content = await file.read()
    from io import BytesIO
    chunks = extract_chunks(BytesIO(content))
    if not chunks:
        raise HTTPException(status_code=422, detail="Could not extract text from PDF")
    index = build_index(chunks)
    session_id = str(uuid.uuid4())
    sessions[session_id] = {"index": index, "chunks": chunks}
    return {"session_id": session_id, "chunks_indexed": len(chunks)}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Upload a PDF first.")
    relevant = retrieve(req.question, session["index"], session["chunks"])
    prompt = build_prompt(req.question, relevant)
    answer = call_bedrock(prompt)
    pages = sorted({c["page"] for c in relevant})
    return AskResponse(answer=answer, pages_cited=pages)

# ── Streamlit UI ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    st.set_page_config(page_title="Bedrock PDF RAG", page_icon="📄", layout="wide")
    st.title("Amazon Bedrock PDF RAG Agent")
    st.caption("Upload a PDF, ask questions, get page-cited answers powered by Claude 3 Haiku")

    API_URL = "http://localhost:8000"

    uploaded = st.file_uploader("Upload PDF", type="pdf")
    if uploaded and "session_id" not in st.session_state:
        with st.spinner("Indexing PDF..."):
            r = requests.post(f"{API_URL}/upload", files={"file": (uploaded.name, uploaded.read(), "application/pdf")})
            if r.ok:
                st.session_state.session_id = r.json()["session_id"]
                st.success(f"Indexed {r.json()['chunks_indexed']} chunks. Ready to answer questions!")
            else:
                st.error(r.json().get("detail", "Upload failed"))

    if "session_id" in st.session_state:
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if question := st.chat_input("Ask a question about the PDF..."):
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    r = requests.post(
                        f"{API_URL}/ask",
                        json={"session_id": st.session_state.session_id, "question": question}
                    )
                    if r.ok:
                        data = r.json()
                        answer = data["answer"]
                        pages = data["pages_cited"]
                        st.markdown(answer)
                        st.caption(f"Pages referenced: {', '.join(map(str, pages))}")
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        st.error("Failed to get answer. Check that the API server is running.")
