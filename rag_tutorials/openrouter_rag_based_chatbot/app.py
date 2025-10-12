import streamlit as st
import requests
import os
from dotenv import load_dotenv
from utils.pdf_reader import extract_text_from_pdf

# Load environment variables
load_dotenv()
OPEN_ROUTER_KEY = os.getenv("OPEN_ROUTER_KEY")
if not OPEN_ROUTER_KEY:
    st.error("OpenRouter API key not found! Add OPEN_ROUTER_KEY to your .env file.")
    st.stop()

# Streamlit configuration
st.set_page_config(page_title="RAG Chatbot", layout="wide")
st.title("💬 RAG Chatbot (OpenRouter + Streamlit)")
st.caption("Uses uploaded PDFs as knowledge base — session-only chat.")

# Session state for chat
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Sidebar: PDF upload
st.sidebar.header("⚙️ Settings")
uploaded_file = st.sidebar.file_uploader("Upload Knowledge File (.pdf)", type=["pdf"])
knowledge_base = ""

if uploaded_file:
    knowledge_base = extract_text_from_pdf(uploaded_file)
    st.sidebar.success("✅ PDF loaded successfully!")

def query_openrouter(prompt_text: str, context_text: str = "") -> str:
    """
    Send prompt and optional PDF context to OpenRouter API.
    Returns assistant response or error message.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPEN_ROUTER_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant using RAG."},
            {"role": "system", "content": f"Context extracted from PDF:\n{context_text}"},
            {"role": "user", "content": prompt_text},
        ],
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"⚠️ OpenRouter API Error: {e}"

def display_messages():
    """
    Render all user and assistant messages from session state.
    """
    for msg in st.session_state["messages"]:
        role = "user" if msg["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(msg["content"])

# Chat input and main handler
prompt = st.chat_input("Type your message here...")

if prompt:
    # Store user message and render immediately
    st.session_state["messages"].append({"role": "user", "content": prompt})
    display_messages()

    # Determine RAG context from uploaded PDF
    context = knowledge_base if knowledge_base else "No PDF context provided."

    # Query OpenRouter for assistant reply
    with st.spinner("🤔 Thinking..."):
        reply = query_openrouter(prompt, context)

    # Store and display assistant reply
    st.session_state["messages"].append({"role": "assistant", "content": reply})
    display_messages()
else:
    # Display existing chat messages
    display_messages()