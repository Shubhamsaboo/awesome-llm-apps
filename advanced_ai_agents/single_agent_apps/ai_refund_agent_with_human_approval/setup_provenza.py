"""
Prepare Provenza for the refund agent, through its API, as an administrator:

  1. approve the five shop tools in the Tool Registry;
  2. enroll the agent: its keys are made here and only the public key goes
     to Provenza; it may call those five tools and nothing else;
  3. give it a policy:
       - a refund over $100 waits for a person's approval,
       - e-mail only to @example-shop.com,
       - never export the customer list.

    python setup_provenza.py          (again with --new for a fresh agent)

Run it before you sign in to the console in your browser: a second sign-in
of the same administrator waits until the open one lets it in. It signs out
when it is done.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import httpx
from provenza import Agent
from provenza.errors import ProvenzaConfigError

from agent import TOOLS

URL = os.environ.get("PROVENZA_URL", "http://localhost:8080").rstrip("/")
ORG = os.environ.get("PROVENZA_ORG", "provenza")
EMAIL = os.environ.get("PROVENZA_ADMIN_EMAIL", "admin@example.com")
PASSWORD = os.environ.get("PROVENZA_ADMIN_PASSWORD", "provenza-try-local")   # docker-compose.try.yml
HERE = Path(__file__).resolve().parent
STATE = HERE / ".provenza"
IDENTITY = STATE / "refund-agent.json"
POLICY_NAME = "Refund agent guardrails"

POLICY = {
    "argument_rules": [
        {"tool": "shop.issue_refund", "arg": "amount", "op": "max", "value": 100, "effect": "require_approval"},
        {"tool": "shop.send_email", "arg": "to", "op": "domain_in", "value": ["example-shop.com"], "effect": "deny"},
    ],
    "deny_tools": ["shop.export_customers"],
}


def fail(msg: str) -> None:
    sys.exit(f"\n  {msg}\n")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--new", action="store_true", help="enroll a new agent (after the old one was quarantined)")
    args = p.parse_args()

    api = httpx.Client(base_url=f"{URL}/api/v1", timeout=20)
    try:
        r = api.post("/auth/login", json={"org_slug": ORG, "email": EMAIL, "password": PASSWORD})
    except httpx.HTTPError as exc:
        fail(f"Provenza is not reachable at {URL} ({exc}). Is docker-compose.try.yml up?")
    if r.status_code != 200:
        fail(f"Sign-in failed ({r.status_code}): {r.text[:200]}")
    api.headers["Authorization"] = f"Bearer {r.json()['access_token']}"
    try:
        configure(api, args.new)
    finally:
        api.post("/auth/logout")


def configure(api: httpx.Client, new: bool) -> None:
    def ok(r: httpx.Response) -> dict:
        if r.status_code == 403 and "session_blocked" in r.text:
            fail("You are signed in to the console in a browser: sign out there (or wait until that sign-in "
                 "ends) and run this again.")
        if r.status_code >= 400:
            fail(f"{r.request.method} {r.request.url.path}: {r.status_code} {r.text[:300]}")
        return r.json() if r.content else {}

    names = [t["name"] for t in TOOLS]

    # 1. the tools, approved in the Tool Registry
    entries = {e["pattern"]: e for e in ok(api.get("/tool-registry/"))}
    for name in names:
        e = entries.get(name)
        if e is None:
            ok(api.post("/tool-registry/", json={"pattern": name, "kind": "tool", "status": "approved",
                                                 "display_name": name, "notes": "governed refund agent example"}))
        elif e["status"] != "approved":
            ok(api.post(f"/tool-registry/{e['id']}/approve", json={}))
    print(f"  ✓ {len(names)} tools approved in the Tool Registry")

    # 2. the agent: enrolled once, its keys made on this machine
    STATE.mkdir(exist_ok=True)
    if new and IDENTITY.exists():
        IDENTITY.unlink()
    if IDENTITY.exists():
        try:
            agent = Agent("refund-agent", server_url=URL, identity_path=str(IDENTITY))
        except ProvenzaConfigError as exc:
            fail(f"{exc}. Run with --new to enroll a new agent here.")
        status = ok(api.get(f"/agents/{agent.agent_id}")).get("status")
        if status != "active":
            fail(f"The agent #{agent.agent_id} is {status}. Release it in the console "
                 "(Rules → Behavior Monitor), or run with --new.")
        print(f"  ✓ agent #{agent.agent_id} already enrolled ({agent.fingerprint})")
    else:
        enr = ok(api.post("/agent-enrollment/tokens", json={
            "name": "refund-agent", "description": "Example Shop's support agent (governed refund agent example)",
            "agent_type": "custom", "allowed_tools": names, "ttl_hours": 1}))
        agent = Agent("refund-agent", server_url=URL, enrollment_token=enr["token"], identity_path=str(IDENTITY))
        print(f"  ✓ agent #{agent.agent_id} enrolled; its keys stay in {IDENTITY.relative_to(HERE)}")

    # 3. its policy
    policies = ok(api.get("/agents/policies/", params={"limit": 200})).get("items", [])
    mine = [x for x in policies if x.get("agent_id") == agent.agent_id and x.get("name") == POLICY_NAME]
    if not mine:
        ok(api.post("/agents/policies/", json={"name": POLICY_NAME, "agent_id": agent.agent_id, "rules": POLICY}))
    print("  ✓ policy: refunds over $100 need a person, e-mail only to @example-shop.com, no customer export")

    (STATE / "config.json").write_text(json.dumps({"url": URL, "org": ORG, "identity": str(IDENTITY),
                                                   "agent_id": agent.agent_id}, indent=2))
    print(f"\n  Ready. Now: streamlit run app.py   (console: {URL}, {EMAIL})\n")


if __name__ == "__main__":
    main()
