# Import the required libraries
import tempfile
from embedchain import App
from embedchain.loaders.github import GithubLoader
import streamlit as st

loader = GithubLoader(
    config={
        "token":"Your GitHub Token",
        }
    )

# Define the embedchain_bot function
def embedchain_bot(db_path):
    return App.from_config(
        config={
            "llm": {"provider": "ollama", "config": {"model": "llama3:instruct", "max_tokens": 250, "temperature": 0.5, "stream": True, "base_url": 'http://localhost:11434'}},
            "vectordb": {"provider": "chroma", "config": {"dir": db_path}},
            "embedder": {"provider": "ollama", "config": {"model": "llama3:instruct", "base_url": 'http://localhost:11434'}},
        }
    )

# Create Streamlit app
st.title("Chat with GitHub Repository 💬")
st.caption("This app allows you to chat with a GitHub Repo using Llama-3 running with Ollama")

# Initialize the Embedchain App
db_path = tempfile.mkdtemp()
app = embedchain_bot(db_path)

# Get the GitHub repo from the user
git_repo = st.text_input("Enter the GitHub Repo", type="default")

if git_repo:
    # Add the repo to the knowledge base
    app.add("repo:" + git_repo + " " + "type:repo", data_type="github", loader=loader)
    st.success(f"Added {git_repo} to knowledge base!")
    # Ask a question about the Github Repo
    prompt = st.text_input("Ask any question about the GitHub Repo")
    # Chat with the GitHub Repo
    if prompt:
        answer = app.chat(prompt)
        st.write(answer)