import streamlit as st
from ollama import Client

# Initialize Ollama client
client = Client()

# Set up Streamlit page
st.set_page_config(page_title="Local ChatGPT Clone", page_icon="🤖", layout="wide")
st.title("🤖 Local ChatGPT Clone")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("What's on your mind?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate AI response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for response in client.chat(model="llama3.1:latest", messages=st.session_state.messages, stream=True):
            full_response += response['message']['content']
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# Add a sidebar with information
st.sidebar.title("About")
st.sidebar.info("This is a local ChatGPT clone using Ollama's llama3.1:latest model and Streamlit.")
st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️ by Your Name")