"""Scoped, short-lived VAID credentials for one approved action.

When a human approves a refund, we mint a VAID scoped to exactly that order
and capability, with a short TTL. The tool that performs the refund verifies
the credential (signature, expiry, revocation, scope, capability) before it
acts, so a credential approved for one thing cannot authorize another, and a
revoked approval cannot be used even if the agent still holds it.

Trust model note: this demo issuer is constructed with
`assuming_nothing_revoked()`, an in-memory revocation store that vouches
"nothing is revoked" until something is explicitly revoked through it. That
is the right choice for a single-process demo with no durable backend; it is
a named fail-open posture (see the vaid-mint README's "Trust model" section)
and a production deployment should inject a durable
`vaid_mint.revocation.RevocationBackend` instead.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone

from vaid_mint import ReferenceIssuer, has_capability, is_in_scope
from vaid_mint.document import is_expired_at

TRUST_DOMAIN = os.getenv("P06_VAID_TRUST_DOMAIN", "hitl-approval.demo")
AGENT_CLASS = "hitl-approval-agent"
AGENT_VERSION = "1.0"
VAID_TTL_HOURS = int(os.getenv("P06_VAID_TTL_HOURS", "1"))

_issuer: ReferenceIssuer | None = None


def get_issuer() -> ReferenceIssuer:
    """The process-wide demo issuer. Lazily built so tests can monkeypatch
    `VAID_TTL_HOURS` / `TRUST_DOMAIN` before first use."""
    global _issuer
    if _issuer is None:
        _issuer = ReferenceIssuer.ephemeral(VAID_TTL_HOURS, TRUST_DOMAIN).assuming_nothing_revoked()
    return _issuer


def reset_issuer() -> None:
    """Test-only: drop the cached issuer so a fresh one is built with new settings."""
    global _issuer
    _issuer = None


def resource_for_order(order_id: str) -> str:
    return f"refund/{order_id}"


CAPABILITY_ISSUE_REFUND = "refund.issue"


def mint_for_refund(order_id: str, approver: str) -> dict:
    """Mint a VAID scoped to refunding exactly this order, held by `approver`."""
    issuer = get_issuer()
    return issuer.issue_vaid_with_lineage(
        agent_class=AGENT_CLASS,
        version=AGENT_VERSION,
        tenant_id=approver,
        parent_vaid=None,
        scope_boundary=[resource_for_order(order_id)],
        capability_set=[CAPABILITY_ISSUE_REFUND],
    )


@dataclass
class VerifyResult:
    ok: bool
    reason: str = ""


def verify_for_refund(vaid: dict, order_id: str, *, now: datetime | None = None) -> VerifyResult:
    """Everything the acting tool must check before it refunds anything.

    Checked in this order so the caller can tell the failures apart: expiry
    first (no need to touch the revocation store for a credential that is
    already too old), then signature + revocation (via the issuer, which
    fails closed on an unreachable or absent revocation store), then scope
    and capability.
    """
    issuer = get_issuer()
    check_at = now or datetime.now(timezone.utc)
    if is_expired_at(vaid, check_at):
        return VerifyResult(False, "credential expired")
    if not issuer.verify_vaid(vaid):
        return VerifyResult(False, "credential invalid or revoked")
    resource = resource_for_order(order_id)
    if not is_in_scope(vaid, resource):
        return VerifyResult(False, f"credential not in scope for {resource}")
    if not has_capability(vaid, CAPABILITY_ISSUE_REFUND):
        return VerifyResult(False, "credential lacks refund.issue capability")
    return VerifyResult(True)


def revoke(vaid_id: str) -> None:
    get_issuer().revoke(vaid_id)
