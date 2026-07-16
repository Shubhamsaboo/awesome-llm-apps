import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

MANIFEST_API_KEY = os.getenv("MANIFEST_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

st.set_page_config(page_title="Manifest MCP Agent", page_icon="🗺️", layout="wide")
st.title("🗺️ Manifest MCP Agent")
st.markdown(
    "Turn any URL into a structured action map, then let an LLM reason about "
    "what an agent could do on that page."
)

url = st.text_input("Enter a URL", placeholder="https://example.com/checkout")

col1, col2 = st.columns([1, 1])

manifest_data = None

with col1:
    if st.button("Generate Manifest", type="primary", disabled=not url):
        if not MANIFEST_API_KEY:
            st.error("MANIFEST_API_KEY not set in .env")
        else:
            with st.spinner("Calling Manifest API..."):
                try:
                    resp = requests.post(
                        "https://manifest.omfang.io/manifest",
                        headers={"X-API-Key": MANIFEST_API_KEY, "Content-Type": "application/json"},
                        json={"url": url},
                        timeout=30,
                    )
                    resp.raise_for_status()
                    manifest_data = resp.json()
                    st.session_state["manifest"] = manifest_data
                except requests.exceptions.RequestException as e:
                    st.error(f"API error: {e}")

if "manifest" in st.session_state:
    manifest_data = st.session_state["manifest"]
    
    st.subheader("Page state")
    st.info(manifest_data.get("current_page_state", "Unknown"))

    st.subheader(f"Actions ({len(manifest_data.get('actions', []))})")
    for action in manifest_data.get("actions", []):
        with st.expander(f"{action.get('label', action.get('id'))} — `{action.get('type')}` {'🔴 required' if action.get('required') else ''}"):
            st.json(action)

    if manifest_data.get("navigation"):
        st.subheader("Navigation")
        for nav in manifest_data["navigation"]:
            st.markdown(f"- [{nav.get('label')}]({nav.get('url')})")

    st.divider()
    
    if st.button("Explain agent plan"):
        if not OPENAI_API_KEY and not ANTHROPIC_API_KEY:
            st.error("Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env")
        else:
            prompt = (
                f"You are an AI agent. You have been given this action manifest for the URL {manifest_data.get('url')}:\n\n"
                f"{json.dumps(manifest_data, indent=2)}\n\n"
                "Describe step by step how you would interact with this page to complete a typical task. "
                "Reference specific action IDs, note required fields, and explain the order of operations based on the requires field."
            )
            with st.spinner("Thinking..."):
                if OPENAI_API_KEY:
                    import openai
                    client = openai.OpenAI(api_key=OPENAI_API_KEY)
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                    )
                    plan = response.choices[0].message.content
                else:
                    import anthropic
                    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                    message = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=1024,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    plan = message.content[0].text

            st.subheader("Agent interaction plan")
            st.markdown(plan)
