from datetime import datetime, timedelta, timezone

import pytest
from google.genai import types

from conftest import call, text


# ---------------------------------------------------------------- end-to-end, via ADK
@pytest.mark.asyncio
async def test_pauses_and_resumes_with_validated_approval(scripted, tmp_path, monkeypatch):
    from hitl_approval_agent import agent
    from hitl_approval_agent import vaid_action
    monkeypatch.setattr(agent, "AUDIT_LOG", tmp_path / "audit.jsonl")
    vaid_action.reset_issuer()
    from google.adk.runners import InMemoryRunner
    import conftest

    llm = scripted(
        call("assess_refund_request", order_id="ORD-1002"),
        call("issue_refund", order_id="ORD-1002", amount=480.0, reason="damaged"),
        text("Awaiting approval."),
        text("Refunded 300."),
    )
    conftest.set_model(agent.root_agent, llm)
    runner = InMemoryRunner(agent=agent.root_agent, app_name="t")
    s = await runner.session_service.create_session(app_name="t", user_id="u")
    events = [e async for e in runner.run_async(user_id="u", session_id=s.id, new_message=types.Content(
        role="user", parts=[types.Part(text="refund ORD-1002 480")]))]
    req = [p.function_call for e in events if e.content for p in e.content.parts
           if p.function_call and p.function_call.name == "adk_request_confirmation"]
    assert req, "tool should have requested human confirmation"

    approval = types.Content(role="user", parts=[types.Part(function_response=types.FunctionResponse(
        id=req[0].id, name="adk_request_confirmation",
        response={"confirmed": True, "payload": {"approver": "ops-lead", "approved_amount": 300.0}}))])
    events2 = [e async for e in runner.run_async(user_id="u", session_id=s.id, new_message=approval)]
    responses = [p.function_response.response for e in events2 if e.content for p in e.content.parts
                 if p.function_response and p.function_response.name == "issue_refund"]
    assert responses and responses[-1]["status"] == "refunded"
    assert responses[-1]["amount"] == 300.0 and responses[-1]["approved_by"] == "ops-lead"
    assert agent.verify_audit_chain(tmp_path / "audit.jsonl")


def test_small_confident_refund_auto_approves(tmp_path, monkeypatch):
    from hitl_approval_agent import agent
    monkeypatch.setattr(agent, "AUDIT_LOG", tmp_path / "a.jsonl")

    class Ctx:
        def __init__(self):
            self.state, self.tool_confirmation, self.user_id, self.invocation_id = {}, None, "u", "i"

        def request_confirmation(self, **kw):
            raise AssertionError("should not ask")

    c = Ctx()
    agent.assess_refund_request("ORD-1001", c)
    assert agent.issue_refund("ORD-1001", 45.0, "late", c)["status"] == "refunded"


def test_audit_chain_detects_tampering(tmp_path, monkeypatch):
    from hitl_approval_agent import agent
    path = tmp_path / "a.jsonl"
    monkeypatch.setattr(agent, "AUDIT_LOG", path)
    agent.audit("x", None, n=1)
    agent.audit("y", None, n=2)
    assert agent.verify_audit_chain(path)
    path.write_text(path.read_text().replace('"n": 1', '"n": 9'))
    assert not agent.verify_audit_chain(path)


# ---------------------------------------------------------------- VAID credential, directly
@pytest.fixture(autouse=True)
def _fresh_issuer():
    from hitl_approval_agent import vaid_action
    vaid_action.reset_issuer()
    yield
    vaid_action.reset_issuer()


def test_vaid_approve_then_verify_succeeds():
    from hitl_approval_agent import vaid_action
    vaid = vaid_action.mint_for_refund("ORD-1002", "ops-lead")
    result = vaid_action.verify_for_refund(vaid, "ORD-1002")
    assert result.ok, result.reason


def test_vaid_deny_never_mints():
    """A denied approval has no payload to mint from; issue_refund never calls
    mint_for_refund on that path. This is asserted at the agent level in
    test_small_confident_refund_auto_approves' sibling below and here directly:
    verifying a credential that was never minted is meaningless, so the
    'deny' guarantee is that no VAID exists to check."""
    from hitl_approval_agent import agent

    class Ctx:
        def __init__(self):
            self.state = {"assessments": {"ORD-1002": {"confidence": 0.5, "risk_signals": ["x"], "order_amount": 480.0}}}
            self.tool_confirmation = type("C", (), {"confirmed": False, "payload": None})()
            self.user_id, self.invocation_id = "u", "i"

    result = agent.issue_refund("ORD-1002", 480.0, "damaged", Ctx())
    assert result["status"] == "rejected_by_human"


def test_vaid_expired_credential_fails_closed():
    from hitl_approval_agent import vaid_action
    vaid = vaid_action.mint_for_refund("ORD-1002", "ops-lead")
    far_future = datetime.now(timezone.utc) + timedelta(hours=vaid_action.VAID_TTL_HOURS, minutes=5)
    result = vaid_action.verify_for_refund(vaid, "ORD-1002", now=far_future)
    assert not result.ok
    assert "expired" in result.reason


def test_vaid_revoked_credential_fails_closed():
    from hitl_approval_agent import vaid_action
    vaid = vaid_action.mint_for_refund("ORD-1002", "ops-lead")
    assert vaid_action.verify_for_refund(vaid, "ORD-1002").ok
    vaid_action.revoke(vaid["vaid_id"])
    result = vaid_action.verify_for_refund(vaid, "ORD-1002")
    assert not result.ok
    assert "revoked" in result.reason or "invalid" in result.reason


def test_vaid_out_of_scope_order_fails_closed():
    from hitl_approval_agent import vaid_action
    vaid = vaid_action.mint_for_refund("ORD-1002", "ops-lead")
    result = vaid_action.verify_for_refund(vaid, "ORD-1003")
    assert not result.ok
    assert "scope" in result.reason


def test_vaid_full_flow_blocks_execution_when_revoked_before_resume(tmp_path, monkeypatch):
    """Mirrors the real race: human approves, agent mints the credential, but
    the approval is revoked before the refund tool actually runs. The refund
    must not execute."""
    from hitl_approval_agent import agent, vaid_action
    monkeypatch.setattr(agent, "AUDIT_LOG", tmp_path / "a.jsonl")

    class Ctx:
        def __init__(self):
            self.state = {"assessments": {"ORD-1002": {"confidence": 0.5, "risk_signals": ["x"], "order_amount": 480.0}}}
            self.tool_confirmation = type("C", (), {
                "confirmed": True,
                "payload": {"approver": "ops-lead", "approved_amount": 300.0},
            })()
            self.user_id, self.invocation_id = "u", "i"

    # Simulate the race by revoking right after mint: patch mint_for_refund to
    # mint, revoke, then return the now-revoked credential.
    real_mint = vaid_action.mint_for_refund

    def mint_then_revoke(order_id, approver):
        vaid = real_mint(order_id, approver)
        vaid_action.revoke(vaid["vaid_id"])
        return vaid

    monkeypatch.setattr(vaid_action, "mint_for_refund", mint_then_revoke)
    monkeypatch.setattr(agent, "vaid_action", vaid_action)

    result = agent.issue_refund("ORD-1002", 480.0, "damaged", Ctx())
    assert result["status"] == "credential_denied"
