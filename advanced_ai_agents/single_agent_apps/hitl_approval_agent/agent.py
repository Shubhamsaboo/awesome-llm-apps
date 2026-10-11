"""Human-in-the-Loop Approval Agent.

A refund agent that pauses for human approval when a request is large or
uncertain, using ADK's native tool confirmation, and backs every approved
action with a scoped, short-lived VAID credential.

Flow for a refund request:
1. `assess_refund_request` gathers facts and scores confidence from risk
   signals.
2. `issue_refund` applies policy. If the amount is above the auto-approve
   limit, or confidence is low, or no assessment exists, the tool pauses the
   run with `tool_context.request_confirmation`. The caller sees an
   `adk_request_confirmation` call and replies with approve/reject and a
   payload.
3. On resume the payload is validated (approver named, approved amount
   within the request) before anything executes.
4. A validated approval mints a VAID scoped to exactly this order and the
   `refund.issue` capability, held by the approver, with a short TTL. The
   refund only executes if that credential verifies: unexpired, correctly
   signed, not revoked, in scope, and holding the right capability. An
   approval revoked before this point fails closed, even though the human
   already said yes.
5. Every step is written to a hash-chained, tamper-evident audit log and to
   session state.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext
from google.genai import types
from pydantic import BaseModel, Field, ValidationError

from . import vaid_action

MODEL = os.getenv("ADK_MODEL", "gemini-2.5-flash")
AUTO_APPROVE_LIMIT = float(os.getenv("P06_AUTO_APPROVE_LIMIT", "100"))
MIN_CONFIDENCE = float(os.getenv("P06_MIN_CONFIDENCE", "0.8"))
AUDIT_LOG = Path(os.getenv("P06_AUDIT_LOG", Path.home() / ".hitl_approval_agent" / "audit.jsonl"))

log = logging.getLogger("hitl_approval_agent")


# ---------------------------------------------------------------- audit trail
def audit(event: str, tool_context: ToolContext | None = None, **data) -> dict:
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    prev = "0" * 64
    if AUDIT_LOG.exists():
        lines = AUDIT_LOG.read_text().strip().splitlines()
        if lines:
            prev = json.loads(lines[-1])["hash"]
    entry = {
        "ts": time.time(), "event": event, "prev_hash": prev,
        "user_id": getattr(tool_context, "user_id", None),
        "invocation_id": getattr(tool_context, "invocation_id", None),
        **data,
    }
    entry["hash"] = hashlib.sha256(json.dumps(entry, sort_keys=True, default=str).encode()).hexdigest()
    with AUDIT_LOG.open("a") as f:
        f.write(json.dumps(entry, default=str) + "\n")
    if tool_context is not None:
        trail = list(tool_context.state.get("audit_trail") or [])
        trail.append({"event": event, "hash": entry["hash"][:12], **{k: v for k, v in data.items() if k != "raw"}})
        tool_context.state["audit_trail"] = trail
    return entry


def verify_audit_chain(path: Path = AUDIT_LOG) -> bool:
    prev = "0" * 64
    for line in path.read_text().strip().splitlines():
        e = json.loads(line)
        h = e.pop("hash")
        if e["prev_hash"] != prev or hashlib.sha256(json.dumps(e, sort_keys=True, default=str).encode()).hexdigest() != h:
            return False
        prev = h
    return True


# ---------------------------------------------------------------- domain stubs
_ORDERS = {
    "ORD-1001": {"amount": 45.0, "customer_tenure_days": 900, "prior_refunds": 0, "delivered": True},
    "ORD-1002": {"amount": 480.0, "customer_tenure_days": 1200, "prior_refunds": 1, "delivered": True},
    "ORD-1003": {"amount": 60.0, "customer_tenure_days": 4, "prior_refunds": 3, "delivered": False},
}


class ApprovalPayload(BaseModel):
    approver: str = Field(min_length=2)
    approved_amount: float = Field(gt=0)
    note: str = ""


def assess_refund_request(order_id: str, tool_context: ToolContext) -> dict:
    """Gather order facts and score how confident we are the refund is legitimate.

    Args:
        order_id: e.g. ORD-1001.
    """
    order = _ORDERS.get(order_id)
    if not order:
        return {"error": f"unknown order {order_id}"}
    risk = []
    if order["customer_tenure_days"] < 30:
        risk.append("new_account")
    if order["prior_refunds"] >= 2:
        risk.append("frequent_refunds")
    if not order["delivered"]:
        risk.append("not_yet_delivered")
    confidence = round(max(0.0, 1.0 - 0.25 * len(risk)), 2)
    assessments = dict(tool_context.state.get("assessments") or {})
    assessments[order_id] = {"confidence": confidence, "risk_signals": risk, "order_amount": order["amount"]}
    tool_context.state["assessments"] = assessments
    audit("assessment", tool_context, order_id=order_id, confidence=confidence, risk_signals=risk)
    return {"order_id": order_id, **order, "confidence": confidence, "risk_signals": risk}


def issue_refund(order_id: str, amount: float, reason: str, tool_context: ToolContext) -> dict:
    """Issue a refund. Large or uncertain refunds pause for human approval, and
    an approved refund only executes once a scoped VAID credential for it
    verifies.

    Args:
        order_id: Order to refund.
        amount: Amount requested.
        reason: Customer-facing reason.
    """
    a = (tool_context.state.get("assessments") or {}).get(order_id)
    reasons = []
    if a is None:
        reasons.append("no assessment on file")
    else:
        if a["confidence"] < MIN_CONFIDENCE:
            reasons.append(f"low confidence {a['confidence']} ({', '.join(a['risk_signals'])})")
        if amount > a["order_amount"]:
            reasons.append("amount exceeds order value")
    if amount > AUTO_APPROVE_LIMIT:
        reasons.append(f"amount {amount} above auto-approve limit {AUTO_APPROVE_LIMIT}")

    confirmation = tool_context.tool_confirmation
    if reasons and confirmation is None:
        hint = f"Approve refund of {amount} for {order_id}? Reasons for review: {'; '.join(reasons)}."
        tool_context.request_confirmation(hint=hint, payload={"approver": "", "approved_amount": amount, "note": ""})
        audit("approval_requested", tool_context, order_id=order_id, amount=amount, reasons=reasons)
        return {"status": "pending_human_approval", "reasons": reasons}

    approved_amount = amount
    approver = "auto-policy"
    vaid_id = None
    if reasons:
        if not confirmation.confirmed:
            audit("approval_rejected", tool_context, order_id=order_id, amount=amount)
            return {"status": "rejected_by_human", "order_id": order_id}
        try:
            payload = ApprovalPayload.model_validate(confirmation.payload or {})
        except ValidationError as e:
            audit("approval_invalid", tool_context, order_id=order_id, errors=str(e))
            return {"status": "approval_invalid", "detail": "Approval payload failed validation; nothing was refunded.",
                    "errors": [err["msg"] for err in e.errors()]}
        if payload.approved_amount > amount:
            audit("approval_invalid", tool_context, order_id=order_id, errors="approved > requested")
            return {"status": "approval_invalid", "detail": "Approved amount exceeds the request."}
        approved_amount, approver = payload.approved_amount, payload.approver

        vaid = vaid_action.mint_for_refund(order_id, approver)
        vaid_id = vaid["vaid_id"]
        audit("vaid_minted", tool_context, order_id=order_id, vaid_id=vaid_id, approver=approver)
        result = vaid_action.verify_for_refund(vaid, order_id)
        if not result.ok:
            audit("vaid_verify_failed", tool_context, order_id=order_id, vaid_id=vaid_id, reason=result.reason)
            return {"status": "credential_denied", "detail": result.reason, "order_id": order_id}

    refund_id = "RF-" + hashlib.sha1(f"{order_id}:{approved_amount}".encode()).hexdigest()[:8].upper()
    audit("refund_issued", tool_context, order_id=order_id, requested=amount, refunded=approved_amount,
          approver=approver, reason=reason, refund_id=refund_id, vaid_id=vaid_id)
    return {"status": "refunded", "refund_id": refund_id, "amount": approved_amount, "approved_by": approver}


root_agent = LlmAgent(
    name="hitl_approval_agent",
    model=MODEL,
    description="Refund agent that pauses for human approval when uncertain or high value.",
    instruction=(
        "You handle refund requests. Always call assess_refund_request before issue_refund. "
        "If issue_refund returns pending_human_approval, tell the user it is awaiting review and "
        "why; do not retry. After a decision, report exactly what happened, including the "
        "approved amount if it differs from the request, and surface credential_denied clearly "
        "if the approval could not be honoured. If the user's request is ambiguous (which order, "
        "how much), ask them rather than guessing."
    ),
    tools=[assess_refund_request, issue_refund],
    generate_content_config=types.GenerateContentConfig(temperature=0),
)
