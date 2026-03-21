import os
import requests
import streamlit as st
from openai import OpenAI

st.title("LLM App with Persistent Memory 🧠")
st.caption(
    "AI chatbot powered by RetainDB — memories persist across sessions, "
    "browser refreshes, and server restarts."
)

# ── API keys ──────────────────────────────────────────────────────────────────
openai_api_key = st.text_input("OpenAI API Key", type="password")
retaindb_api_key = st.text_input("RetainDB API Key — get free at retaindb.com", type="password")

RETAINDB_BASE = "https://api.retaindb.com"

def retaindb_headers():
    return {
        "Authorization": f"Bearer {retaindb_api_key}",
        "Content-Type": "application/json",
    }

def get_context(user_id: str, query: str) -> str:
    """Retrieve relevant memories for this user and query."""
    resp = requests.post(
        f"{RETAINDB_BASE}/v1/context/query",
        headers=retaindb_headers(),
        json={
            "query": query,
            "user_id": user_id,
            "top_k": 8,
            "include_memories": True,
        },
        timeout=10,
    )
    if resp.ok:
        return resp.json().get("context", "")
    return ""

def remember(user_id: str, messages: list):
    """Store the conversation turn so future sessions can recall it."""
    requests.post(
        f"{RETAINDB_BASE}/v1/learn",
        headers=retaindb_headers(),
        json={
            "mode": "conversation",
            "user_id": user_id,
            "messages": messages,
        },
        timeout=10,
    )

def get_all_memories(user_id: str) -> list:
    """List all stored memories for this user."""
    resp = requests.get(
        f"{RETAINDB_BASE}/v1/memories",
        headers=retaindb_headers(),
        params={"user_id": user_id, "limit": 50},
        timeout=10,
    )
    if resp.ok:
        return resp.json().get("memories", [])
    return []


# ── Chat UI ───────────────────────────────────────────────────────────────────
if openai_api_key and retaindb_api_key:
    openai_client = OpenAI(api_key=openai_api_key)

    user_id = st.text_input("Username (used to scope your memories)", value="demo_user")

    # Session-level chat history (display only — real persistence is in RetainDB)
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    prompt = st.chat_input("Say something…")

    if prompt and user_id:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Recalling memories…"):
                # 1. Retrieve relevant memories
                context = get_context(user_id, prompt)

            system_prompt = "You are a helpful personal assistant with persistent memory."
            if context:
                system_prompt += f"\n\nWhat you know about this user:\n{context}"

            # 2. Generate response
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    *st.session_state.messages,
                ],
            )
            reply = response.choices[0].message.content
            st.write(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})

        # 3. Store the turn in RetainDB (fire-and-forget)
        remember(user_id, [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": reply},
        ])

    # ── Sidebar: view stored memories ─────────────────────────────────────────
    st.sidebar.title("🧠 Memory Store")
    st.sidebar.caption(f"Memories for: **{user_id}**")
    if st.sidebar.button("Load Memories"):
        memories = get_all_memories(user_id)
        if memories:
            for mem in memories:
                st.sidebar.markdown(f"- {mem.get('content', '')}")
        else:
            st.sidebar.info("No memories found yet — start chatting!")
else:
    st.info("Enter your API keys above to start chatting.")
