# Import necessary libraries
import os
import tempfile
import streamlit as st
from embedchain import App

# Define the embedchain_bot function
def embedchain_bot(db_path):
    return App.from_config(
        config={
            "llm": {"provider": "ollama", "config": {"model": "llama3:instruct", "max_tokens": 250, "temperature": 0.5, "stream": True, "base_url": 'http://localhost:11434'}},
            "vectordb": {"provider": "chroma", "config": {"dir": db_path}},
            "embedder": {"provider": "ollama", "config": {"model": "llama3:instruct", "base_url": 'http://localhost:11434'}},
        }
    )

st.title("Chat with PDF")
st.caption("This app allows you to chat with a PDF using Llama3 running locally wiht Ollama!")

# Create a temporary directory to store the PDF file
db_path = tempfile.mkdtemp()
# Create an instance of the embedchain App
app = embedchain_bot(db_path)

# Upload a PDF file
pdf_file = st.file_uploader("Upload a PDF file", type="pdf")

# If a PDF file is uploaded, add it to the knowledge base
if pdf_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        f.write(pdf_file.getvalue())
        app.add(f.name, data_type="pdf_file")
    os.remove(f.name)
    st.success(f"Added {pdf_file.name} to knowledge base!")

# Ask a question about the PDF
prompt = st.text_input("Ask a question about the PDF")
# Display the answer
if prompt:
    answer = app.chat(prompt)
    st.write(answer)