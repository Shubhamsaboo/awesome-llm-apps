import os
import requests
import streamlit as st
from anthropic import Anthropic

YOURMEMORY_URL = "http://localhost:3033"
USER_ID = "demo"

st.title("AI Assistant with Biological Memory 🧠")
st.caption("Memories decay over time, strengthen on recall, and connect through an entity graph.")

anthropic_key = st.sidebar.text_input("Anthropic API Key", type="password")

if not anthropic_key:
    st.warning("Enter your Anthropic API key in the sidebar to start.")
    st.stop()

client = Anthropic(api_key=anthropic_key)


def recall(query):
    try:
        r = requests.post(f"{YOURMEMORY_URL}/recall", json={"query": query, "user_id": USER_ID, "top_k": 5}, timeout=5)
        return r.json().get("memories", [])
    except Exception:
        return []


def store(content, importance=0.7, category="fact"):
    try:
        requests.post(f"{YOURMEMORY_URL}/store", json={
            "content": content, "user_id": USER_ID,
            "importance": importance, "category": category
        }, timeout=5)
    except Exception:
        pass


def list_memories():
    try:
        r = requests.get(f"{YOURMEMORY_URL}/memories?user_id={USER_ID}&limit=20", timeout=5)
        return r.json().get("memories", [])
    except Exception:
        return []


# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Memory panel
with st.sidebar:
    st.subheader("Memory Panel")
    if st.button("Refresh memories"):
        st.session_state.all_memories = list_memories()

    for mem in st.session_state.get("all_memories", []):
        strength = mem.get("strength", 1.0)
        color = "#00D4FF" if strength > 0.5 else "#f59e0b" if strength > 0.2 else "#6b7280"
        st.markdown(
            f"<div style='border-left:3px solid {color};padding:6px 10px;margin:4px 0;font-size:12px'>"
            f"{mem.get('content','')[:80]}<br>"
            f"<span style='color:{color};font-family:monospace'>strength {strength:.2f} · {mem.get('category','fact')}</span>"
            f"</div>",
            unsafe_allow_html=True
        )

# Chat input
if prompt := st.chat_input("Ask anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Recall relevant memories
    memories = recall(prompt)
    memory_context = ""
    if memories:
        memory_context = "Relevant memories from past sessions:\n" + "\n".join(
            f"- {m['content']} (strength: {m.get('strength', 1.0):.2f})"
            for m in memories
        ) + "\n\n"

    system_prompt = (
        "You are a helpful assistant with persistent memory across sessions. "
        "Use the recalled memories to give personalised, context-aware responses. "
        "After answering, if the user revealed a preference, fact, or important context, "
        "note it in your response with [STORE: <fact>] so it can be saved."
    )

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]],
                    {"role": "user", "content": memory_context + prompt}
                ]
            )
            reply = response.content[0].text

        # Parse and store any [STORE: ...] facts
        import re
        facts = re.findall(r'\[STORE:\s*(.+?)\]', reply)
        clean_reply = re.sub(r'\[STORE:\s*.+?\]', '', reply).strip()

        st.markdown(clean_reply)

        if facts:
            for fact in facts:
                store(fact.strip())
            st.caption(f"💾 Stored {len(facts)} new memory{'s' if len(facts) > 1 else ''}")

    st.session_state.messages.append({"role": "assistant", "content": clean_reply})
