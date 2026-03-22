"""AI Agent Governance with Aegis — Streamlit Demo

Demonstrates how to add policy-based governance to AI agent tool calls
using Aegis. Define YAML policies to control what actions agents can take,
with automatic approval gates and full audit logging.

No API keys required — this demo uses a simulated agent executor.

Run:
    streamlit run aegis_governance_app.py
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import streamlit as st
from aegis import Action, Policy, Result, ResultStatus, Runtime
from aegis.adapters.base import BaseExecutor
from aegis.runtime.approval import AutoApprovalHandler
from aegis.runtime.audit import AuditLogger

# ---------------------------------------------------------------------------
# Simulated executor — no real API calls
# ---------------------------------------------------------------------------

class SimulatedAgentExecutor(BaseExecutor):
    """Simulates AI agent tool execution for demonstration."""

    async def execute(self, action: Action) -> Result:
        responses = {
            "search": {"results": ["Q3 revenue report", "Market analysis 2024"]},
            "read": {"data": "Contact: Alice (alice@example.com)"},
            "write": {"written": True, "field": action.params.get("field", "unknown")},
            "send_email": {"sent": True, "to": action.params.get("to", "unknown")},
            "delete": {"deleted": True, "target": action.target},
            "bulk_update": {"updated": action.params.get("count", 0)},
            "export": {"exported": True, "format": action.params.get("format", "csv")},
        }
        data = responses.get(action.type, {"result": "ok"})
        return Result(
            action=action,
            status=ResultStatus.SUCCESS,
            data=data,
            completed_at=datetime.now(UTC),
        )


# ---------------------------------------------------------------------------
# Default policy — editable in the UI
# ---------------------------------------------------------------------------

DEFAULT_POLICY = """\
version: "1"
defaults:
  risk_level: medium
  approval: approve

rules:
  - name: search_auto
    match: { type: "search*" }
    risk_level: low
    approval: auto

  - name: read_auto
    match: { type: "read" }
    risk_level: low
    approval: auto

  - name: write_approve
    match: { type: "write" }
    risk_level: medium
    approval: approve

  - name: send_email_approve
    match: { type: "send_email" }
    risk_level: medium
    approval: approve

  - name: export_high
    match: { type: "export" }
    risk_level: high
    approval: approve

  - name: bulk_ops_high
    match: { type: "bulk_*" }
    risk_level: high
    approval: approve

  - name: delete_block
    match: { type: "delete" }
    risk_level: critical
    approval: block
"""

# ---------------------------------------------------------------------------
# Predefined agent scenarios
# ---------------------------------------------------------------------------

SCENARIOS = {
    "CRM Agent — Customer Lookup": [
        Action("search", "crm", params={"query": "top customers Q3"}),
        Action("read", "crm", params={"selector": ".contacts"}),
        Action("write", "crm", params={"field": "status", "value": "active"}),
    ],
    "Email Agent — Send Campaign": [
        Action("read", "contacts", params={"list": "newsletter"}),
        Action("send_email", "smtp", params={"to": "team@example.com", "subject": "Weekly update"}),
        Action("send_email", "smtp", params={"to": "all-customers@example.com", "subject": "Promo"}),
    ],
    "Data Agent — Export & Cleanup": [
        Action("search", "database", params={"query": "stale records"}),
        Action("export", "database", params={"format": "csv", "table": "users"}),
        Action("bulk_update", "database", params={"count": 500, "field": "archived"}),
        Action("delete", "database", params={"id": "all", "table": "temp_cache"}),
    ],
}

# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

RISK_COLORS = {
    "low": "🟢",
    "medium": "🟡",
    "high": "🟠",
    "critical": "🔴",
}


def run_scenario(policy_yaml: str, actions: list[Action]) -> None:
    """Execute a scenario through Aegis and display results."""
    try:
        policy = Policy.from_yaml(policy_yaml)
    except Exception as e:
        st.error(f"Invalid policy YAML: {e}")
        return

    runtime = Runtime(
        executor=SimulatedAgentExecutor(),
        policy=policy,
        approval_handler=AutoApprovalHandler(),
        audit_logger=AuditLogger(db_path=":memory:"),
    )

    plan = runtime.plan(actions)

    # Show execution plan
    st.subheader("Execution Plan")
    st.code(plan.summary(), language="text")

    # Execute
    results = asyncio.run(runtime.execute(plan))

    # Show results
    st.subheader("Results")
    for r in results:
        icon = "✅" if r.status == ResultStatus.SUCCESS else "🚫"
        st.markdown(f"{icon} **{r.action.type}**(`{r.action.target}`) → `{r.status.value}`")

    # Show audit log
    st.subheader("Audit Trail")
    log_entries = runtime.audit.get_log(session_id=runtime.session_id)
    if log_entries:
        rows = []
        for entry in log_entries:
            risk = entry["risk_level"]
            rows.append({
                "Action": entry["action_type"],
                "Target": entry.get("action_target", "-"),
                "Risk": f"{RISK_COLORS.get(risk, '⚪')} {risk}",
                "Decision": entry.get("human_decision") or entry["approval"],
                "Result": entry.get("result_status") or "-",
            })
        st.table(rows)
    else:
        st.info("No audit entries recorded.")


def main() -> None:
    st.set_page_config(page_title="Aegis — AI Agent Governance", layout="wide")
    st.title("🛡️ Aegis — AI Agent Governance")
    st.markdown(
        "Policy-based governance for AI agent tool calls. "
        "Edit the YAML policy, pick a scenario, and see how Aegis "
        "controls what the agent can do — with a full audit trail."
    )

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("Policy (YAML)")
        policy_yaml = st.text_area(
            "Edit the policy below:",
            value=DEFAULT_POLICY,
            height=400,
            label_visibility="collapsed",
        )

        st.subheader("Scenario")
        scenario_name = st.selectbox("Choose an agent scenario:", list(SCENARIOS.keys()))

        st.markdown("**Actions in this scenario:**")
        for a in SCENARIOS[scenario_name]:
            st.markdown(f"- `{a.type}` → `{a.target}`")

        run_button = st.button("▶ Run Scenario", type="primary", use_container_width=True)

    with col_right:
        if run_button:
            run_scenario(policy_yaml, SCENARIOS[scenario_name])
        else:
            st.info("👈 Edit the policy and click **Run Scenario** to see Aegis in action.")
            st.markdown(
                """
                ### How It Works

                1. **Define a YAML policy** — set risk levels and approval rules for each action type
                2. **Agent proposes actions** — tool calls are intercepted before execution
                3. **Aegis evaluates** — each action is matched against policy rules
                4. **Approval gates** — `auto` (proceed), `approve` (require confirmation), `block` (deny)
                5. **Full audit trail** — every decision is logged with timestamps

                ### Risk Levels

                | Level | Meaning |
                |-------|---------|
                | 🟢 low | Read-only, no side effects |
                | 🟡 medium | Writes to a single record |
                | 🟠 high | Bulk operations, data export |
                | 🔴 critical | Destructive actions — blocked by default |
                """
            )


if __name__ == "__main__":
    main()
