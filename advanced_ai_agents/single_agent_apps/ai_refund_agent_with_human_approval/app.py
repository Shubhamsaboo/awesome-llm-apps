"""
Governed refund agent - Streamlit UI.

    python setup_provenza.py      (once)
    streamlit run app.py

Pick a ticket and run the agent. Left: what the agent does. Right: what
Provenza decided about each tool call, with a link to its signed record.
"""

import json
import os
import socket
import threading
from pathlib import Path

import streamlit as st
from provenza import Agent

import agent as refund

HERE = Path(__file__).resolve().parent
CONFIG = HERE / ".provenza" / "config.json"
SHOP_PORT = int(os.environ.get("SHOP_PORT", "8765"))

st.set_page_config(page_title="Governed refund agent", page_icon="🛡️", layout="wide")

if not CONFIG.exists():
    st.error("Run `python setup_provenza.py` first: it enrolls the agent and gives it its policy.")
    st.stop()
cfg = json.loads(CONFIG.read_text())
os.environ.setdefault("PROVENZA_URL", cfg["url"])
os.environ.setdefault("PROVENZA_ORG", cfg["org"])


@st.cache_resource
def shop_api() -> str:
    """Start Example Shop's API next to the app (once per process)."""
    with socket.socket() as s:
        if s.connect_ex(("127.0.0.1", SHOP_PORT)) != 0:
            import uvicorn
            from shop_api import app as shop_app
            server = uvicorn.Server(uvicorn.Config(shop_app, host="127.0.0.1", port=SHOP_PORT, log_level="warning"))
            threading.Thread(target=server.run, daemon=True).start()
    return f"http://127.0.0.1:{SHOP_PORT}"


@st.cache_resource
def provenza_agent() -> Agent:
    return Agent("refund-agent", server_url=cfg["url"], identity_path=cfg["identity"])


def llm_client():
    """An OpenAI-compatible model if one is configured, else None (the scripted model)."""
    if not (os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_BASE_URL")):
        return None
    from openai import OpenAI
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY") or "ollama")


refund.SHOP_URL = shop_api()
agent = provenza_agent()
llm = llm_client()
model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
console = cfg["url"]

BADGE = {"allowed": ("✅", "allowed"), "approved": ("✅", "approved by a person, then allowed"),
         "denied": ("⛔", "refused"), "pending_approval": ("⏳", "waiting for a person"),
         "quarantined": ("🚨", "agent quarantined")}

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.header("🛡️ Governed refund agent")
    st.caption(f"Agent #{agent.agent_id} · `{agent.fingerprint[:22]}…`")
    st.markdown(f"Model: **{model}**" if llm else
                "Model: **scripted** - no API key set, so the model's choices are fixed. "
                "Provenza's decisions are real.")
    st.divider()
    st.markdown("**Its policy in Provenza**\n\n"
                "- refund over **$100** → a person approves\n"
                "- e-mail only to **@example-shop.com**\n"
                "- **never** export customers\n"
                "- 3 refusals in 10 minutes → quarantined")
    st.markdown(f"[Open the console]({console}) · [Approvals]({console}/approvals)")

# ------------------------------------------------------------------ ticket
st.title("Support agent with a policy it cannot talk its way around")
ids = list(refund.TICKETS)
choice = st.radio("Ticket", ids, format_func=lambda k: f"{k} · {refund.TICKETS[k][0]}", horizontal=True)
text = st.text_area("Customer's message", refund.TICKETS[choice][1], height=140)
run = st.button("Run the agent", type="primary")

left, right = st.columns([1, 1], gap="large")
left.subheader("Agent")
right.subheader("Provenza")

if run:
    import shop_api
    shop_api.REFUNDS.clear()            # a demo shop: every run starts from the same orders

    def wait(action_id: int) -> str:
        with right.status(f"Held for a person - approve action #{action_id} in the console", expanded=True) as s:
            s.markdown(f"[Approvals]({console}/approvals) · Provenza holds the call until someone decides.")
            decision = refund.wait_for(agent)(action_id)
            s.update(label=f"Action #{action_id}: {decision}", state="complete" if decision == "approved" else "error")
        return decision

    for ev in refund.run_ticket(agent, choice, text, wait, llm=llm, model=model):
        if ev.kind == "step":
            s = ev.step
            icon, label = BADGE.get(s.decision, ("•", s.decision))
            left.markdown(f"→ `{s.tool}` `{json.dumps(s.args)[:160]}`")
            record = f" · [record #{s.action_id}]({console}/audit?tab=evidence&action={s.action_id})" \
                if s.action_id else ""
            box = right.success if s.decision in ("allowed", "approved") else \
                right.warning if s.decision == "pending_approval" else right.error
            box(f"{icon} **{s.tool}** - {label}{record}\n\n{s.reason}")
            if s.decision in ("allowed", "approved") and s.result is not None:
                left.caption(f"shop API: {json.dumps(s.result)[:200]}")
        elif ev.kind == "message":
            left.info(ev.text)
        elif ev.kind == "done":
            left.caption("Done.")
