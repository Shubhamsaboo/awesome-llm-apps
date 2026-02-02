import streamlit as st
import os
from datetime import datetime
from memlayer.wrappers.openai import OpenAI as MemLayerOpenAI

# Set up the Streamlit App
st.title("AI Contextual Memory Assistant 🧠")
st.caption("Chat with an intelligent assistant that remembers context from your past conversations.")

# Initialize session state for API key and authentication
if "api_key_submitted" not in st.session_state:
    st.session_state.api_key_submitted = False
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = None

# Initialize chat sessions
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {}
    st.session_state.current_chat_id = None
    st.session_state.chat_counter = 0

# API Key input with submit button
if not st.session_state.api_key_submitted:
    st.markdown("### 🔑 Enter your OpenAI API Key to get started")
    col1, col2 = st.columns([3, 1])
    with col1:
        api_key_input = st.text_input("OpenAI API Key", type="password", key="api_key_input")
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        submit_button = st.button("Submit", type="primary")
    
    if submit_button and api_key_input:
        st.session_state.openai_api_key = api_key_input
        st.session_state.api_key_submitted = True
        os.environ["OPENAI_API_KEY"] = api_key_input
        st.rerun()
    elif submit_button and not api_key_input:
        st.error("Please enter your OpenAI API key")
else:
    os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key

if st.session_state.api_key_submitted:
    # Sidebar for username and chat management
    st.sidebar.title("User Settings")
    user_id = st.sidebar.text_input("Username", value="user_123", key="user_id")

    st.sidebar.markdown("---")
    st.sidebar.title("💬 Chat Sessions")
    
    # New chat button
    if st.sidebar.button("➕ New Chat", use_container_width=True):
        st.session_state.chat_counter += 1
        chat_id = f"chat_{st.session_state.chat_counter}"
        timestamp = datetime.now().strftime("%I:%M %p")
        st.session_state.chat_sessions[chat_id] = {
            "name": f"Chat {st.session_state.chat_counter}",
            "messages": [],
            "created": timestamp
        }
        st.session_state.current_chat_id = chat_id
        st.rerun()
    
    # Create first chat if none exists
    if not st.session_state.chat_sessions:
        st.session_state.chat_counter += 1
        chat_id = f"chat_{st.session_state.chat_counter}"
        timestamp = datetime.now().strftime("%I:%M %p")
        st.session_state.chat_sessions[chat_id] = {
            "name": f"Chat {st.session_state.chat_counter}",
            "messages": [],
            "created": timestamp
        }
        st.session_state.current_chat_id = chat_id
    
    # Display chat sessions
    for chat_id, chat_data in st.session_state.chat_sessions.items():
        col1, col2 = st.sidebar.columns([4, 1])
        with col1:
            if st.sidebar.button(
                f"💬 {chat_data['name']}",
                key=f"select_{chat_id}",
                use_container_width=True,
                type="primary" if chat_id == st.session_state.current_chat_id else "secondary"
            ):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with col2:
            if st.sidebar.button("🗑️", key=f"delete_{chat_id}"):
                del st.session_state.chat_sessions[chat_id]
                if st.session_state.current_chat_id == chat_id:
                    st.session_state.current_chat_id = list(st.session_state.chat_sessions.keys())[0] if st.session_state.chat_sessions else None
                st.rerun()

    # Initialize Memlayer client
    if "memlayer_client" not in st.session_state or st.session_state.get("current_user_id") != user_id:
        st.session_state.memlayer_client = MemLayerOpenAI(
            model="gpt-4.1-mini",
            storage_path="./memories",
            user_id=user_id,
            operation_mode="online",
        )
        st.session_state.current_user_id = user_id

    client = st.session_state.memlayer_client

    # Display current chat
    if st.session_state.current_chat_id:
        current_chat = st.session_state.chat_sessions[st.session_state.current_chat_id]
        
        # Display chat history
        for message in current_chat["messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Accept user input
        prompt = st.chat_input("Ask me anything! I'll remember our conversations...")

        if prompt:
            # Add user message to chat history
            current_chat["messages"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate response using Memlayer
            with st.spinner("Thinking..."):
                try:
                    # Convert chat history to memlayer format
                    messages = [{"role": msg["role"], "content": msg["content"]} 
                               for msg in current_chat["messages"]]
                    
                    # Get response with automatic memory management
                    answer = client.chat(messages)

                    # Add assistant response to chat history
                    current_chat["messages"].append({"role": "assistant", "content": answer})
                    with st.chat_message("assistant"):
                        st.markdown(answer)

                except Exception as e:
                    st.error(f"Error generating response: {str(e)}")
    else:
        st.info("👈 Create a new chat to get started!")

# Footer
st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: gray; font-size: 0.9em;">'
    'Powered by <a href="https://github.com/divagr18/memlayer" target="_blank">Memlayer</a>'
    '</p>',
    unsafe_allow_html=True
)
