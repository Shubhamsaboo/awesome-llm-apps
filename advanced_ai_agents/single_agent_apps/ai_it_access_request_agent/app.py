"""Streamlit chat UI for the IT access request agent."""

import os

import streamlit as st

from access_agent import DEFAULT_MODEL, DEMO_DEFECT, AccessDesk, build_agent
from directory import APPS, EMPLOYEES

st.set_page_config(page_title="IT Access Request Agent", page_icon="🔐")
st.title("🔐 AI IT Access Request Agent")
st.caption("Ask for access to an internal app. The agent checks policy and manager approvals before granting anything.")

with st.sidebar:
    api_key = st.text_input(
        "Gemini API key", type="password", value=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY", "")
    )
    model = st.text_input("Model", value=DEFAULT_MODEL)
    requester = st.selectbox(
        "Signed in as",
        sorted(EMPLOYEES),
        format_func=lambda e: f"{e} · {EMPLOYEES[e]['name']}",
    )
    if DEMO_DEFECT:
        st.warning("DEMO_DEFECT=1: approval checks are deliberately broken.")
    with st.expander("App catalog"):
        for name, policy in APPS.items():
            st.markdown(f"**{name}** · {policy['sensitivity']} · roles: {', '.join(policy['roles'])}")

# Switching the signed-in employee starts a fresh session.
if st.session_state.get("requester") != requester:
    st.session_state.requester = requester
    st.session_state.desk = AccessDesk(requester)
    st.session_state.messages = []

desk: AccessDesk = st.session_state.desk

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("e.g. I need read access to prod-database"):
    if not api_key:
        st.error("Add your Gemini API key in the sidebar.")
        st.stop()
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Checking policy..."):
            reply = build_agent(desk, api_key=api_key, model=model).run(prompt).content
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})

st.divider()
col_access, col_log = st.columns(2)
with col_access:
    st.subheader("Current access")
    st.json(desk.grants.get(requester, {}))
with col_log:
    st.subheader("Audit log")
    st.json(desk.audit_log)
