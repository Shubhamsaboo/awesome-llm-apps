# Import the required libraries
import streamlit as st
from phi.assistant import Assistant
from phi.llm.ollama import Ollama
from phi.tools.arxiv_toolkit import ArxivToolkit

# Set up the Streamlit app
st.title("Chat with Research Papers 🔎🤖")
st.caption("This app allows you to chat with arXiv research papers using Llama-3 running locally.")

# Create an instance of the Assistant
assistant = Assistant(
llm=Ollama(
    model="llama3:instruct") , tools=[ArxivToolkit()], show_tool_calls=True
)

# Get the search query from the user
query= st.text_input("Enter the Search Query", type="default")

if query:
    # Search the web using the AI Assistant
    response = assistant.run(query, stream=False)
    st.write(response)