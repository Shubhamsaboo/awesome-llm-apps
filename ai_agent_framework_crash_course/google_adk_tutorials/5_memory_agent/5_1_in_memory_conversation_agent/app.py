import streamlit as st
import asyncio
from agent import chat

# Page configuration
st.set_page_config(page_title="In-Memory Agent", page_icon="🧠")

# Title
st.title("🧠 In-Memory Conversation Agent")
st.markdown("Simple demo of `InMemorySessionService` - agent remembers conversations within a session.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Say something..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = asyncio.run(chat("demo_user", prompt))
            st.markdown(response)
    
    # Add assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})

# Clear button
if st.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# Sidebar info
with st.sidebar:
    st.header("ℹ️ How it works")
    st.markdown("""
    1. **Session Creation**: Creates session for user
    2. **State Storage**: Saves conversation history
    3. **Memory Retrieval**: Uses previous context
    4. **Temporary**: Lost when app restarts
    
    **Test**: Tell it your name, then ask "What's my name?"
    """) 