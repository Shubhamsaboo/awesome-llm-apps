import ipaddress
import os
import socket
from typing import Any, Literal, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from google.genai import types as genai_types
from pydantic import BaseModel, Field, HttpUrl
from starlette.concurrency import run_in_threadpool

from app_state import RAG_STORE

SETUP_ERROR = ""

try:
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from agentic_rag_agent.agent import build_agent

    ADK_AVAILABLE = bool(os.getenv("GOOGLE_API_KEY"))
except Exception:
    Runner = None
    InMemorySessionService = None
    build_agent = None
    ADK_AVAILABLE = False
    SETUP_ERROR = "Google ADK could not be imported. Install backend requirements and set GOOGLE_API_KEY."

if not os.getenv("GOOGLE_API_KEY"):
    SETUP_ERROR = "GOOGLE_API_KEY is required for Gemini Embedding 2 and the ADK answer flow."


APP_NAME = "multimodal_agentic_rag"
USER_ID = "demo-user"

app = FastAPI(title="Multimodal Agentic RAG ADK")
allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5177,http://127.0.0.1:5177").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_service = InMemorySessionService() if ADK_AVAILABLE else None


class TextSourceRequest(BaseModel):
    title: str
    text: str
    modality: Literal["text"] = "text"


class UrlSourceRequest(BaseModel):
    url: HttpUrl
    title: Optional[str] = None


class AskRequest(BaseModel):
    question: str
    top_k: int = Field(6, ge=1, le=12)


def _extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return " ".join(soup.get_text(" ").split())


def _validate_fetch_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only HTTP and HTTPS URLs are supported.")

    if os.getenv("ALLOW_PRIVATE_URLS", "").lower() == "true":
        return

    if parsed.hostname.lower() == "localhost":
        raise ValueError("Private and localhost URLs are disabled for URL ingestion.")

    try:
        address_info = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror as exc:
        raise ValueError(f"Could not resolve URL host: {parsed.hostname}") from exc

    for item in address_info:
        address = ipaddress.ip_address(item[4][0])
        if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
            raise ValueError("Private and localhost URLs are disabled for URL ingestion.")


def _event_text(event: Any) -> str:
    if not getattr(event, "content", None) or not event.content.parts:
        return ""
    fragments = []
    for part in event.content.parts:
        text = getattr(part, "text", None)
        if text:
            fragments.append(text)
    return "".join(fragments)


async def _run_adk_agent(question: str, retrieval: dict[str, Any]) -> str:
    if not ADK_AVAILABLE:
        raise HTTPException(503, SETUP_ERROR or "Google ADK is unavailable.")

    def retrieve_relevant_context(query: str, top_k: int = 6) -> dict:
        """Return the exact retrieval packet already embedded for this request."""
        return retrieval

    request_agent = build_agent(retrieve_relevant_context)
    request_runner = Runner(agent=request_agent, app_name=APP_NAME, session_service=session_service)
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID)
    try:
        content = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=f"Question: {question}\nUse the retrieval tool result for this exact question.")],
        )
        final_text = ""
        async for event in request_runner.run_async(
            user_id=USER_ID,
            session_id=session.id,
            new_message=content,
        ):
            text = _event_text(event)
            if text:
                final_text = text
        return final_text
    finally:
        # Each request owns a fresh session; no later request reuses its history.
        await session_service.delete_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session.id
        )


@app.get("/health")
async def health():
    return {
        "status": "ok" if ADK_AVAILABLE and not SETUP_ERROR else "setup_required",
        "adk": ADK_AVAILABLE,
        "setup_error": SETUP_ERROR,
        **await run_in_threadpool(RAG_STORE.space_tool),
    }


@app.get("/space")
async def space():
    return await run_in_threadpool(RAG_STORE.snapshot)


@app.post("/sources/text")
async def add_text_source(req: TextSourceRequest):
    try:
        source = await run_in_threadpool(RAG_STORE.add_text_source, req.title, req.text, req.modality)
        snapshot = await run_in_threadpool(RAG_STORE.snapshot)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"source": source.__dict__, "space": snapshot}


@app.post("/sources/url")
async def add_url_source(req: UrlSourceRequest):
    try:
        url = str(req.url)
        await run_in_threadpool(_validate_fetch_url, url)
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
        text = _extract_text_from_html(response.text)
        title = req.title or url.replace("https://", "").replace("http://", "")[:80]
        source = await run_in_threadpool(RAG_STORE.add_text_source, title, text[:12000], "url")
        snapshot = await run_in_threadpool(RAG_STORE.snapshot)
    except Exception as exc:
        raise HTTPException(400, f"Could not ingest URL: {exc}") from exc
    return {"source": source.__dict__, "space": snapshot}


@app.post("/sources/file")
async def add_file_source(
    file: UploadFile = File(...),
    title: str = Form(""),
    notes: str = Form(""),
):
    data = await file.read()
    if len(data) > 120 * 1024 * 1024:
        raise HTTPException(400, "File too large for this demo. Keep uploads under 120 MB.")
    try:
        source = await run_in_threadpool(
            RAG_STORE.add_file_source,
            title=title or file.filename or "Uploaded source",
            data=data,
            mime_type=file.content_type or "application/octet-stream",
            notes=notes,
        )
        snapshot = await run_in_threadpool(RAG_STORE.snapshot)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"source": source.__dict__, "space": snapshot}


@app.delete("/sources/{source_id}")
async def delete_source(source_id: str):
    removed = await run_in_threadpool(RAG_STORE.remove_source, source_id)
    if not removed:
        raise HTTPException(404, "Source not found.")
    return {"deleted": source_id, "space": await run_in_threadpool(RAG_STORE.snapshot)}


@app.post("/ask")
async def ask(req: AskRequest):
    if not req.question.strip():
        raise HTTPException(400, "Question is required.")

    retrieval = await run_in_threadpool(RAG_STORE.search, req.question, req.top_k)
    retrieval_payload = RAG_STORE.retrieval_payload(retrieval)
    answer = await _run_adk_agent(req.question, retrieval_payload)
    trace = [
        {
            "agent": "space_inspector",
            "status": "complete",
            "detail": f"{len(RAG_STORE.sources)} sources, {len(RAG_STORE.chunks)} chunks, {RAG_STORE.dimensions} dimensions",
        },
        {
            "agent": "retrieval_tool",
            "status": "complete",
            "detail": f"Embedded query and retrieved {len(retrieval['matches'])} nearest sources",
        },
        {
            "agent": "answer_synthesizer",
            "status": "complete",
            "detail": "Generated grounded answer; citations are shown separately",
        },
    ]
    return {
        "answer": answer,
        "matches": retrieval["matches"],
        "query_point": retrieval["query_point"],
        "trace": trace,
        "space": retrieval["space"],
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8897"))
    uvicorn.run(app, host="0.0.0.0", port=port)
