"""AI Agent Governance with Aegis — Streamlit Demo

A real OpenAI-powered CRM agent governed by Aegis YAML policies.
The LLM autonomously decides which tools to call, while Aegis evaluates
every tool call against policy rules before execution — auto-approving
safe reads, requiring confirmation for writes, and blocking destructive
operations outright.

Run:
    streamlit run aegis_governance_app.py
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime

import yaml
import streamlit as st
from openai import OpenAI

from aegis import Action, Policy, Result, ResultStatus, Runtime
from aegis.adapters.base import BaseExecutor
from aegis.runtime.approval import AutoApprovalHandler
from aegis.runtime.audit import AuditLogger

# ---------------------------------------------------------------------------
# Tools — simulated business logic (the LLM decides which to call)
# ---------------------------------------------------------------------------

TOOL_FUNCTIONS = {
    "search_contacts": lambda params: {
        "results": [
            {"name": "Alice Kim", "email": "alice@example.com", "tier": "enterprise"},
            {"name": "Bob Park", "email": "bob@example.com", "tier": "pro"},
            {"name": "Carol Lee", "email": "carol@example.com", "tier": "free"},
        ],
        "query": params.get("query", ""),
    },
    "read_record": lambda params: {
        "record": {
            "id": params.get("record_id", "C-001"),
            "name": "Alice Kim",
            "email": "alice@example.com",
            "plan": "enterprise",
            "mrr": 2400,
            "last_contact": "2026-03-15",
        },
    },
    "update_record": lambda params: {
        "updated": True,
        "record_id": params.get("record_id", "C-001"),
        "field": params.get("field", "unknown"),
        "new_value": params.get("value", ""),
    },
    "send_email": lambda params: {
        "sent": True,
        "to": params.get("to", "unknown"),
        "subject": params.get("subject", ""),
    },
    "export_data": lambda params: {
        "exported": True,
        "format": params.get("format", "csv"),
        "row_count": 1847,
    },
    "delete_records": lambda params: {
        "deleted": True,
        "target": params.get("target", "unknown"),
        "count": params.get("count", 0),
    },
}

# OpenAI function definitions
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_contacts",
            "description": "Search CRM contacts by name, email, or keyword.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_record",
            "description": "Read a specific customer record by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "record_id": {"type": "string", "description": "Customer record ID"},
                },
                "required": ["record_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_record",
            "description": "Update a field on a customer record.",
            "parameters": {
                "type": "object",
                "properties": {
                    "record_id": {"type": "string", "description": "Customer record ID"},
                    "field": {"type": "string", "description": "Field name to update"},
                    "value": {"type": "string", "description": "New value"},
                },
                "required": ["record_id", "field", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email to a contact.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject line"},
                    "body": {"type": "string", "description": "Email body text"},
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "export_data",
            "description": "Export customer data to a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "enum": ["csv", "json", "xlsx"],
                        "description": "Export format",
                    },
                    "table": {"type": "string", "description": "Table or dataset name"},
                },
                "required": ["format"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_records",
            "description": "Delete customer records from the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Target table or record ID"},
                    "count": {"type": "integer", "description": "Number of records to delete"},
                },
                "required": ["target"],
            },
        },
    },
]

# ---------------------------------------------------------------------------
# Aegis executor — bridges tool functions with the governance layer
# ---------------------------------------------------------------------------


class GovernedExecutor(BaseExecutor):
    """Executes tool calls after Aegis policy approval."""

    async def execute(self, action: Action) -> Result:
        func = TOOL_FUNCTIONS.get(action.type)
        if func is None:
            return Result(
                action=action,
                status=ResultStatus.FAILURE,
                data={"error": f"Unknown tool: {action.type}"},
                completed_at=datetime.now(UTC),
            )
        data = func(action.params)
        return Result(
            action=action,
            status=ResultStatus.SUCCESS,
            data=data,
            completed_at=datetime.now(UTC),
        )


# ---------------------------------------------------------------------------
# Default governance policy
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
    match: { type: "read*" }
    risk_level: low
    approval: auto

  - name: update_approve
    match: { type: "update*" }
    risk_level: medium
    approval: approve

  - name: send_email_approve
    match: { type: "send_email" }
    risk_level: medium
    approval: approve

  - name: export_high
    match: { type: "export*" }
    risk_level: high
    approval: approve

  - name: delete_block
    match: { type: "delete*" }
    risk_level: critical
    approval: block
"""

RISK_LABEL = {1: "low", 2: "medium", 3: "high", 4: "critical"}
RISK_EMOJI = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴"}

SYSTEM_PROMPT = """\
You are a CRM assistant at a SaaS company. You manage customer records, \
handle outreach, and maintain data hygiene.

You have access to these tools:
- search_contacts: Search customers by name, email, or keyword
- read_record: Look up a specific customer record by ID
- update_record: Modify a field on a customer record
- send_email: Send an email to a customer
- export_data: Export customer data to CSV/JSON/XLSX
- delete_records: Delete customer records from the database

IMPORTANT: You MUST always call the appropriate tool for every user \
request, including destructive operations like delete. Never refuse a \
request on your own — an external governance system evaluates every \
tool call and decides whether it is allowed or blocked. Your job is to \
call the tool; the system handles the rest.

If a tool call returns a BLOCKED error:
1. Clearly explain to the user that the action was blocked by policy
2. Suggest a safer alternative (e.g., archive instead of delete, \
   export for review before bulk changes)

Be concise and helpful. Use tools proactively to answer user questions.\
"""

# ---------------------------------------------------------------------------
# Core agent loop — OpenAI function calling + Aegis governance
# ---------------------------------------------------------------------------


def run_governed_agent(
    client: OpenAI,
    model: str,
    messages: list[dict],
    policy: Policy,
    runtime: Runtime,
) -> tuple[str, list[dict]]:
    """Run the agent loop. Returns (final_response, governance_log)."""

    governance_log: list[dict] = []
    max_turns = 10

    for _ in range(max_turns):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=OPENAI_TOOLS,
        )

        choice = response.choices[0]

        # No more tool calls — return final text
        if choice.finish_reason != "tool_calls" or not choice.message.tool_calls:
            return choice.message.content or "", governance_log

        messages.append(choice.message)

        # Process each tool call through Aegis
        for tc in choice.message.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)

            action = Action(
                type=fn_name,
                target="crm",
                params=fn_args,
                description=f"LLM requested: {fn_name}",
            )

            # Aegis policy evaluation
            decision = policy.evaluate(action)
            risk_val = decision.risk_level.value
            risk_name = RISK_LABEL.get(risk_val, "unknown")
            approval = decision.approval.value

            entry = {
                "tool": fn_name,
                "args": fn_args,
                "risk": risk_name,
                "approval": approval,
                "emoji": RISK_EMOJI.get(risk_val, "⚪"),
                "status": "",
            }

            if decision.is_allowed:
                plan = runtime.plan([action])
                results = asyncio.run(runtime.execute(plan))
                result_data = results[0].data if results else {}
                entry["status"] = "executed"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result_data, ensure_ascii=False),
                })
            else:
                block_msg = (
                    f"BLOCKED by governance policy. "
                    f"Action '{fn_name}' is classified as {risk_name} risk "
                    f"and is not allowed. Suggest a safer alternative."
                )
                entry["status"] = "blocked"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps({"error": block_msg}),
                })

            governance_log.append(entry)

    return "Agent reached maximum turns.", governance_log


# ---------------------------------------------------------------------------
# Streamlit UI — chat interface with governance panel
# ---------------------------------------------------------------------------


def init_session_state():
    """Initialize Streamlit session state for chat history."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "governance_history" not in st.session_state:
        st.session_state.governance_history = []


def main():
    st.set_page_config(page_title="Aegis — AI Agent Governance", layout="wide")
    init_session_state()

    st.title("🛡️ Aegis — AI Agent Governance")
    st.caption(
        "A real OpenAI-powered CRM agent governed by YAML policies. "
        "The LLM decides which tools to call — Aegis evaluates every call "
        "against policy rules before execution."
    )

    # Sidebar — API key + model + policy editor
    with st.sidebar:
        st.header("⚙️ Settings")
        api_key = st.text_input("OpenAI API Key", type="password")
        model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"])

        st.divider()
        st.header("📋 Governance Policy")
        policy_yaml = st.text_area(
            "YAML policy:",
            value=DEFAULT_POLICY,
            height=380,
            label_visibility="collapsed",
        )
        st.caption(
            "🟢 low = auto | 🟡 medium = approve | 🟠 high = approve | 🔴 critical = block"
        )

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.governance_history = []
            st.rerun()

    # Main area — two columns: chat + governance
    chat_col, gov_col = st.columns([3, 2])

    with chat_col:
        # Render chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat input
        user_input = st.chat_input(
            "e.g., Search for enterprise customers and send them a promo email"
        )

        if user_input:
            if not api_key:
                st.error("Please enter your OpenAI API key in the sidebar.")
                st.stop()

            # Display user message
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            # Build messages for OpenAI
            try:
                policy = Policy.from_dict(yaml.safe_load(policy_yaml))
            except Exception as e:
                st.error(f"Invalid policy YAML: {e}")
                st.stop()

            runtime = Runtime(
                executor=GovernedExecutor(),
                policy=policy,
                approval_handler=AutoApprovalHandler(),
                audit_logger=AuditLogger(db_path=":memory:"),
            )

            openai_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for msg in st.session_state.chat_history:
                openai_messages.append({"role": msg["role"], "content": msg["content"]})

            # Run agent
            client = OpenAI(api_key=api_key)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    agent_response, gov_log = run_governed_agent(
                        client, model, openai_messages, policy, runtime
                    )

                # Stream-style rendering of response
                st.markdown(agent_response)

            st.session_state.chat_history.append(
                {"role": "assistant", "content": agent_response}
            )

            # Store governance log for this turn
            if gov_log:
                st.session_state.governance_history.append({
                    "query": user_input,
                    "decisions": gov_log,
                })

            # Force rerun so governance panel updates
            st.rerun()

    with gov_col:
        st.subheader("🔍 Governance Log")

        if not st.session_state.governance_history:
            st.info("Governance decisions will appear here as you chat with the agent.")
        else:
            # Show latest turn first
            for turn in reversed(st.session_state.governance_history):
                st.markdown(f"**Query:** {turn['query']}")
                for g in turn["decisions"]:
                    icon = "✅" if g["status"] == "executed" else "🚫"
                    st.markdown(
                        f"  {icon} {g['emoji']} **{g['tool']}** "
                        f"→ {g['risk']} / {g['approval']} → **{g['status']}**"
                    )
                    if g.get("args"):
                        st.caption(f"  Args: `{json.dumps(g['args'], ensure_ascii=False)}`")
                st.divider()

    # Example prompts at the bottom
    if not st.session_state.chat_history:
        st.divider()
        st.markdown("**Try these prompts:**")
        prompts = [
            "Search for our enterprise customers",
            "Look up customer C-001 and update their plan to premium",
            "Export all customer data as CSV",
            "Delete all inactive customer records",
        ]
        cols = st.columns(len(prompts))
        for i, p in enumerate(prompts):
            cols[i].markdown(f"- _{p}_")


if __name__ == "__main__":
    main()
