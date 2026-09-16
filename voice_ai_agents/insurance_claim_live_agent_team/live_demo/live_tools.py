"""Gemini 3.8 Live configuration and background tool contracts for the voice agent.

Gemini 3.8 Live runs function calls in the background (behavior NON_BLOCKING)
so the voice agent keeps talking while the claim team works. The tools here are
the bridge between the live call, the ADK claim graph, the mock policy
directory, the claimant's camera, and the sketch model. Execution lives in
server.py, which owns the session state.
"""

from __future__ import annotations

import os
from typing import Any

from google.genai import types

LIVE_MODEL_ID = os.getenv("FNOL_GEMINI_LIVE_MODEL", "gemini-3.8-live")
SKETCH_MODEL_ID = os.getenv("FNOL_SKETCH_MODEL", "gemini-3.1-flash-image")
VOICE_NAME = os.getenv("FNOL_VOICE", "Kore")

TOOL_NAMES = ["lookup_policy", "sync_claim_packet", "pin_evidence_photo", "draw_incident_sketch"]

SYSTEM_INSTRUCTION = """
You are the live voice intake agent for an insurance first notice of loss (FNOL) team.
Speak naturally, warmly, and briefly. The claimant may be stressed. Acknowledge what
they say, then keep the intake moving one or two questions at a time. Your notes are
written into a field notebook the claimant can see, so narrate what you are doing in
short asides like "I'm noting that" or "let me check that policy".

You work with a claim team that runs in the background while you talk:
- lookup_policy: verifies a policy number against the carrier's policy records.
  Call it as soon as you hear a policy number. Keep talking while it runs. When it
  returns, confirm the policyholder name and policy line out loud in one sentence.
  If the policy is lapsed or not found, say a human reviewer will check it and do
  not stop collecting loss facts.
- sync_claim_packet: sends everything the claimant has said, plus your camera
  observations, to the claim team, which extracts facts, applies deterministic
  intake rules, and returns the routing decision and the list of open items the
  packet still needs. Call it after the claimant shares new loss facts, roughly
  every turn or two. The open items are a checklist, not a script. Never interrupt
  the current topic to ask one. Finish what the claimant is describing or showing,
  acknowledge it, and only then pick the open item that follows naturally from
  where the conversation is. Dates, addresses, and policy numbers wait until the
  current topic is closed.
- pin_evidence_photo: the claimant can turn on their camera and show you the damage.
  Whenever you can see anything relevant to the claim on camera (damage, water
  lines, dents, broken items, the scene or layout, a floor plan, receipts, documents,
  serial numbers), say what you see in one or two concrete sentences and call
  pin_evidence_photo in that same turn. The current camera frame gets taped into the
  notebook. Do this the first time you see each new thing; do not wait to be asked
  and do not postpone it to a later turn. Skip frames that show nothing relevant,
  like a blank wall or a face.
  Your eyes are the adjuster's eyes, so report only what you can actually see. If
  the claimant names something (a crack, a leak, mold, a dent) and the frame does
  not clearly show it, do not repeat their word as if you saw it. Say what you do
  see ("I can see a dark mark about the size of a coin, but I can't make out a crack
  from here"), ask them politely to get closer, tilt the camera, or add light, and
  pin the frame with confirmed set to false. Pin it again with confirmed true once
  you can see it. Being honest about what is visible is more helpful to the claimant
  than agreeing, because the adjuster will look at the same photo.
- draw_incident_sketch: once you understand the scene, call this with a short
  description of the layout and what happened, written for an illustrator. The team
  draws a rough pen sketch into the notebook. When it returns, ask the claimant
  whether the sketch looks right. If they correct it, call it again with the fix.
  Call it in the same turn you first learn where it happened and what happened,
  alongside sync_claim_packet; do not wait for every detail or for the claimant to
  ask. A rough first sketch that gets corrected is better than a late one.

Safety first: if the claimant mentions injury, unsafe housing, or immediate danger,
tell them to contact emergency services if anyone is in danger, say that a human
representative will take over, and call sync_claim_packet so the team escalates.

Stay with the claimant. Talk about what they are talking about; when the camera is
on, the conversation is about what is on camera until you both move on. While a
camera view is still unconfirmed, your next question is about getting a better view
(closer, more light, a different angle), not about the packet. Double check the
details that matter (what is visible, dates, amounts, who was involved) and if
something does not add up, ask about it politely instead of writing it down. Never
announce that you are checking a list or the packet; just ask the next question.

Never promise coverage, payment, liability, benefits, or approval. Policy details
from lookup_policy describe what is on the policy, not what will be paid.
When the core facts and blocking items are collected, summarize the claim back in
two sentences and tell the claimant an adjuster will be in touch.
""".strip()


def _string_param(description: str) -> types.Schema:
    return types.Schema(type=types.Type.STRING, description=description)


def tool_declarations() -> list[types.Tool]:
    """Return the background tools the voice agent can call."""

    lookup = types.FunctionDeclaration(
        name="lookup_policy",
        description=(
            "Verify an insurance policy number against the carrier policy directory. "
            "Runs in the background. Returns policyholder name, policy line, status, "
            "deductibles, and coverages when found."
        ),
        behavior=types.Behavior.NON_BLOCKING,
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "policy_number": _string_param(
                    "Policy number exactly as the claimant said it, for example H0-44721 or AUTO 90210."
                )
            },
            required=["policy_number"],
        ),
    )
    sync = types.FunctionDeclaration(
        name="sync_claim_packet",
        description=(
            "Send the full claimant conversation and camera observations so far to the "
            "background claim team. Returns the routing decision, severity, blocking intake "
            "items, required documents, and the next best question to ask."
        ),
        behavior=types.Behavior.NON_BLOCKING,
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "reason": _string_param(
                    "One short phrase on why you are syncing now, for example 'new loss facts' or 'injury mentioned'."
                )
            },
        ),
    )
    pin_photo = types.FunctionDeclaration(
        name="pin_evidence_photo",
        description=(
            "Tape the current camera frame into the claim notebook as evidence, with your own "
            "observation as the caption and whether it confirms what the claimant described. "
            "Call it only after you have looked at the camera and can describe what is in the frame."
        ),
        behavior=types.Behavior.NON_BLOCKING,
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "observation": _string_param(
                    "One or two concrete sentences describing only what you can actually see in "
                    "the frame, for example 'Water line about two inches up the drywall next to "
                    "the stairs.' Never restate the claimant's description as your own."
                ),
                "claimant_description": _string_param(
                    "What the claimant says this shows, in their words, for example 'a crack in the wall'. "
                    "Leave empty if they did not describe it."
                ),
                "confirmed": types.Schema(
                    type=types.Type.BOOLEAN,
                    description=(
                        "True only if the frame clearly shows what the claimant described. False if you "
                        "cannot make it out, the frame is blurry or dark, or you see something different."
                    ),
                ),
                "evidence_type": _string_param(
                    "Short category such as 'damage', 'receipt', 'document', 'serial number', or 'scene'."
                ),
            },
            required=["observation", "confirmed"],
        ),
    )
    sketch = types.FunctionDeclaration(
        name="draw_incident_sketch",
        description=(
            "Ask the claim team to draw a rough hand-drawn pen sketch of the incident scene "
            "into the notebook. Runs in the background for several seconds. Call it once you "
            "know the location, the layout, and what happened. Call it again with corrections."
        ),
        behavior=types.Behavior.NON_BLOCKING,
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "scene_description": _string_param(
                    "Illustrator brief in plain words: the space or intersection, where things "
                    "are, what got damaged, and the direction of impact or water flow. Include "
                    "labels to write on the sketch. Fold in any corrections the claimant gave."
                )
            },
            required=["scene_description"],
        ),
    )
    return [types.Tool(function_declarations=[lookup, sync, pin_photo, sketch])]


def build_live_config() -> types.LiveConnectConfig:
    """Build the LiveConnectConfig for Gemini 3.8 Live with audio and camera input."""

    return types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=SYSTEM_INSTRUCTION,
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE_NAME)
            )
        ),
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
        tools=tool_declarations(),
    )


def scheduling_for(*, urgent: bool) -> types.FunctionResponseScheduling:
    """Pick how the model should react when a background tool result lands."""

    if urgent:
        return types.FunctionResponseScheduling.INTERRUPT
    return types.FunctionResponseScheduling.WHEN_IDLE


def sketch_prompt(scene_description: str) -> str:
    """Prompt for the image model so every sketch looks like the same adjuster's pen."""

    return (
        "A quick hand-drawn pen sketch on cream notebook paper, the kind an insurance "
        "adjuster draws in a field notebook. Black ink line drawing, loose confident "
        "strokes, small handwritten labels in the same ink, a light blue wash only where "
        "water is present and a light red wash only where impact damage is. Top-down or "
        "simple perspective, no photorealism, no shading gradients, no people. Write no names, "
        "dates, addresses, or claim numbers anywhere; the only text is short labels for the "
        "objects in the scene. Scene to draw: "
        f"{scene_description.strip()}"
    )


def summarize_workflow_for_voice(workflow: dict[str, Any]) -> dict[str, Any]:
    """Compact the ADK graph output into what the voice agent needs to hear."""

    packet = workflow["claim_intake_packet"]
    validation = workflow["field_validation"]
    fraud_gate = workflow["fraud_safety_gate"]
    classification = workflow["claim_classification"]
    checklist = workflow["document_checklist"]
    route = fraud_gate["final_routing_decision"]
    outstanding_docs = [
        item["item"] for item in checklist.get("items", []) if not item.get("already_provided")
    ]
    return {
        "routing_decision": route,
        "safety_escalation": route == "emergency_escalation",
        "claim_type": classification["claim_type"],
        "severity": classification["severity"],
        "open_items": validation.get("missing_fields", []),
        "open_documents": outstanding_docs[:3],
        "suggested_question_when_topic_is_closed": packet["claimant_next_message"],
        "how_to_use": (
            "Open items are a checklist for the packet. Finish the current topic first, then "
            "raise the item that fits the conversation. Do not read the list out."
        ),
        "handoff_summary": packet["adjuster_handoff_summary"],
        "guardrail": "Do not confirm coverage, payment, or liability.",
    }


def tool_headline(name: str, args: dict[str, Any], result: dict[str, Any] | None) -> str:
    """One-line description of a tool call for the operator activity feed."""

    if name == "lookup_policy":
        number = str(args.get("policy_number", "")).strip() or "unknown number"
        if result is None:
            return f"Checking policy {number}"
        if result.get("found"):
            return f"{result['policyholder_name']} - {result['policy_line']} ({result['status']})"
        return f"No match for {number}"
    if name == "sync_claim_packet":
        if result is None:
            return "Claim team writing up the notes"
        blockers = result.get("open_items", [])
        route = str(result.get("routing_decision", "")).replace("_", " ")
        if blockers:
            return f"{route}: {len(blockers)} open item{'s' if len(blockers) != 1 else ''} left"
        return f"{route}: no open items"
    if name == "pin_evidence_photo":
        if result is None:
            return "Looking at the camera frame"
        if result.get("pinned"):
            return "Pinned, confirmed on camera" if result.get("confirmed") else "Pinned, not confirmed on camera yet"
        return str(result.get("message", "No camera frame available"))
    if name == "draw_incident_sketch":
        if result is None:
            return "Sketching the scene"
        return "Sketch pinned to the notebook" if result.get("sketched") else str(result.get("message", "Sketch failed"))
    return name


__all__ = [
    "LIVE_MODEL_ID",
    "SKETCH_MODEL_ID",
    "SYSTEM_INSTRUCTION",
    "TOOL_NAMES",
    "build_live_config",
    "scheduling_for",
    "sketch_prompt",
    "summarize_workflow_for_voice",
    "tool_declarations",
    "tool_headline",
]
