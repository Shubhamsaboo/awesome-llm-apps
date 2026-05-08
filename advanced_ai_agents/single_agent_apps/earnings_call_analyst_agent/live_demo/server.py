from __future__ import annotations

import asyncio
import os
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

APP_DIR = Path(__file__).resolve().parents[1]
DEMO_DIR = Path(__file__).resolve().parent
APP_PARENT_DIR = APP_DIR.parent
if str(APP_PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(APP_PARENT_DIR))


def _load_env() -> None:
    env_path = APP_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env()
if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

from earnings_call_analyst_agent.agent import generate_insights  # noqa: E402
from earnings_call_analyst_agent.research import build_research_pack  # noqa: E402
from earnings_call_analyst_agent.schemas import AnalysisSession  # noqa: E402
from earnings_call_analyst_agent.youtube_ingest import (  # noqa: E402
    chunk_transcript,
    extract_video_id,
    fetch_transcript,
    fetch_video_metadata,
    transcribe_audio_with_adk,
)


class SessionRequest(BaseModel):
    youtube_url: str


class SessionCreated(BaseModel):
    session_id: str


@dataclass
class RuntimeSession:
    session_id: str
    youtube_url: str
    status: Literal["queued", "metadata", "transcript", "research", "analysis", "ready", "error"] = "queued"
    progress: int = 0
    message: str = "Queued"
    data: AnalysisSession | None = None
    error: str = ""
    diagnostics: dict[str, Any] = field(default_factory=dict)


sessions: dict[str, RuntimeSession] = {}
session_lock = asyncio.Lock()

app = FastAPI(title="📡 Earnings Call Analyst Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:4188", "http://localhost:4188"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=DEMO_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(DEMO_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "has_google_key": bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")),
    }


@app.post("/api/sessions", response_model=SessionCreated)
async def create_session(request: SessionRequest, background_tasks: BackgroundTasks) -> SessionCreated:
    try:
        extract_video_id(request.youtube_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    session_id = uuid.uuid4().hex[:12]
    runtime = RuntimeSession(session_id=session_id, youtube_url=request.youtube_url)
    async with session_lock:
        sessions[session_id] = runtime
    background_tasks.add_task(_run_session, session_id)
    return SessionCreated(session_id=session_id)


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str) -> dict[str, Any]:
    runtime = sessions.get(session_id)
    if not runtime:
        raise HTTPException(status_code=404, detail="Unknown analysis session.")
    payload: dict[str, Any] = {
        "session_id": runtime.session_id,
        "status": runtime.status,
        "progress": runtime.progress,
        "message": runtime.message,
        "error": runtime.error,
        "diagnostics": runtime.diagnostics,
    }
    if runtime.data:
        payload["data"] = runtime.data.model_dump()
    return payload


async def _run_session(session_id: str) -> None:
    runtime = sessions[session_id]
    try:
        await _set_status(runtime, "metadata", 10, "Resolving YouTube video")
        video_id = extract_video_id(runtime.youtube_url)
        metadata = await asyncio.to_thread(fetch_video_metadata, runtime.youtube_url, video_id)

        await _set_status(runtime, "transcript", 25, "Loading YouTube captions")
        try:
            transcript = await asyncio.to_thread(fetch_transcript, video_id)
            transcript_source = "youtube_captions"
        except Exception:
            await _set_status(
                runtime,
                "transcript",
                32,
                "Captions unavailable; transcribing audio with ADK",
            )
            transcript = await asyncio.to_thread(
                transcribe_audio_with_adk,
                video_id,
                lambda progress, message: _set_status_from_thread(runtime, progress, message),
            )
            transcript_source = "adk_audio"
        if not transcript:
            raise RuntimeError("This video did not return usable transcript segments.")
        chunks = chunk_transcript(transcript, window_seconds=42)

        await _set_status(runtime, "research", 45, "Building company research pack")
        research = await asyncio.to_thread(build_research_pack, metadata, transcript)

        await _set_status(runtime, "analysis", 70, "Curating high-signal analyst cards")
        insights = await asyncio.to_thread(generate_insights, metadata, research, chunks)

        runtime.data = AnalysisSession(
            session_id=session_id,
            video=metadata,
            transcript=transcript,
            chunks=chunks,
            research=research,
            insights=insights,
            status="ready" if insights else "partial",
            message="Ready" if insights else "Ready with transcript and research; no high-signal insights were emitted.",
            diagnostics={
                "transcript_segments": len(transcript),
                "transcript_source": transcript_source,
                "chunks": len(chunks),
                "insights": len(insights),
                "analysis_engine": "adk" if os.getenv("GOOGLE_API_KEY") else "local_fallback",
            },
        )
        await _set_status(runtime, "ready", 100, runtime.data.message)
    except Exception as exc:
        runtime.status = "error"
        runtime.progress = 100
        runtime.error = str(exc)
        runtime.message = "Analysis failed"


async def _set_status(
    runtime: RuntimeSession,
    status: Literal["queued", "metadata", "transcript", "research", "analysis", "ready", "error"],
    progress: int,
    message: str,
) -> None:
    runtime.status = status
    runtime.progress = progress
    runtime.message = message
    await asyncio.sleep(0)


def _set_status_from_thread(runtime: RuntimeSession, progress: int, message: str) -> None:
    runtime.status = "transcript"
    runtime.progress = progress
    runtime.message = message
