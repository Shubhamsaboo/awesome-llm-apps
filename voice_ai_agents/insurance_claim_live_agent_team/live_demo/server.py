"""FastAPI backend for the Insurance Claim Live Agent Team UI.

The browser transport lives here. Claim workflow execution lives in agent.py,
which defines and runs the ADK graph.
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
import logging
import os
import re
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

APP_DIR = Path(__file__).resolve().parents[1]
DEMO_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


def _load_dotenv() -> None:
    env_path = APP_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _cors_origins() -> list[str]:
    raw = os.getenv("FNOL_CORS_ORIGINS", "")
    if raw.strip():
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return ["http://127.0.0.1:4177", "http://localhost:4177"]


_load_dotenv()

from agent import (  # noqa: E402
    MODEL,
    blank_claim,
    build_initial_workflow_state,
    run_claim_workflow,
)
from schemas import ClaimClassification, ClaimNarrative  # noqa: E402

LIVE_MODEL = os.getenv("FNOL_GEMINI_LIVE_MODEL", "gemini-3.1-flash-live-preview")
GENAI_CLIENT = None
logger = logging.getLogger(__name__)


class MessageRequest(BaseModel):
    session_id: str
    text: str


class SessionResponse(BaseModel):
    session_id: str
    model: str
    has_api_key: bool
    state: dict[str, Any]


@dataclass
class IntakeSession:
    session_id: str
    transcript: list[dict[str, str]] = field(default_factory=list)
    normalized_claim: dict[str, Any] | None = None
    classification: dict[str, Any] | None = None
    route: str = "needs_docs"


sessions: dict[str, IntakeSession] = {}

app = FastAPI(title="Insurance Claim Live Agent Team API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)


def _has_api_key() -> bool:
    return bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))


def _client():
    global GENAI_CLIENT
    if not _has_api_key():
        raise HTTPException(
            status_code=503,
            detail=(
                "Missing GOOGLE_API_KEY. Add it to "
                f"{APP_DIR / '.env'} and restart the live intake backend."
            ),
        )
    if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
    try:
        from google import genai
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Missing google-genai package. Run pip install -r requirements.txt.",
        ) from exc
    if GENAI_CLIENT is None:
        GENAI_CLIENT = genai.Client()
    return GENAI_CLIENT


def _claim_from_session(session: IntakeSession) -> dict[str, Any]:
    return session.normalized_claim or blank_claim()


def _claimant_text(session: IntakeSession) -> str:
    return "\n".join(
        turn["text"] for turn in session.transcript if turn["speaker"] == "Claimant"
    )


def _status(value: Any, urgent: bool = False) -> str:
    text = str(value or "").strip().lower()
    if urgent:
        return "urgent"
    if text in {"", "unknown", "not specified", "unspecified", "n/a", "none", "not provided"}:
        return "missing"
    return "complete"


def _without_negated_safety_mentions(text: str) -> str:
    cleaned = str(text or "")
    for pattern in [
        r"\b(?:no|not|none|without|denies|denied)\s+(?:one\s+)?(?:was\s+)?(?:injur\w*|hurt|pain|medical attention|ambulance|hospital|unsafe|hazard\w*|danger)\b",
        r"\b(?:injur\w*|hurt|pain|medical attention|ambulance|hospital|unsafe|hazard\w*|danger)\s+(?:was|were|is|are)?\s*(?:reported\s+)?(?:no|none|not reported|denied)\b",
    ]:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
    return cleaned


def _has_negated_safety_mention(text: str) -> bool:
    return _without_negated_safety_mentions(text) != str(text or "")


def _positive_safety_items(items: list[str]) -> list[str]:
    patterns = [
        r"\binjur",
        r"\bhurt\b",
        r"\bneck pain\b",
        r"\bhospital\b",
        r"\burgent care\b",
        r"\bambulance\b",
        r"\bunsafe\b",
        r"\bhazard",
        r"\bdanger\b",
    ]
    return [
        item
        for item in items
        if any(
            re.search(pattern, _without_negated_safety_mentions(item), flags=re.IGNORECASE)
            for pattern in patterns
        )
    ]


def _join(items: list[str], fallback: str) -> str:
    return ", ".join(items) if items else fallback


def _field(label: str, value: Any, source: str = "Gemini extraction", urgent: bool = False) -> dict[str, str]:
    status = _status(value, urgent=urgent)
    display = value if status != "missing" else f"Missing: {label.lower()}"
    return {
        "label": label,
        "value": str(display),
        "status": status,
        "source": "-" if status == "missing" else source,
    }


def _items_containing(items: list[str], needles: list[str], fallback: str = "Unknown") -> str:
    matches = [
        item
        for item in items
        if any(needle in item.lower() for needle in needles)
    ]
    return _join(matches, fallback)


def _events(
    session: IntakeSession,
    validation: dict[str, Any],
    coverage: dict[str, Any],
    fraud_gate: dict[str, Any],
) -> list[dict[str, str]]:
    events: list[dict[str, str]] = [
        {
            "tone": "success",
            "title": "Gemini extraction complete",
            "detail": f"Updated structured claim facts using {MODEL}.",
            "rule": "LLM-001",
        }
    ]
    if validation.get("missing_fields"):
        events.append(
            {
                "tone": "warning",
                "title": "Missing intake facts",
                "detail": ", ".join(validation["missing_fields"]),
                "rule": "INTAKE-001",
            }
        )
    for finding in coverage.get("findings", []):
        tone = "danger" if finding["required_action"] == "emergency_escalation" else "warning"
        if finding["required_action"] == "adjuster_review":
            tone = "success"
        events.append(
            {
                "tone": tone,
                "title": finding["message"],
                "detail": f"Required action: {finding['required_action']}.",
                "rule": finding["rule_id"],
            }
        )
    for signal in fraud_gate.get("signals", []):
        tone = "danger" if signal.get("route_to_emergency") else "warning"
        events.append(
            {
                "tone": tone,
                "title": signal["message"],
                "detail": "Deterministic fraud/safety gate signal.",
                "rule": signal["signal_id"],
            }
        )
    route = fraud_gate.get("final_routing_decision", coverage.get("routing_decision"))
    if route != session.route:
        events.append(
            {
                "tone": "danger" if route == "emergency_escalation" else "success",
                "title": "Routing changed",
                "detail": f"{session.route} -> {route}.",
                "rule": "ROUTE-001",
            }
        )
    return events


def _ui_state(
    session: IntakeSession,
    validation: dict[str, Any],
    coverage: dict[str, Any],
    checklist: dict[str, Any],
    fraud_gate: dict[str, Any],
    packet: dict[str, Any],
    events: list[dict[str, str]],
) -> dict[str, Any]:
    claim = ClaimNarrative.model_validate(_claim_from_session(session))
    classification = ClaimClassification.model_validate(session.classification)
    route = fraud_gate["final_routing_decision"]
    completed = 0

    def counted(field: dict[str, str]) -> dict[str, str]:
        nonlocal completed
        if field["status"] in {"complete", "urgent"}:
            completed += 1
        return field

    positive_safety_items = _positive_safety_items(claim.injuries_or_safety_concerns)
    safety_text = " ".join(
        [
            claim.loss_description,
            claim.raw_narrative_summary,
            _claimant_text(session),
            *claim.injuries_or_safety_concerns,
        ]
    )
    injury_text = _join(claim.injuries_or_safety_concerns, "Unknown")
    if not positive_safety_items and _has_negated_safety_mention(safety_text):
        injury_text = "No injuries reported"
    evidence_text = _join(claim.evidence_available, "Not captured yet")
    required_doc_names = [item["item"] for item in checklist.get("items", [])]

    fields = {
        "claimant": counted(_field("Claimant name", claim.policyholder_name)),
        "policy": counted(_field("Policy number", claim.policy_number)),
        "contact": counted(_field("Contact method", claim.contact_method)),
        "type": counted(_field("Claim type", classification.claim_type.replace("_", " "))),
        "date": counted(_field("Date of loss", claim.date_of_loss)),
        "time": counted(_field("Reported date", claim.reported_date)),
        "location": counted(_field("Location", claim.loss_location)),
        "description": counted(_field("Loss description", claim.loss_description)),
        "injuries": counted(
            _field(
                "Injuries",
                injury_text,
                source="Gemini extraction + safety gate",
                urgent=bool(positive_safety_items),
            )
        ),
        "hazards": counted(
            _field(
                "Hazards present",
                _items_containing(
                    claim.injuries_or_safety_concerns,
                    ["hazard", "unsafe"],
                ),
            )
        ),
        "medical": counted(
            _field(
                "Medical attention",
                _items_containing(
                    claim.injuries_or_safety_concerns,
                    ["medical", "care", "hospital"],
                ),
            )
        ),
        "police": counted(_field("Report number", _find_report(claim))),
        "photos": counted(_field("Evidence available", evidence_text)),
        "tow": counted(_field("Tow info", _find_text(claim, ["tow", "storage"]))),
        "otherDriver": counted(_field("Other driver info", _find_text(claim, ["other driver", "driver", "plate", "witness"]))),
    }

    progress = max(12, round(completed / len(fields) * 100))
    return {
        "route": route,
        "progress": progress,
        "fields": fields,
        "transcript": session.transcript,
        "events": events,
        "handoff": {
            "Summary": packet["adjuster_handoff_summary"],
            "Priority": f"{classification.severity.title()} - {classification.severity_rationale}",
            "Required actions": _join(required_doc_names, "No additional documents identified by current rules."),
            "Attachments": evidence_text,
            "Next best action": packet["claimant_next_message"],
        },
        "packet_markdown": packet["markdown"],
        "model": MODEL,
    }


def _find_text(claim: ClaimNarrative, needles: list[str]) -> str:
    text = " | ".join(
        [claim.loss_description, *claim.evidence_available, *claim.documents_mentioned, *claim.parties_involved]
    )
    lower = text.lower()
    if any(needle in lower for needle in needles):
        return text
    return "not specified"


def _find_report(claim: ClaimNarrative) -> str:
    text = " | ".join([*claim.evidence_available, *claim.documents_mentioned, claim.loss_description])
    lower = text.lower()
    if any(term in lower for term in ["police", "report", "case number", "incident"]):
        return text
    return "not specified"


def _state_from_workflow(session: IntakeSession, workflow: dict[str, Any]) -> dict[str, Any]:
    validation = workflow["field_validation"]
    coverage = workflow["coverage_evidence_decision"]
    checklist = workflow["document_checklist"]
    fraud_gate = workflow["fraud_safety_gate"]
    packet = workflow["claim_intake_packet"]
    session.normalized_claim = workflow["normalized_claim"]
    session.classification = workflow["claim_classification"]
    events = _events(session, validation, coverage, fraud_gate)
    session.route = fraud_gate["final_routing_decision"]
    return _ui_state(session, validation, coverage, checklist, fraud_gate, packet, events)


async def _process_with_adk_graph(
    session: IntakeSession,
    *,
    add_claimant_facing_reply: bool,
) -> dict[str, Any]:
    workflow = await run_claim_workflow(
        _claimant_text(session),
        session_id=session.session_id,
    )
    if add_claimant_facing_reply:
        packet = workflow["claim_intake_packet"]
        session.transcript.append({"speaker": "Agent", "text": packet["claimant_next_message"]})
    return _state_from_workflow(session, workflow)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "model": MODEL, "has_api_key": _has_api_key()}


@app.post("/api/sessions", response_model=SessionResponse)
def create_session() -> SessionResponse:
    session = IntakeSession(session_id=str(uuid.uuid4()))
    session.transcript.append(
        {
            "speaker": "Agent",
            "text": "I can start the claim while we talk. First, are you and everyone else in a safe place?",
        }
    )
    sessions[session.session_id] = session
    workflow = build_initial_workflow_state()
    session.normalized_claim = workflow["normalized_claim"]
    session.classification = workflow["claim_classification"]
    session.route = workflow["fraud_safety_gate"]["final_routing_decision"]
    state = _ui_state(
        session,
        workflow["field_validation"],
        workflow["coverage_evidence_decision"],
        workflow["document_checklist"],
        workflow["fraud_safety_gate"],
        workflow["claim_intake_packet"],
        [
            {
                "tone": "warning",
                "title": "Waiting for claimant facts",
                "detail": "The ADK graph is ready to process claimant facts.",
                "rule": "SESSION-001",
            }
        ],
    )
    return SessionResponse(
        session_id=session.session_id,
        model=MODEL,
        has_api_key=_has_api_key(),
        state=state,
    )


@app.post("/api/message", response_model=SessionResponse)
async def message(request: MessageRequest) -> SessionResponse:
    session = sessions.get(request.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown intake session.")
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message text is required.")
    session.transcript.append({"speaker": "Claimant", "text": text})
    state = await _process_with_adk_graph(session, add_claimant_facing_reply=True)
    return SessionResponse(
        session_id=session.session_id,
        model=MODEL,
        has_api_key=_has_api_key(),
        state=state,
    )


@app.websocket("/ws/live")
async def live_voice(websocket: WebSocket) -> None:
    await websocket.accept()
    session_id = str(uuid.uuid4())
    session = IntakeSession(session_id=session_id)
    session.transcript.append(
        {
            "speaker": "Agent",
            "text": "I can start the claim while we talk. First, are you and everyone else in a safe place?",
        }
    )
    sessions[session_id] = session

    try:
        from google.genai import types
    except ImportError:
        await websocket.send_json(
            {"type": "error", "message": "Missing google-genai package. Run pip install -r requirements.txt."}
        )
        await websocket.close()
        return

    if not _has_api_key():
        await websocket.send_json(
            {
                "type": "error",
                "message": f"Missing GOOGLE_API_KEY. Add it to {APP_DIR / '.env'} and restart the backend.",
            }
        )
        await websocket.close()
        return

    await websocket.send_json(
        {
            "type": "session",
            "session_id": session_id,
            "model": LIVE_MODEL,
            "message": "Gemini Live voice session connected.",
        }
    )

    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=(
            "You are a voice insurance FNOL intake agent. Speak naturally and briefly. "
            "Your job is to collect enough blocking intake facts for a smooth adjuster handoff, "
            "not to end the call after the claimant's first narrative. If injury, unsafe housing, "
            "or immediate danger is mentioned, prioritize safety and human escalation. Otherwise, "
            "keep asking for missing blockers one step at a time: claimant name, contact method, "
            "policy number if available, date and location of loss, what happened, safety/injury "
            "status, evidence, documents, reports, tow details, or other involved parties. Do not "
            "promise coverage, payment, liability, benefits, or approval. Ask only one or two "
            "focused follow-up questions at a time."
        ),
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
            )
        ),
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
    )

    state_lock = asyncio.Lock()
    background_tasks: set[asyncio.Task] = set()

    def schedule_state_update(text: str) -> None:
        task = asyncio.create_task(update_claim_state(text))
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

    async def update_claim_state(text: str) -> None:
        if not text.strip():
            return
        async with state_lock:
            session.transcript.append({"speaker": "Claimant", "text": text.strip()})
            try:
                state = await _process_with_adk_graph(session, add_claimant_facing_reply=False)
                await websocket.send_json({"type": "state", "state": state})
            except Exception as exc:
                await websocket.send_json({"type": "error", "message": f"Claim state update failed: {exc}"})

    try:
        async with _client().aio.live.connect(model=LIVE_MODEL, config=config) as live_session:
            async def client_to_gemini() -> None:
                while True:
                    message = await websocket.receive_json()
                    msg_type = message.get("type")
                    if msg_type == "audio":
                        data = base64.b64decode(message["data"])
                        await live_session.send_realtime_input(
                            audio=types.Blob(data=data, mime_type="audio/pcm;rate=16000")
                        )
                    elif msg_type == "text":
                        text = str(message.get("text", "")).strip()
                        if text:
                            session.transcript.append({"speaker": "Claimant", "text": text})
                            await live_session.send(input=text, end_of_turn=True)
                            state = await _process_with_adk_graph(session, add_claimant_facing_reply=False)
                            await websocket.send_json({"type": "state", "state": state})
                    elif msg_type == "close":
                        await websocket.close()
                        return

            async def gemini_to_client() -> None:
                pending_input = ""
                pending_output = ""

                async def finalize_input(reason: str) -> None:
                    nonlocal pending_input
                    finished = pending_input.strip()
                    if not finished:
                        return
                    pending_input = ""
                    await websocket.send_json(
                        {
                            "type": "transcript",
                            "speaker": "Claimant",
                            "text": finished,
                            "final": True,
                            "reason": reason,
                        }
                    )
                    schedule_state_update(finished)

                async def finalize_output(reason: str) -> None:
                    nonlocal pending_output
                    finished = pending_output.strip()
                    if not finished:
                        return
                    pending_output = ""
                    session.transcript.append({"speaker": "Agent", "text": finished})
                    await websocket.send_json(
                        {
                            "type": "transcript",
                            "speaker": "Agent",
                            "text": finished,
                            "final": True,
                            "reason": reason,
                        }
                    )

                while True:
                    turn = live_session.receive()
                    async for response in turn:
                        server_content = response.server_content
                        if not server_content:
                            continue

                        if server_content.input_transcription and server_content.input_transcription.text:
                            text = server_content.input_transcription.text
                            pending_input += text
                            await websocket.send_json(
                                {
                                    "type": "transcript",
                                    "speaker": "Claimant",
                                    "text": pending_input,
                                    "delta": text,
                                    "final": bool(getattr(server_content.input_transcription, "finished", False)),
                                }
                            )
                            if getattr(server_content.input_transcription, "finished", False):
                                await finalize_input("input_transcription_finished")

                        if server_content.output_transcription and server_content.output_transcription.text:
                            await finalize_input("model_started_response")
                            text = server_content.output_transcription.text
                            pending_output += text
                            await websocket.send_json(
                                {
                                    "type": "transcript",
                                    "speaker": "Agent",
                                    "text": pending_output,
                                    "delta": text,
                                    "final": bool(getattr(server_content.output_transcription, "finished", False)),
                                }
                            )
                            if getattr(server_content.output_transcription, "finished", False):
                                await finalize_output("output_transcription_finished")

                        if server_content.model_turn:
                            await finalize_input("model_audio_started")
                            for part in server_content.model_turn.parts or []:
                                if part.inline_data and isinstance(part.inline_data.data, bytes):
                                    await websocket.send_json(
                                        {
                                            "type": "audio",
                                            "data": base64.b64encode(part.inline_data.data).decode("ascii"),
                                            "mime_type": part.inline_data.mime_type or "audio/pcm;rate=24000",
                                        }
                                    )

                        if server_content.interrupted:
                            pending_output = ""
                            await websocket.send_json({"type": "interrupted"})

                        if (
                            getattr(server_content, "generation_complete", False)
                            or getattr(server_content, "turn_complete", False)
                            or getattr(server_content, "waiting_for_input", False)
                        ):
                            await finalize_output("live_turn_complete")

            tasks = {
                asyncio.create_task(client_to_gemini()),
                asyncio.create_task(gemini_to_client()),
            }
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            for task in pending:
                with contextlib.suppress(asyncio.CancelledError):
                    await task
            for task in done:
                task.result()
    except WebSocketDisconnect:
        return
    except Exception as exc:
        logger.exception("Gemini Live session failed")
        try:
            await websocket.send_json({"type": "error", "message": f"Gemini Live session failed: {exc}"})
        except Exception:
            pass
    finally:
        for task in list(background_tasks):
            task.cancel()
        for task in list(background_tasks):
            with contextlib.suppress(asyncio.CancelledError):
                await task


@app.get("/")
def index() -> FileResponse:
    return FileResponse(DEMO_DIR / "index.html")


app.mount("/", StaticFiles(directory=DEMO_DIR, html=True), name="static")
