"""ADK hybrid graph workflow for AI Insurance Claim Intake."""

from __future__ import annotations

import inspect
import json
import uuid
from typing import Any, AsyncGenerator, Callable

from google.adk.agents import BaseAgent, LlmAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from pydantic import BaseModel, ConfigDict
from typing_extensions import override

try:
    from .policies import (
        apply_coverage_and_evidence_rules,
        build_claim_intake_packet,
        fraud_signal_and_safety_gate,
        generate_document_checklist,
        validate_required_claim_fields,
    )
    from .schemas import (
        ClaimClassification,
        ClaimIntakePacket,
        ClaimNarrative,
        CoverageEvidenceDecision,
        DocumentChecklist,
        FieldValidation,
        FraudSafetyGate,
    )
except ImportError:
    from policies import (
        apply_coverage_and_evidence_rules,
        build_claim_intake_packet,
        fraud_signal_and_safety_gate,
        generate_document_checklist,
        validate_required_claim_fields,
    )
    from schemas import (
        ClaimClassification,
        ClaimIntakePacket,
        ClaimNarrative,
        CoverageEvidenceDecision,
        DocumentChecklist,
        FieldValidation,
        FraudSafetyGate,
    )


MODEL = "gemini-3.8-flash"
APP_NAME = "insurance_claim_live_agent_team"


async def _await_if_needed(value: Any) -> Any:
    return await value if inspect.isawaitable(value) else value


def _plain(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(exclude_none=True)
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("{") or text.startswith("["):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return value
    return value


def blank_claim() -> dict[str, Any]:
    return {
        "policyholder_name": "not specified",
        "policy_number": "not specified",
        "contact_method": "not specified",
        "date_of_loss": "not specified",
        "reported_date": "not specified",
        "loss_location": "not specified",
        "loss_description": "not specified",
        "estimated_loss_usd": None,
        "injuries_or_safety_concerns": [],
        "parties_involved": [],
        "evidence_available": [],
        "documents_mentioned": [],
        "missing_or_uncertain_facts": [],
        "raw_narrative_summary": "not specified",
        "assumptions": [],
    }


def initial_classification() -> dict[str, Any]:
    return {
        "claim_type": "other",
        "severity": "medium",
        "severity_rationale": "Waiting for claimant facts.",
        "likely_policy_line": "unknown",
        "loss_drivers": [],
        "claimant_needs": ["Provide initial loss facts."],
    }


def build_initial_workflow_state() -> dict[str, Any]:
    claim = blank_claim()
    classification = initial_classification()
    validation = validate_required_claim_fields(claim)
    coverage = apply_coverage_and_evidence_rules(claim, validation, classification)
    checklist = generate_document_checklist(claim, classification, coverage)
    fraud_gate = fraud_signal_and_safety_gate(claim, validation, classification, coverage)
    packet = build_claim_intake_packet(
        claim,
        validation,
        classification,
        coverage,
        checklist,
        fraud_gate,
    )
    return {
        "normalized_claim": claim,
        "field_validation": validation,
        "claim_classification": classification,
        "coverage_evidence_decision": coverage,
        "document_checklist": checklist,
        "fraud_safety_gate": fraud_gate,
        "claim_intake_packet": packet,
        "final_markdown": packet["markdown"],
    }


def _content(text: str) -> genai_types.Content:
    return genai_types.Content(role="model", parts=[genai_types.Part(text=text)])


def _state_event(author: str, text: str, updates: dict[str, Any]) -> Event:
    return Event(
        author=author,
        content=_content(text),
        actions=EventActions(state_delta=updates),
    )


class FunctionNode(BaseAgent):
    """Deterministic workflow node that reads and writes ADK session state."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    handler: Callable[[InvocationContext], dict[str, Any]]
    output_key: str
    summary: str

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        result = self.handler(ctx)
        ctx.session.state[self.output_key] = result
        yield _state_event(self.name, self.summary, {self.output_key: result})


class FinalPacketNode(FunctionNode):
    """Function node that returns the final packet Markdown as ADK Web output."""

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        result = self.handler(ctx)
        updates = {self.output_key: result, "final_markdown": result["markdown"]}
        ctx.session.state.update(updates)
        yield _state_event(self.name, result["markdown"], updates)


def _validate_claim_handler(ctx: InvocationContext) -> dict[str, Any]:
    return validate_required_claim_fields(ctx.session.state.get("normalized_claim"))


def _coverage_evidence_handler(ctx: InvocationContext) -> dict[str, Any]:
    return apply_coverage_and_evidence_rules(
        ctx.session.state.get("normalized_claim"),
        ctx.session.state.get("field_validation"),
        ctx.session.state.get("claim_classification"),
    )


def _document_checklist_handler(ctx: InvocationContext) -> dict[str, Any]:
    return generate_document_checklist(
        ctx.session.state.get("normalized_claim"),
        ctx.session.state.get("claim_classification"),
        ctx.session.state.get("coverage_evidence_decision"),
    )


def _fraud_safety_handler(ctx: InvocationContext) -> dict[str, Any]:
    return fraud_signal_and_safety_gate(
        ctx.session.state.get("normalized_claim"),
        ctx.session.state.get("field_validation"),
        ctx.session.state.get("claim_classification"),
        ctx.session.state.get("coverage_evidence_decision"),
    )


def _final_packet_handler(ctx: InvocationContext) -> dict[str, Any]:
    return build_claim_intake_packet(
        ctx.session.state.get("normalized_claim"),
        ctx.session.state.get("field_validation"),
        ctx.session.state.get("claim_classification"),
        ctx.session.state.get("coverage_evidence_decision"),
        ctx.session.state.get("document_checklist"),
        ctx.session.state.get("fraud_safety_gate"),
    )


def create_normalizer() -> LlmAgent:
    return LlmAgent(
        name="NormalizeClaimNarrative",
        model=MODEL,
        description="Normalizes messy insurance claim narratives into structured intake facts.",
        disallow_transfer_to_parent=True,
        disallow_transfer_to_peers=True,
        instruction="""
You are the intake specialist for an AI Insurance Claim Intake Agent.

Read the user's messy insurance claim narrative and produce a structured
ClaimNarrative. Preserve facts exactly when possible. Do not invent policy
numbers, contacts, dates, locations, evidence, or dollar amounts.

Extraction rules:
- policyholder_name: claimant or policyholder name, otherwise "not specified".
- policy_number: policy/member number, otherwise "not specified".
- contact_method: phone, email, mailing address, or preferred channel, otherwise "not specified".
- date_of_loss: date or date range of the loss, otherwise "not specified".
- reported_date: date the user says they are reporting the claim, otherwise "not specified".
- loss_location: address, city, intersection, provider, or travel route, otherwise "not specified".
- loss_description: concise factual description of what happened.
- estimated_loss_usd: numeric USD estimate only if supplied.
- injuries_or_safety_concerns: include injuries, urgent medical care, unsafe housing, electrical hazards, sewage, mold, or no place to live.
- evidence_available: photos, video, receipts, report numbers, estimates, bills, carrier notices, EOBs, proof of payment, serial numbers, or similar evidence already mentioned.
- documents_mentioned: specific documents mentioned whether available or missing.
- missing_or_uncertain_facts: key facts the narrative says are unknown, vague, or incomplete.

This is an intake normalization step only. Do not confirm coverage or payment.
""",
        output_schema=ClaimNarrative,
        output_key="normalized_claim",
    )


def create_classifier() -> LlmAgent:
    return LlmAgent(
        name="ClassifyClaimTypeAndSeverity",
        model=MODEL,
        description="Classifies claim type, severity, policy line, and claimant needs.",
        disallow_transfer_to_parent=True,
        disallow_transfer_to_peers=True,
        instruction="""
Classify this normalized claim for insurance intake routing.

Normalized claim:
{normalized_claim}

Validation:
{field_validation}

Supported claim types:
- home_water_damage
- auto_collision
- theft_property_loss
- health_medical_reimbursement
- travel_delay_cancellation
- other

Severity rubric:
- low: complete, low-dollar, no injury/safety issue, routine documentation.
- medium: missing documents or moderate complexity.
- high: high estimated loss, unclear liability, missing core facts, or specialized handling likely.
- urgent: injury, unsafe living condition, emergency medical/safety concern, or time-sensitive mitigation.

Return only the structured ClaimClassification. This is classification, not a
coverage decision.
""",
        output_schema=ClaimClassification,
        output_key="claim_classification",
    )


def create_workflow() -> SequentialAgent:
    return SequentialAgent(
        name="insurance_claim_live_agent_team",
        description="Hybrid voice-first agent team for insurance claim intake, evidence triage, and routing.",
        sub_agents=[
            create_normalizer(),
            FunctionNode(
                name="ValidateRequiredClaimFields",
                description="Deterministically validates required claim intake fields.",
                handler=_validate_claim_handler,
                output_key="field_validation",
                summary="Validated required claim intake fields.",
            ),
            create_classifier(),
            FunctionNode(
                name="ApplyCoverageAndEvidenceRules",
                description="Applies deterministic coverage, evidence, severity, and routing gates.",
                handler=_coverage_evidence_handler,
                output_key="coverage_evidence_decision",
                summary="Applied deterministic coverage and evidence rules.",
            ),
            FunctionNode(
                name="GenerateDocumentChecklist",
                description="Builds a claimant-facing document checklist from deterministic rules.",
                handler=_document_checklist_handler,
                output_key="document_checklist",
                summary="Generated required document checklist.",
            ),
            FunctionNode(
                name="FraudSignalAndSafetyGate",
                description="Applies deterministic fraud signal, suspicious timing, and safety gates.",
                handler=_fraud_safety_handler,
                output_key="fraud_safety_gate",
                summary="Applied fraud, timing, and safety routing gates.",
            ),
            FinalPacketNode(
                name="FinalClaimIntakePacket",
                description="Builds the final polished Markdown claim intake packet.",
                handler=_final_packet_handler,
                output_key="claim_intake_packet",
                summary="Built final claim intake packet.",
            ),
        ],
    )


root_agent = create_workflow()


async def run_claim_workflow(
    claimant_transcript: str,
    *,
    session_id: str | None = None,
    user_id: str = "live-ui",
) -> dict[str, Any]:
    """Run the ADK claim graph for the current claimant transcript snapshot."""

    transcript = str(claimant_transcript or "").strip()
    if not transcript:
        return build_initial_workflow_state()

    adk_session_id = f"claim-{session_id or uuid.uuid4().hex}"
    session_service = InMemorySessionService()
    await _await_if_needed(
        session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=adk_session_id,
        )
    )
    runner = Runner(
        app_name=APP_NAME,
        agent=root_agent,
        session_service=session_service,
    )
    message = genai_types.Content(
        role="user",
        parts=[
            genai_types.Part(
                text=(
                    "Use this full claimant transcript as the source of truth for "
                    "the insurance intake workflow. Do not invent missing facts.\n\n"
                    f"{transcript}"
                )
            )
        ],
    )

    event_count = 0
    async for _event in runner.run_async(
        user_id=user_id,
        session_id=adk_session_id,
        new_message=message,
    ):
        event_count += 1
    if event_count == 0:
        raise RuntimeError("ADK workflow completed without emitting any events.")

    session = await _await_if_needed(
        session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=adk_session_id,
        )
    )
    state = session.state
    claim = ClaimNarrative.model_validate(_plain(state.get("normalized_claim")))
    validation = FieldValidation.model_validate(_plain(state.get("field_validation")))
    classification = ClaimClassification.model_validate(_plain(state.get("claim_classification")))
    coverage = CoverageEvidenceDecision.model_validate(_plain(state.get("coverage_evidence_decision")))
    checklist = DocumentChecklist.model_validate(_plain(state.get("document_checklist")))
    fraud_gate = FraudSafetyGate.model_validate(_plain(state.get("fraud_safety_gate")))
    packet = ClaimIntakePacket.model_validate(_plain(state.get("claim_intake_packet")))
    return {
        "normalized_claim": claim.model_dump(exclude_none=True),
        "field_validation": validation.model_dump(exclude_none=True),
        "claim_classification": classification.model_dump(exclude_none=True),
        "coverage_evidence_decision": coverage.model_dump(exclude_none=True),
        "document_checklist": checklist.model_dump(exclude_none=True),
        "fraud_safety_gate": fraud_gate.model_dump(exclude_none=True),
        "claim_intake_packet": packet.model_dump(exclude_none=True),
        "final_markdown": packet.markdown,
    }


__all__ = [
    "APP_NAME",
    "MODEL",
    "blank_claim",
    "build_initial_workflow_state",
    "create_workflow",
    "run_claim_workflow",
    "root_agent",
]
