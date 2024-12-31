import tempfile
from embedchain import App
import streamlit as st
import os

def embedchain_bot(db_path):
    return App.from_config(
        config={
            "llm": {"provider": "ollama", "config": {"model": "llama3:instruct", "max_tokens": 250, "temperature": 0.5, "stream": True, "base_url": 'http://localhost:11434'}},
            "vectordb": {"provider": "chroma", "config": {"dir": db_path}},
            "embedder": {"provider": "ollama", "config": {"model": "llama3:instruct", "base_url": 'http://localhost:11434'}},
        }
    )

def make_db_path():
    ret = tempfile.mkdtemp(suffix="chroma")
    print(f"Created Chroma DB at {ret}")    
    return ret

# Create Streamlit app
st.title("Chat with your Gmail Inbox 📧")
st.caption("This app allows you to chat with your Gmail inbox using Llama-3 running with Ollama")

# Initialize the Embedchain App if not already in session state
if "app" not in st.session_state:
    st.session_state['app'] = embedchain_bot(make_db_path())

app = st.session_state.app

# Set the Gmail filter statically
gmail_filter = "to: me label:inbox"

# Add Gmail data to knowledge base if not already added
if "gmail_loaded" not in st.session_state:
    app.add(gmail_filter, data_type="gmail")
    st.session_state["gmail_loaded"] = True
    st.success(f"Added emails from Inbox to the knowledge base!")

# Ask a question about the emails
prompt = st.text_input("Ask any question about your emails")

# Chat with the emails
if prompt:
    answer = app.chat(prompt)
    st.write(answer)