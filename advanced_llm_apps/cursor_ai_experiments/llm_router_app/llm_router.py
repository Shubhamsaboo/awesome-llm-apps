import streamlit as st
from routellm.controller import Controller

# Set up Streamlit app
st.title("RouteLLM Chat App")

# API key input via sidebar
openai_key = st.sidebar.text_input("OpenAI API Key", type="password")
together_key = st.sidebar.text_input("Together AI API Key", type="password")

if not openai_key or not together_key:
    st.info("Enter your OpenAI and Together AI API keys in the sidebar to get started.")
    st.stop()

import os
os.environ["OPENAI_API_KEY"] = openai_key
os.environ["TOGETHERAI_API_KEY"] = together_key

# Initialize RouteLLM client
client = Controller(
    routers=["mf"],
    strong_model="gpt-4o-mini",
    weak_model="together_ai/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "model" in message:
            st.caption(f"Model used: {message['model']}")

# Chat input
if prompt := st.chat_input("What is your message?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get RouteLLM response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        response = client.chat.completions.create(
            model="router-mf-0.11593",
            messages=[{"role": "user", "content": prompt}]
        )
        message_content = response['choices'][0]['message']['content']
        model_name = response['model']
        
        # Display assistant's response
        message_placeholder.markdown(message_content)
        st.caption(f"Model used: {model_name}")
    
    # Add assistant's response to chat history
    st.session_state.messages.append({"role": "assistant", "content": message_content, "model": model_name})