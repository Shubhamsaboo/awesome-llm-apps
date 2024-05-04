import streamlit as st
from embedchain import App
import tempfile

# Define the embedchain_bot function
def embedchain_bot(db_path, api_key):
    return App.from_config(
        config={
            "llm": {"provider": "openai", "config": {"model": "gpt-4-turbo", "temperature": 0.5, "api_key": api_key}},
            "vectordb": {"provider": "chroma", "config": {"dir": db_path}},
            "embedder": {"provider": "openai", "config": {"api_key": api_key}},
        }
    )

st.title("Chat with Substack Newsletter 📝")
st.caption("This app allows you to chat with Substack newsletter using OpenAI API")

# Get OpenAI API key from user
openai_access_token = st.text_input("OpenAI API Key", type="password")

if openai_access_token:
    # Create a temporary directory to store the database
    db_path = tempfile.mkdtemp()
    # Create an instance of Embedchain App
    app = embedchain_bot(db_path, openai_access_token)

    # Get the Substack blog URL from the user
    substack_url = st.text_input("Enter Substack Newsletter URL", type="default")

    if substack_url:
        # Add the Substack blog to the knowledge base
        app.add(substack_url, data_type='substack')
        st.success(f"Added {substack_url} to knowledge base!")

        # Ask a question about the Substack blog
        query = st.text_input("Ask any question about the substack newsletter!")

        # Query the Substack blog
        if query:
            result = app.query(query)
            st.write(result)
