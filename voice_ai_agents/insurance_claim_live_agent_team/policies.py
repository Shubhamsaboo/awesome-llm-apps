"""Deterministic policy, evidence, routing, and packet builders."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

try:
    from .schemas import (
        ClaimClassification,
        ClaimIntakePacket,
        ClaimNarrative,
        CoverageEvidenceDecision,
        DocumentChecklist,
        DocumentChecklistItem,
        EvidenceRuleFinding,
        FieldValidation,
        FraudSafetyGate,
        FraudSafetySignal,
    )
except ImportError:
    from schemas import (
        ClaimClassification,
        ClaimIntakePacket,
        ClaimNarrative,
        CoverageEvidenceDecision,
        DocumentChecklist,
        DocumentChecklistItem,
        EvidenceRuleFinding,
        FieldValidation,
        FraudSafetyGate,
        FraudSafetySignal,
    )


TYPE_REQUIRED_DOCS: dict[str, list[tuple[str, str]]] = {
    "home_water_damage": [
        ("Photos or video of damaged areas before cleanup", "Documents the loss condition."),
        ("Mitigation or drying invoice", "Shows steps taken to prevent additional damage."),
        ("Repair estimate or contractor assessment", "Supports the estimated repair cost."),
        ("Receipts for damaged personal property", "Supports contents reimbursement."),
    ],
    "auto_collision": [
        ("Photos of vehicles and scene", "Documents impact location and visible damage."),
        ("Police report or incident exchange form", "Confirms crash facts and involved parties."),
        ("Repair estimate or tow/storage invoice", "Supports vehicle damage costs."),
        ("Medical documentation for any injuries", "Supports injury-related escalation and benefits."),
        ("Other driver and witness information", "Helps liability review."),
    ],
    "theft_property_loss": [
        ("Police report number or theft report", "Most theft claims require a filed report."),
        ("Receipts, serial numbers, or ownership proof", "Supports ownership and value."),
        ("Photos of the item or packaging if available", "Helps item identification."),
        ("Location timeline and access details", "Helps verify circumstances of loss."),
    ],
    "health_medical_reimbursement": [
        ("Itemized provider bill", "Shows services, dates, and charged amounts."),
        ("Explanation of benefits or denial notice", "Shows what was paid or denied."),
        ("Proof of payment", "Supports reimbursement amount."),
        ("Provider name and diagnosis or treatment summary", "Supports eligibility review."),
    ],
    "travel_delay_cancellation": [
        ("Carrier cancellation or delay notice", "Confirms the covered travel disruption."),
        ("Original itinerary and booking confirmation", "Shows trip dates and route."),
        ("Receipts for prepaid nonrefundable expenses", "Supports claimed loss amount."),
        ("Refund, voucher, or credit documentation", "Prevents duplicate recovery."),
        ("Weather, emergency, or event documentation if available", "Supports cause of disruption."),
    ],
    "other": [
        ("Photos or available proof of loss", "Documents what happened."),
        ("Receipts, estimates, or invoices", "Supports the claimed amount."),
        ("Any third-party report or confirmation", "Helps verify loss facts."),
    ],
}

BLOCKING_FIELD_QUESTIONS = {
    "policyholder_name": "What is your full name as it appears on the policy?",
    "policy_number": "What is the policy number, if you have it available?",
    "contact_method": "What is the best phone number or email for the adjuster to reach you?",
    "date_of_loss": "When did the loss happen?",
    "loss_location": "Where did the loss happen?",
    "loss_description": "Can you briefly describe what happened?",
}


def _as_model(model_type, value):
    if isinstance(value, model_type):
        return value
    if value is None:
        return model_type()
    if isinstance(value, str):
        return model_type.model_validate_json(value)
    return model_type.model_validate(value)


def _blank(value: Any) -> bool:
    text = str(value or "").strip().lower()
    return text in {"", "unknown", "not specified", "unspecified", "n/a", "none", "not provided"}


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = item.strip()
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            result.append(normalized)
    return result


def _all_evidence_text(claim: ClaimNarrative) -> str:
    fields = [
        claim.loss_description,
        claim.raw_narrative_summary,
        " ".join(claim.evidence_available),
        " ".join(claim.documents_mentioned),
    ]
    return "\n".join(fields).lower()


def _has_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _without_negated_safety_mentions(text: str) -> str:
    """Remove phrases like "no injuries" before positive safety regex checks."""

    negated_patterns = [
        r"\b(?:no|not|none|without|denies|denied)\s+(?:one\s+)?(?:was\s+)?(?:injur\w*|hurt|pain|medical attention|ambulance|hospital|unsafe|hazard\w*|danger)\b",
        r"\b(?:injur\w*|hurt|pain|medical attention|ambulance|hospital|unsafe|hazard\w*|danger)\s+(?:was|were|is|are)?\s*(?:reported\s+)?(?:no|none|not reported|denied)\b",
    ]
    cleaned = text
    for pattern in negated_patterns:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
    return cleaned


def _positive_safety_concerns(claim: ClaimNarrative) -> list[str]:
    return [item for item in claim.injuries_or_safety_concerns if _has_positive_safety_language(item)]


def _has_positive_safety_language(text: str) -> bool:
    cleaned = _without_negated_safety_mentions(text)
    return _has_any(
        cleaned,
        [r"\binjur", r"\bhurt\b", r"\bneck pain\b", r"\bhospital\b", r"\burgent care\b", r"\bambulance\b"],
    )


def _document_provided(document: str, claim: ClaimNarrative) -> bool:
    evidence = _all_evidence_text(claim)
    doc = document.lower()
    keyword_groups = [
        ["photo", "picture", "video"],
        ["police", "report number", "incident report"],
        ["receipt", "invoice", "proof of payment", "credit card"],
        ["estimate", "contractor", "repair"],
        ["medical", "urgent care", "hospital", "provider", "bill"],
        ["airline", "carrier", "cancellation", "delay notice"],
        ["itinerary", "booking", "confirmation"],
        ["serial", "ownership", "purchase"],
        ["tow", "storage"],
    ]
    for keywords in keyword_groups:
        if any(keyword in doc for keyword in keywords):
            return any(keyword in evidence for keyword in keywords)
    return any(word in evidence for word in doc.split()[:3])


def _parse_date(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None

    cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", text, flags=re.IGNORECASE)
    candidates = [cleaned[:10], cleaned]
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m-%d-%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%B %d %Y",
        "%b %d %Y",
    ]
    for candidate in candidates:
        for fmt in formats:
            try:
                return datetime.strptime(candidate, fmt)
            except ValueError:
                continue
    return None


def _next_claimant_message(
    route: str,
    missing: list[str],
    required_documents: list[str],
) -> str:
    if route == "emergency_escalation":
        return (
            "Your claim mentions injury, safety, or habitability concerns. A human representative "
            "should review this immediately. If anyone is in danger, contact local emergency services first."
        )

    for field_name in missing:
        if field_name in BLOCKING_FIELD_QUESTIONS:
            return BLOCKING_FIELD_QUESTIONS[field_name]

    if missing:
        return f"Can you clarify this missing detail so the adjuster can process the claim smoothly: {missing[0]}?"

    if required_documents:
        return f"Do you have this document or evidence available now: {required_documents[0]}?"

    if route == "special_investigation":
        return (
            "A human reviewer should look at this file, but the core intake packet is started. "
            "Please keep originals of any receipts, reports, photos, or messages related to the loss."
        )

    return (
        "Your intake packet has the core information needed for adjuster assignment. Keep copies of "
        "all receipts, photos, reports, and communications related to the loss."
    )


def validate_required_claim_fields(claim_value: Any) -> dict[str, Any]:
    """Validate minimum intake facts before coverage and evidence rules run."""

    claim = _as_model(ClaimNarrative, claim_value)
    missing: list[str] = []
    warnings: list[str] = []

    required_fields = {
        "policyholder_name": claim.policyholder_name,
        "policy_number": claim.policy_number,
        "contact_method": claim.contact_method,
        "date_of_loss": claim.date_of_loss,
        "loss_location": claim.loss_location,
        "loss_description": claim.loss_description,
    }
    for field_name, value in required_fields.items():
        if _blank(value):
            missing.append(field_name)

    if claim.estimated_loss_usd is None:
        warnings.append("Estimated loss amount was not supplied.")

    missing.extend(claim.missing_or_uncertain_facts)
    missing = _dedupe(missing)

    validation = FieldValidation(
        intake_status="missing_info" if missing else "valid",
        missing_fields=missing,
        warnings=_dedupe(warnings),
        ready_for_policy_review=not missing,
    )
    return validation.model_dump(exclude_none=True)


def apply_coverage_and_evidence_rules(
    claim_value: Any,
    validation_value: Any,
    classification_value: Any,
) -> dict[str, Any]:
    """Apply deterministic coverage, evidence, and first-pass routing rules."""

    claim = _as_model(ClaimNarrative, claim_value)
    validation = _as_model(FieldValidation, validation_value)
    classification = _as_model(ClaimClassification, classification_value)

    findings: list[EvidenceRuleFinding] = []
    coverage_notes: list[str] = []
    required_docs: list[str] = []
    evidence_text = _all_evidence_text(claim)

    def add(
        rule_id: str,
        severity: str,
        message: str,
        required_action: str,
        document: str | None = None,
    ) -> None:
        findings.append(
            EvidenceRuleFinding(
                rule_id=rule_id,
                severity=severity,
                message=message,
                required_action=required_action,
                document=document,
            )
        )
        if document:
            required_docs.append(document)

    if validation.missing_fields:
        add(
            "INTAKE-001",
            "medium",
            "Required intake facts are missing before the claim can be fully assigned.",
            "collect_info",
        )

    for document, reason in TYPE_REQUIRED_DOCS.get(classification.claim_type, TYPE_REQUIRED_DOCS["other"]):
        if not _document_provided(document, claim):
            add(
                "DOC-001",
                "medium",
                f"Missing or unconfirmed document: {document}. {reason}",
                "collect_document",
                document,
            )

    if claim.estimated_loss_usd is not None and claim.estimated_loss_usd >= 25000:
        add(
            "LOSS-001",
            "high",
            "Estimated loss is high enough to require prompt human adjuster review.",
            "adjuster_review",
        )

    if classification.claim_type == "home_water_damage":
        coverage_notes.extend(
            [
                "Water damage review usually turns on source of water, suddenness, mitigation, exclusions, and whether flood coverage is separate.",
                "Do not promise coverage until policy forms, endorsements, cause of loss, and mitigation facts are reviewed.",
            ]
        )
        if _has_any(evidence_text, [r"\bunsafe\b", r"\belectrical\b", r"\bsewage\b", r"\bmold\b", r"\bno place to live\b"]):
            add(
                "SAFE-001",
                "urgent",
                "Unsafe living condition or potential health hazard was mentioned.",
                "emergency_escalation",
            )

    elif classification.claim_type == "auto_collision":
        coverage_notes.extend(
            [
                "Auto collision review usually depends on liability facts, coverage type, deductibles, police report, photos, and damage estimate.",
                "Injury claims require immediate human handling and no medical coverage promises in the intake response.",
            ]
        )
        if _positive_safety_concerns(claim) or _has_positive_safety_language(evidence_text):
            add("SAFE-002", "urgent", "Injury or medical attention was mentioned.", "emergency_escalation")

    elif classification.claim_type == "theft_property_loss":
        coverage_notes.extend(
            [
                "Theft/property loss review usually requires proof of ownership, loss location, access details, and a police or incident report.",
                "High-value electronics or jewelry may have sublimits or scheduled-property requirements.",
            ]
        )
        if not _has_any(evidence_text, [r"\bpolice\b", r"\breport number\b", r"\bcase number\b"]):
            add(
                "THEFT-001",
                "medium",
                "Theft claim lacks a police or incident report.",
                "collect_document",
                "Police report number or theft report",
            )

    elif classification.claim_type == "health_medical_reimbursement":
        coverage_notes.extend(
            [
                "Educational/demo note: medical reimbursement review depends on plan terms, eligibility, dates of service, itemized bills, EOBs, and proof of payment.",
                "This app does not provide medical, benefits, or coverage advice.",
            ]
        )

    elif classification.claim_type == "travel_delay_cancellation":
        coverage_notes.extend(
            [
                "Travel claim review usually depends on covered reason, carrier confirmation, trip dates, nonrefundable amounts, and refunds or credits received.",
                "Weather-related disruption may require carrier notices and documentation of unused prepaid expenses.",
            ]
        )

    else:
        coverage_notes.append(
            "Claim type is unclear; route for human triage after collecting minimum loss facts and proof of loss."
        )

    if any(f.required_action == "emergency_escalation" for f in findings):
        route = "emergency_escalation"
    elif any(f.required_action == "siu_review" for f in findings):
        route = "special_investigation"
    elif validation.missing_fields or any(f.required_action == "collect_document" for f in findings):
        route = "needs_docs"
    else:
        route = "ready_for_adjuster"

    decision = CoverageEvidenceDecision(
        routing_decision=route,
        provisional_coverage_considerations=_dedupe(coverage_notes),
        required_documents=_dedupe(required_docs),
        findings=findings,
        audit_trail=[
            "Validated minimum claim intake fields.",
            f"Classified claim as {classification.claim_type} with {classification.severity} severity.",
            "Applied deterministic evidence, document, high-loss, injury, and safety routing gates.",
            f"Initial route selected: {route}.",
        ],
    )
    return decision.model_dump(exclude_none=True)


def generate_document_checklist(
    claim_value: Any,
    classification_value: Any,
    evidence_decision_value: Any,
) -> dict[str, Any]:
    """Generate a claimant-facing checklist from deterministic document rules."""

    claim = _as_model(ClaimNarrative, claim_value)
    classification = _as_model(ClaimClassification, classification_value)
    evidence_decision = _as_model(CoverageEvidenceDecision, evidence_decision_value)
    required = set(evidence_decision.required_documents)

    items: list[DocumentChecklistItem] = []
    for document, reason in TYPE_REQUIRED_DOCS.get(classification.claim_type, TYPE_REQUIRED_DOCS["other"]):
        provided = _document_provided(document, claim)
        priority = "required" if document in required else "recommended"
        items.append(
            DocumentChecklistItem(
                item=document,
                reason=reason,
                priority=priority,
                already_provided=provided,
            )
        )

    if classification.claim_type == "auto_collision" and _positive_safety_concerns(claim):
        items.append(
            DocumentChecklistItem(
                item="Names of injured people and treatment locations",
                reason="Supports urgent injury claim assignment.",
                priority="required",
                already_provided=_has_any(_all_evidence_text(claim), [r"\burgent care\b", r"\bhospital\b"]),
            )
        )

    checklist = DocumentChecklist(
        items=items,
        claimant_tip=(
            "Upload clear copies when available. If a document is not available yet, explain why "
            "and provide the expected date."
        ),
    )
    return checklist.model_dump(exclude_none=True)


def fraud_signal_and_safety_gate(
    claim_value: Any,
    validation_value: Any,
    classification_value: Any,
    evidence_decision_value: Any,
) -> dict[str, Any]:
    """Apply deterministic SIU, fraud-pattern, timing, and safety gates."""

    claim = _as_model(ClaimNarrative, claim_value)
    validation = _as_model(FieldValidation, validation_value)
    classification = _as_model(ClaimClassification, classification_value)
    evidence_decision = _as_model(CoverageEvidenceDecision, evidence_decision_value)

    signals: list[FraudSafetySignal] = []
    evidence_text = _all_evidence_text(claim)

    def signal(
        signal_id: str,
        severity: str,
        message: str,
        route_to_siu: bool = False,
        route_to_emergency: bool = False,
    ) -> None:
        signals.append(
            FraudSafetySignal(
                signal_id=signal_id,
                severity=severity,
                message=message,
                route_to_siu=route_to_siu,
                route_to_emergency=route_to_emergency,
            )
        )

    loss_date = _parse_date(claim.date_of_loss)
    report_date = _parse_date(claim.reported_date)

    if loss_date and report_date and report_date < loss_date:
        signal(
            "TIMING-001",
            "high",
            "Reported date appears to be before the loss date.",
            route_to_siu=True,
        )

    if loss_date and report_date and (report_date - loss_date).days > 90:
        signal(
            "TIMING-002",
            "medium",
            "Claim appears to be reported more than 90 days after the loss.",
            route_to_siu=True,
        )

    if _has_any(evidence_text, [r"\bnot sure\b", r"\bdon'?t remember\b", r"\bmaybe\b", r"\bexact date\b"]):
        signal(
            "FACTS-001",
            "medium",
            "Narrative contains uncertain or vague key facts that need follow-up.",
            route_to_siu=False,
        )

    if (
        claim.estimated_loss_usd is not None
        and claim.estimated_loss_usd >= 10000
        and not claim.evidence_available
        and not claim.documents_mentioned
    ):
        signal(
            "EVID-001",
            "high",
            "High estimated loss was submitted without supporting evidence.",
            route_to_siu=True,
        )

    if classification.claim_type == "theft_property_loss" and _has_any(
        evidence_text,
        [r"\bno police\b", r"\bhave not filed\b", r"\bdidn'?t file\b"],
    ):
        signal(
            "THEFT-002",
            "medium",
            "Theft claim states that no police report has been filed yet.",
            route_to_siu=False,
        )

    if evidence_decision.routing_decision == "emergency_escalation" or any(
        f.required_action == "emergency_escalation" for f in evidence_decision.findings
    ):
        signal(
            "SAFETY-001",
            "urgent",
            "Safety, injury, or habitability issue requires immediate human review.",
            route_to_emergency=True,
        )

    if any(item in validation.missing_fields for item in ["date_of_loss", "loss_location", "loss_description"]):
        signal(
            "INTAKE-002",
            "medium",
            "Core loss facts are missing, so routing should remain follow-up oriented.",
        )

    if any(s.route_to_emergency for s in signals):
        final_route = "emergency_escalation"
    elif any(s.route_to_siu for s in signals):
        final_route = "special_investigation"
    else:
        final_route = evidence_decision.routing_decision

    gate = FraudSafetyGate(
        final_routing_decision=final_route,
        signals=signals,
        audit_trail=evidence_decision.audit_trail
        + [
            "Applied deterministic fraud, suspicious timing, vague facts, and safety gates.",
            f"Final route selected: {final_route}.",
        ],
    )
    return gate.model_dump(exclude_none=True)


def build_claim_intake_packet(
    claim_value: Any,
    validation_value: Any,
    classification_value: Any,
    evidence_decision_value: Any,
    checklist_value: Any,
    fraud_gate_value: Any,
) -> dict[str, Any]:
    """Build the final Markdown claim intake packet for ADK Web."""

    claim = _as_model(ClaimNarrative, claim_value)
    validation = _as_model(FieldValidation, validation_value)
    classification = _as_model(ClaimClassification, classification_value)
    evidence_decision = _as_model(CoverageEvidenceDecision, evidence_decision_value)
    checklist = _as_model(DocumentChecklist, checklist_value)
    fraud_gate = _as_model(FraudSafetyGate, fraud_gate_value)

    missing = _dedupe(validation.missing_fields)
    route = fraud_gate.final_routing_decision
    route_label = route.replace("_", " ").title()

    checklist_lines = []
    for item in checklist.items:
        status = "already provided" if item.already_provided else item.priority
        checklist_lines.append(f"- [{status}] **{item.item}** - {item.reason}")

    if not checklist_lines:
        checklist_lines.append("- No additional documents identified by current rules.")

    missing_lines = [f"- {field}" for field in missing] or ["- No required intake fields are missing."]
    coverage_lines = [
        f"- {note}" for note in evidence_decision.provisional_coverage_considerations
    ] or ["- Coverage review requires policy forms, endorsements, loss facts, and adjuster analysis."]

    signal_lines = [
        f"- `{signal.signal_id}` [{signal.severity}] {signal.message}"
        for signal in fraud_gate.signals
    ] or ["- No deterministic fraud or emergency signal was triggered."]

    finding_lines = [
        f"- `{finding.rule_id}` [{finding.severity}] {finding.message}"
        for finding in evidence_decision.findings
    ] or ["- No deterministic evidence findings were generated."]

    handoff = (
        f"{claim.policyholder_name or 'Unknown claimant'} reported a "
        f"{classification.claim_type.replace('_', ' ')} loss at {claim.loss_location or 'an unknown location'} "
        f"on {claim.date_of_loss or 'an unknown date'}. "
        f"Summary: {claim.raw_narrative_summary or claim.loss_description}. "
        f"Estimated loss: {claim.estimated_loss_usd if claim.estimated_loss_usd is not None else 'not supplied'}."
    )

    claimant_next = _next_claimant_message(route, missing, evidence_decision.required_documents)

    audit_lines = [f"{idx}. {entry}" for idx, entry in enumerate(fraud_gate.audit_trail, start=1)]

    markdown = f"""# Insurance Claim Intake Packet

**Claim type:** {classification.claim_type.replace("_", " ").title()}  
**Intake status:** {validation.intake_status.replace("_", " ").title()}  
**Severity:** {classification.severity.title()}  
**Routing decision:** {route_label}

## Missing Information
{chr(10).join(missing_lines)}

## Required Documents Checklist
{chr(10).join(checklist_lines)}

## Coverage Considerations and Disclaimer
{chr(10).join(coverage_lines)}

This is an intake triage packet for demo and educational use. It does not confirm coverage, benefits, liability, payment, or legal rights. A licensed adjuster or qualified human reviewer must evaluate the applicable policy, endorsements, exclusions, deductibles, documentation, and governing law.

## Adjuster Handoff Summary
{handoff}

## Claimant-Friendly Next Message
{claimant_next}

## Deterministic Findings
{chr(10).join(finding_lines)}

## Fraud, Timing, and Safety Signals
{chr(10).join(signal_lines)}

## Audit Trail
{chr(10).join(audit_lines)}
"""

    packet = ClaimIntakePacket(
        claim_type=classification.claim_type,
        intake_status=validation.intake_status,
        severity=classification.severity,
        routing_decision=route,
        missing_information=missing,
        required_documents=checklist.items,
        coverage_considerations=evidence_decision.provisional_coverage_considerations,
        adjuster_handoff_summary=handoff,
        claimant_next_message=claimant_next,
        audit_trail=fraud_gate.audit_trail,
        markdown=markdown,
    )
    return packet.model_dump(exclude_none=True)
