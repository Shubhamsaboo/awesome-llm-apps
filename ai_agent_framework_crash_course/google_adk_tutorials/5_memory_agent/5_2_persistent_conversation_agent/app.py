import streamlit as st
import asyncio
from agent import chat, session_service

# Page configuration
st.set_page_config(page_title="Persistent Agent", page_icon="🗄️")

# Title
st.title("🗄️ Persistent Conversation Agent")
st.markdown("Simple demo of `DatabaseSessionService` - agent remembers conversations across program restarts using SQLite database.")

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
        with st.spinner("Thinking with persistent memory..."):
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
    1. **Database Storage**: Uses SQLite database (sessions.db)
    2. **Persistent Memory**: Survives program restarts
    3. **Cross-Session**: Remembers across multiple sessions
    4. **Simple State**: Basic conversation history

    **Test**: Tell it your name, restart the app, ask "What's my name?"
    
    **Database**: Check `sessions.db` file in project directory
    """)
    
    st.markdown("---")
    st.markdown("### 🗄️ Database Info")
    st.markdown("""
    **File:** `sessions.db`
    **Type:** SQLite database
    **Persistence:** Survives restarts
    **Location:** Project directory
    """) 