import tempfile
import streamlit as st
from embedchain import App

# Define the embedchain_bot function
def embedchain_bot(db_path, api_key):
    return App.from_config(
        config={
            "llm": {"provider": "openai", "config": {"model": "gpt-4-turbo", "temperature": 0.5, "api_key": api_key}},
            "vectordb": {"provider": "chroma", "config": {"dir": db_path}},
            "embedder": {"provider": "openai", "config": {"api_key": api_key}},
        }
    )

# Create Streamlit app
st.title("Chat with your Gmail Inbox 📧")
st.caption("This app allows you to chat with your Gmail inbox using OpenAI API")

# Get the OpenAI API key from the user
openai_access_token = st.text_input("Enter your OpenAI API Key", type="password")

# Set the Gmail filter statically
gmail_filter = "to: me label:inbox"

# Add the Gmail data to the knowledge base if the OpenAI API key is provided
if openai_access_token:
    # Create a temporary directory to store the database
    db_path = tempfile.mkdtemp()
    # Create an instance of Embedchain App
    app = embedchain_bot(db_path, openai_access_token)
    app.add(gmail_filter, data_type="gmail")
    st.success(f"Added emails from Inbox to the knowledge base!")

    # Ask a question about the emails
    prompt = st.text_input("Ask any question about your emails")

    # Chat with the emails
    if prompt:
        answer = app.query(prompt)
        st.write(answer)