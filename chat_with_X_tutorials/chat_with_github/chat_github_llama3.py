# Import the required libraries
import tempfile
from embedchain import App
from embedchain.loaders.github import GithubLoader
import streamlit as st
import os

GITHUB_TOKEN = os.getenv("Your GitHub Token")

def get_loader():
    loader = GithubLoader(
        config={
            "token": GITHUB_TOKEN
        }
    )
    return loader

if "loader" not in st.session_state:
    st.session_state['loader'] = get_loader()

loader = st.session_state.loader

# Define the embedchain_bot function
def embedchain_bot(db_path):
    return App.from_config(
        config={
            "llm": {"provider": "ollama", "config": {"model": "llama3:instruct", "max_tokens": 250, "temperature": 0.5, "stream": True, "base_url": 'http://localhost:11434'}},
            "vectordb": {"provider": "chroma", "config": {"dir": db_path}},
            "embedder": {"provider": "ollama", "config": {"model": "llama3:instruct", "base_url": 'http://localhost:11434'}},
        }
    )

def load_repo(git_repo):
    global app
    # Add the repo to the knowledge base
    print(f"Adding {git_repo} to knowledge base!")
    app.add("repo:" + git_repo + " " + "type:repo", data_type="github", loader=loader)
    st.success(f"Added {git_repo} to knowledge base!")


def make_db_path():
    ret = tempfile.mkdtemp(suffix="chroma")
    print(f"Created Chroma DB at {ret}")    
    return ret

# Create Streamlit app
st.title("Chat with GitHub Repository 💬")
st.caption("This app allows you to chat with a GitHub Repo using Llama-3 running with Ollama")

# Initialize the Embedchain App
if "app" not in st.session_state:
    st.session_state['app'] = embedchain_bot(make_db_path())

app = st.session_state.app

# Get the GitHub repo from the user
git_repo = st.text_input("Enter the GitHub Repo", type="default")

if git_repo and ("repos" not in st.session_state or git_repo not in st.session_state.repos):
    if "repos" not in st.session_state:
        st.session_state["repos"] = [git_repo]
    else:
        st.session_state.repos.append(git_repo)
    load_repo(git_repo)


# Ask a question about the Github Repo
prompt = st.text_input("Ask any question about the GitHub Repo")
# Chat with the GitHub Repo
if prompt:
    answer = st.session_state.app.chat(prompt)
    st.write(answer)