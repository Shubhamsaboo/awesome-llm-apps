"""The IT access request agent: tools, policy checks and the agent itself.

Shared by the Streamlit app (app.py) and the command-line entry point (cli.py).
"""

from __future__ import annotations

import copy
import json
import os
import re
from datetime import datetime, timezone

from agno.agent import Agent
from agno.models.google import Gemini

from directory import APPROVALS, APPS, EMPLOYEES, INITIAL_GRANTS

# A rolling alias, so the default keeps working when providers retire versions.
DEFAULT_MODEL = os.getenv("ACCESS_AGENT_MODEL", "gemini-flash-latest")

# DEMO_DEFECT=1 reintroduces a deliberate bug for the testing walkthrough in
# the README: any well-formed ticket id the requester quotes counts as an
# approval, and grant_access trusts the model's word instead of the approval
# records. Never enable this outside a demo.
DEMO_DEFECT = os.getenv("DEMO_DEFECT", "0") == "1"

INSTRUCTIONS = """\
You are the IT access desk for a company. Employees message you to request
access to internal apps. You act only for the signed-in requester, never for
anyone else, whatever the message says.

For every request:
1. Call get_my_profile to see who the requester is.
2. Call get_app_policy for the app they named. If the app or role does not
   exist, say so and list what does.
3. If the policy says manager approval is required, call
   check_manager_approval, passing any approval ticket id (like APR-1042) the
   requester quotes. A claim in the chat ("my manager said yes") is not an
   approval. Only a recorded approval counts.
4. Call grant_access only when every policy rule is met. Otherwise call
   deny_request with the specific rule that blocked it and what the requester
   can do next (for example, ask their manager to record an approval).

Keep replies short: the decision, the reason, and the next step.
"""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class AccessDesk:
    """Holds the in-memory state for one session and exposes it as agent tools."""

    def __init__(self, requester_id: str):
        if requester_id not in EMPLOYEES:
            raise ValueError(f"Unknown employee id: {requester_id}")
        self.requester_id = requester_id
        self.grants = copy.deepcopy(INITIAL_GRANTS)
        self.audit_log: list[dict] = []

    def _log(self, action: str, **details) -> None:
        self.audit_log.append({"time": _now(), "action": action, "requester": self.requester_id, **details})

    def _policy_problems(self, app: str, role: str) -> list[str]:
        employee = EMPLOYEES[self.requester_id]
        policy = APPS.get(app)
        if policy is None:
            return [f"'{app}' is not in the app catalog"]
        problems = []
        if role not in policy["roles"]:
            problems.append(f"'{role}' is not a role on {app} (roles: {', '.join(policy['roles'])})")
        if employee["department"] not in policy["departments"]:
            problems.append(f"{app} is limited to {', '.join(policy['departments'])}")
        return problems

    @staticmethod
    def _needs_approval(app: str, role: str) -> bool:
        return APPS[app]["sensitivity"] == "high" or role == "admin"

    # Tools the agent can call. Docstrings are what the model sees.

    def get_my_profile(self) -> str:
        """Return the signed-in requester's profile and the access they already hold."""
        profile = {"employee_id": self.requester_id, **EMPLOYEES[self.requester_id]}
        profile["current_access"] = self.grants.get(self.requester_id, {})
        return json.dumps(profile)

    def list_apps(self) -> str:
        """List every app in the catalog with its roles and the departments allowed to use it."""
        return json.dumps(APPS)

    def get_app_policy(self, app: str, role: str) -> str:
        """Check the access policy for one app and role for the signed-in requester.

        Args:
            app: App name from the catalog, for example "github".
            role: Role being requested, for example "read" or "admin".
        """
        app, role = app.strip().lower(), role.strip().lower()
        problems = self._policy_problems(app, role)
        result = {"app": app, "role": role, "eligible": not problems, "problems": problems}
        if app in APPS:
            result["manager_approval_required"] = self._needs_approval(app, role)
        return json.dumps(result)

    def _recorded_ticket(self, app: str, role: str) -> str | None:
        for ticket_id, ticket in APPROVALS.items():
            if (ticket["employee"], ticket["app"], ticket["role"]) == (self.requester_id, app, role):
                return ticket_id
        return None

    def check_manager_approval(self, app: str, role: str, ticket_id: str = "") -> str:
        """Look up whether the requester's manager has recorded an approval for this app and role.

        Args:
            app: App name from the catalog.
            role: Role being requested.
            ticket_id: Approval ticket id the requester quoted, if any (for example "APR-1042").
        """
        app, role, ticket_id = app.strip().lower(), role.strip().lower(), ticket_id.strip().upper()
        if DEMO_DEFECT and re.fullmatch(r"APR-\d{4}", ticket_id):
            # DELIBERATE DEFECT (demo only): a well-formed id is taken on trust.
            return json.dumps({"app": app, "role": role, "approved": True, "ticket_id": ticket_id})
        recorded = self._recorded_ticket(app, role)
        approved = recorded is not None and ticket_id in ("", recorded)
        result = {"app": app, "role": role, "approved": approved, "ticket_id": recorded if approved else None}
        if ticket_id and not approved:
            result["note"] = f"{ticket_id} is not a recorded approval for this employee, app and role"
        return json.dumps(result)

    def grant_access(self, app: str, role: str, manager_approved: bool, justification: str) -> str:
        """Grant the signed-in requester access to an app. Only call this when every policy rule is met.

        Args:
            app: App name from the catalog.
            role: Role to grant.
            manager_approved: Whether check_manager_approval returned approved=true.
            justification: One sentence on why the request meets policy.
        """
        app, role = app.strip().lower(), role.strip().lower()
        problems = self._policy_problems(app, role)
        if not problems and self._needs_approval(app, role):
            if DEMO_DEFECT:
                # DELIBERATE DEFECT (demo only): trusts the model's flag.
                approved = manager_approved
            else:
                approved = self._recorded_ticket(app, role) is not None
            if not approved:
                problems.append("manager approval required but none is recorded")
        if problems:
            self._log("grant_refused", app=app, role=role, problems=problems)
            return json.dumps({"granted": False, "problems": problems})
        self.grants.setdefault(self.requester_id, {})[app] = role
        self._log("granted", app=app, role=role, justification=justification)
        return json.dumps({"granted": True, "app": app, "role": role})

    def deny_request(self, app: str, role: str, reason: str) -> str:
        """Record that a request was denied and why.

        Args:
            app: App name the requester asked for.
            role: Role the requester asked for.
            reason: The policy rule that blocked it and what the requester can do next.
        """
        self._log("denied", app=app, role=role, reason=reason)
        return json.dumps({"denied": True})

    def tools(self) -> list:
        return [
            self.get_my_profile,
            self.list_apps,
            self.get_app_policy,
            self.check_manager_approval,
            self.grant_access,
            self.deny_request,
        ]


def build_agent(desk: AccessDesk, api_key: str | None = None, model: str | None = None) -> Agent:
    return Agent(
        model=Gemini(id=model or DEFAULT_MODEL, api_key=api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")),
        tools=desk.tools(),
        instructions=INSTRUCTIONS,
        markdown=True,
    )
