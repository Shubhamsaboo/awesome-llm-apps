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
import time
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
from policy_directory import lookup_policy, policy_status_headline  # noqa: E402

if str(DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(DEMO_DIR))

from live_tools import (  # noqa: E402
    LIVE_MODEL_ID,
    SKETCH_MODEL_ID,
    TOOL_NAMES,
    build_live_config,
    scheduling_for,
    sketch_prompt,
    summarize_workflow_for_voice,
    tool_headline,
)

GENAI_CLIENT = None
logger = logging.getLogger(__name__)
FRAME_MAX_AGE_SECONDS = 12.0


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
    policy_record: dict[str, Any] | None = None
    live_model: str | None = None
    tool_activity: list[dict[str, Any]] = field(default_factory=list)
    last_workflow_key: str | None = None
    last_workflow: dict[str, Any] | None = None
    evidence_photos: list[dict[str, Any]] = field(default_factory=list)
    camera_notes: list[str] = field(default_factory=list)
    sketch: dict[str, Any] | None = None
    last_frame: bytes | None = None
    last_frame_at: float = 0.0


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


def _intake_text(session: IntakeSession) -> str:
    """Claimant transcript plus what the agent observed on camera, for the claim graph."""

    text = _claimant_text(session)
    if session.camera_notes:
        notes = "\n".join(f"- {note}" for note in session.camera_notes)
        text = f"{text}\n\nEvidence the intake agent observed on the claimant's camera:\n{notes}"
    return text.strip()


def _data_url(data: bytes, mime_type: str) -> str:
    return f"data:{mime_type};base64,{base64.b64encode(data).decode('ascii')}"


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
        **_policy_fields(session, counted),
    }

    progress = max(12, round(completed / len(fields) * 100))
    return {
        "route": route,
        "progress": progress,
        "fields": fields,
        "transcript": session.transcript,
        "events": events,
        "policy": session.policy_record,
        "tool_activity": session.tool_activity[-12:],
        "live_model": session.live_model,
        "missing_blockers": validation.get("missing_fields", []),
        "documents": checklist.get("items", []),
        "evidence_photos": session.evidence_photos,
        "camera_notes": session.camera_notes,
        "sketch": session.sketch,
        "severity": classification.severity,
        "claim_type": classification.claim_type.replace("_", " "),
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


def _policy_fields(session: IntakeSession, counted) -> dict[str, dict[str, str]]:
    """Policy verification rows sourced from the background lookup_policy tool."""

    record = session.policy_record
    source = "Policy directory lookup"
    if not record:
        return {
            "policyStatus": counted(_field("Policy status", "")),
            "policyLine": counted(_field("Policy line", "")),
            "deductible": counted(_field("Deductibles", "")),
            "coverages": counted(_field("Coverages on file", "")),
        }
    if not record.get("found"):
        return {
            "policyStatus": counted(_field("Policy status", "Not found - confirm number", source=source, urgent=True)),
            "policyLine": counted(_field("Policy line", "")),
            "deductible": counted(_field("Deductibles", "")),
            "coverages": counted(_field("Coverages on file", "")),
        }
    deductibles = ", ".join(
        f"{name.replace('_', ' ')} ${int(amount):,}" for name, amount in record.get("deductibles", {}).items()
    )
    return {
        "policyStatus": counted(
            _field(
                "Policy status",
                policy_status_headline(record),
                source=source,
                urgent=str(record.get("status")) != "active",
            )
        ),
        "policyLine": counted(_field("Policy line", record.get("policy_line", ""), source=source)),
        "deductible": counted(_field("Deductibles", deductibles or "None listed", source=source)),
        "coverages": counted(_field("Coverages on file", "; ".join(record.get("coverages", [])), source=source)),
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


def _attach_policy_from_claim(session: IntakeSession, workflow: dict[str, Any]) -> None:
    """Verify an extracted policy number against the directory if the voice agent has not yet."""

    if session.policy_record and session.policy_record.get("found"):
        return
    number = str(workflow["normalized_claim"].get("policy_number", "")).strip()
    if not number or number.lower() in {"not specified", "unknown"}:
        return
    record = lookup_policy(number)
    if record.get("found") or session.policy_record is None:
        session.policy_record = record


async def _run_workflow_cached(session: IntakeSession) -> dict[str, Any]:
    """Run the ADK graph for the current claimant transcript, reusing the last result if unchanged."""

    text = _intake_text(session)
    if session.last_workflow is not None and session.last_workflow_key == text:
        return session.last_workflow
    workflow = await run_claim_workflow(text, session_id=session.session_id)
    session.last_workflow_key = text
    session.last_workflow = workflow
    _attach_policy_from_claim(session, workflow)
    return workflow


async def _process_with_adk_graph(
    session: IntakeSession,
    *,
    add_claimant_facing_reply: bool,
) -> dict[str, Any]:
    workflow = await _run_workflow_cached(session)
    if add_claimant_facing_reply:
        packet = workflow["claim_intake_packet"]
        session.transcript.append({"speaker": "Agent", "text": packet["claimant_next_message"]})
    return _state_from_workflow(session, workflow)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "model": MODEL,
        "has_api_key": _has_api_key(),
        "live_model": LIVE_MODEL_ID,
        "sketch_model": SKETCH_MODEL_ID,
        "tools": TOOL_NAMES,
    }


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


def _pin_evidence_photo(session: IntakeSession, args: dict[str, Any]) -> dict[str, Any]:
    """Tape the most recent camera frame into the notebook with the agent's caption."""

    observation = str(args.get("observation") or args.get("caption") or "").strip()
    claimant_said = str(args.get("claimant_description", "")).strip()
    confirmed = bool(args.get("confirmed", False))
    if not observation:
        return {"pinned": False, "message": "An observation describing what you can see in the frame is required."}
    if session.last_frame is None:
        return {
            "pinned": False,
            "message": "No camera frame has arrived yet. Ask the claimant to turn on the camera and show the damage.",
        }
    if time.monotonic() - session.last_frame_at > FRAME_MAX_AGE_SECONDS:
        return {
            "pinned": False,
            "message": "The camera stopped sending frames. Ask the claimant to turn the camera back on.",
        }
    photo = {
        "id": uuid.uuid4().hex,
        "data_url": _data_url(session.last_frame, "image/jpeg"),
        "caption": observation,
        "claimant_description": claimant_said,
        "confirmed": confirmed,
        "evidence_type": str(args.get("evidence_type", "damage")).strip() or "damage",
        "captured_at": time.strftime("%H:%M"),
    }
    session.evidence_photos.append(photo)
    note = f"Agent saw on camera: {observation}"
    if claimant_said:
        note += f" Claimant described it as: {claimant_said}."
        note += " Confirmed on camera." if confirmed else " Not confirmed on camera; needs a clearer photo."
    session.camera_notes.append(note)
    return {
        "pinned": True,
        "confirmed": confirmed,
        "photo_count": len(session.evidence_photos),
        "message": (
            "Frame taped into the notebook as confirmed evidence."
            if confirmed
            else "Frame taped into the notebook marked as not confirmed. Ask for a closer or brighter view, then pin again."
        ),
    }


async def _draw_incident_sketch(session: IntakeSession, args: dict[str, Any]) -> dict[str, Any]:
    """Generate a pen sketch of the incident scene with the image model."""

    brief = str(args.get("scene_description", "")).strip()
    if not brief:
        return {"sketched": False, "message": "A scene description is required."}
    from google.genai import types

    response = await _client().aio.models.generate_content(
        model=SKETCH_MODEL_ID,
        contents=sketch_prompt(brief),
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    image_part = next(
        (
            part
            for candidate in response.candidates or []
            for part in (candidate.content.parts if candidate.content else [])
            if part.inline_data and part.inline_data.data
        ),
        None,
    )
    if image_part is None:
        return {"sketched": False, "message": "The sketch model returned no image. Continue without it."}
    version = (session.sketch or {}).get("version", 0) + 1
    session.sketch = {
        "data_url": _data_url(image_part.inline_data.data, image_part.inline_data.mime_type or "image/png"),
        "brief": brief,
        "version": version,
        "confirmed": False,
    }
    return {
        "sketched": True,
        "version": version,
        "next_step": "Tell the claimant the sketch is in the notebook and ask if it looks right.",
    }


def _current_ui_state(session: IntakeSession) -> dict[str, Any]:
    """Rebuild the UI state from the cached workflow without re-running the graph."""

    workflow = session.last_workflow or build_initial_workflow_state()
    return _state_from_workflow(session, workflow)


@app.websocket("/ws/live")
async def live_voice(websocket: WebSocket) -> None:
    await websocket.accept()
    live_model = LIVE_MODEL_ID
    session_id = str(uuid.uuid4())
    session = IntakeSession(session_id=session_id, live_model=live_model)
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
            "model": live_model,
            "sketch_model": SKETCH_MODEL_ID,
            "tools": TOOL_NAMES,
            "message": "Gemini 3.8 Live voice session connected.",
        }
    )

    config = build_live_config()

    state_lock = asyncio.Lock()
    background_tasks: set[asyncio.Task] = set()
    tool_tasks: dict[str, asyncio.Task] = {}
    pending_input = ""
    pending_output = ""

    def track(task: asyncio.Task) -> None:
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

    def schedule_state_update(text: str) -> None:
        track(asyncio.create_task(update_claim_state(text)))

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

    async def finalize_input(reason: str) -> None:
        nonlocal pending_input
        finished = pending_input.strip()
        if not finished:
            return
        pending_input = ""
        await websocket.send_json(
            {"type": "transcript", "speaker": "Claimant", "text": finished, "final": True, "reason": reason}
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
            {"type": "transcript", "speaker": "Agent", "text": finished, "final": True, "reason": reason}
        )

    def record_activity(entry: dict[str, Any]) -> None:
        session.tool_activity = [item for item in session.tool_activity if item["id"] != entry["id"]]
        session.tool_activity.append(entry)
        session.tool_activity = session.tool_activity[-30:]

    async def publish_tool(entry: dict[str, Any]) -> None:
        record_activity(entry)
        await websocket.send_json({"type": "tool", **entry})

    async def execute_tool(fc: Any, live_session: Any) -> None:
        """Run one background tool call and hand the result back to Gemini Live."""

        started = time.monotonic()
        name = str(fc.name or "")
        args = dict(fc.args or {})
        call_id = str(fc.id or uuid.uuid4())
        entry: dict[str, Any] = {
            "id": call_id,
            "name": name,
            "args": args,
            "phase": "running",
            "headline": tool_headline(name, args, None),
            "model": live_model,
        }
        await publish_tool(entry)

        urgent = False
        refresh_ui_after_response = False
        try:
            if name == "lookup_policy":
                result = lookup_policy(str(args.get("policy_number", "")))
                session.policy_record = result
                urgent = bool(result.get("found") and str(result.get("status")) != "active")
                refresh_ui_after_response = True
            elif name == "sync_claim_packet":
                await finalize_input("tool_call")
                async with state_lock:
                    workflow = await _run_workflow_cached(session)
                    await websocket.send_json(
                        {"type": "state", "state": _state_from_workflow(session, workflow)}
                    )
                result = summarize_workflow_for_voice(workflow)
                urgent = bool(result["safety_escalation"])
            elif name == "pin_evidence_photo":
                result = _pin_evidence_photo(session, args)
                refresh_ui_after_response = True
            elif name == "draw_incident_sketch":
                result = await _draw_incident_sketch(session, args)
                refresh_ui_after_response = True
            else:
                result = {"error": f"Unknown tool: {name}"}
        except asyncio.CancelledError:
            entry.update(phase="cancelled", headline="Cancelled by the model", duration_ms=int((time.monotonic() - started) * 1000))
            await publish_tool(entry)
            raise
        except Exception as exc:
            logger.exception("Tool %s failed", name)
            result = {"error": str(exc)}

        scheduling = scheduling_for(urgent=urgent)
        await live_session.send_tool_response(
            function_responses=[
                types.FunctionResponse(
                    id=fc.id,
                    name=name,
                    response=result,
                    scheduling=scheduling,
                )
            ]
        )
        entry.update(
            phase="error" if "error" in result else "done",
            headline=result["error"] if "error" in result else tool_headline(name, args, result),
            scheduling=scheduling.value if scheduling else None,
            urgent=urgent,
            duration_ms=int((time.monotonic() - started) * 1000),
            result=result,
        )
        await publish_tool(entry)
        if refresh_ui_after_response:
            # The model already has its answer; the operator UI can wait for the state lock.
            async with state_lock:
                await websocket.send_json({"type": "state", "state": _current_ui_state(session)})

    def launch_tool(fc: Any, live_session: Any) -> None:
        task = asyncio.create_task(execute_tool(fc, live_session))
        tool_tasks[str(fc.id)] = task
        task.add_done_callback(lambda done, key=str(fc.id): tool_tasks.pop(key, None))
        track(task)

    try:
        async with _client().aio.live.connect(model=live_model, config=config) as live_session:
            async def client_to_gemini() -> None:
                while True:
                    message = await websocket.receive_json()
                    msg_type = message.get("type")
                    if msg_type == "audio":
                        data = base64.b64decode(message["data"])
                        await live_session.send_realtime_input(
                            audio=types.Blob(data=data, mime_type="audio/pcm;rate=16000")
                        )
                    elif msg_type == "video":
                        frame = base64.b64decode(message["data"])
                        session.last_frame = frame
                        session.last_frame_at = time.monotonic()
                        await live_session.send_realtime_input(
                            video=types.Blob(data=frame, mime_type="image/jpeg")
                        )
                    elif msg_type == "text":
                        text = str(message.get("text", "")).strip()
                        if text:
                            async with state_lock:
                                session.transcript.append({"speaker": "Claimant", "text": text})
                            await live_session.send_client_content(
                                turns=types.Content(role="user", parts=[types.Part(text=text)]),
                                turn_complete=True,
                            )
                            async with state_lock:
                                state = await _process_with_adk_graph(session, add_claimant_facing_reply=False)
                                await websocket.send_json({"type": "state", "state": state})
                    elif msg_type == "close":
                        await websocket.close()
                        return

            async def gemini_to_client() -> None:
                nonlocal pending_input, pending_output
                while True:
                    turn = live_session.receive()
                    async for response in turn:
                        if response.tool_call and response.tool_call.function_calls:
                            await finalize_input("tool_call")
                            for fc in response.tool_call.function_calls:
                                launch_tool(fc, live_session)

                        if response.tool_call_cancellation and response.tool_call_cancellation.ids:
                            for call_id in response.tool_call_cancellation.ids:
                                task = tool_tasks.get(str(call_id))
                                if task:
                                    task.cancel()

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
                                if getattr(part, "thought", False) and part.text:
                                    await websocket.send_json({"type": "thought", "text": part.text})
                                    continue
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
