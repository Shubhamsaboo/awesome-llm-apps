# Import the required libraries
import streamlit as st
from phi.assistant import Assistant
from phi.llm.openai import OpenAIChat
from phi.tools.arxiv_toolkit import ArxivToolkit

# Set up the Streamlit app
st.title("Chat with Research Papers 🔎🤖")
st.caption("This app allows you to chat with arXiv research papers using OpenAI GPT-4o model.")

# Get OpenAI API key from user
openai_access_token = st.text_input("OpenAI API Key", type="password")

# If OpenAI API key is provided, create an instance of Assistant
if openai_access_token:
    # Create an instance of the Assistant
    assistant = Assistant(
    llm=OpenAIChat(
        model="gpt-4o",
        max_tokens=1024,
        temperature=0.9,
        api_key=openai_access_token) , tools=[ArxivToolkit()]
    )

    # Get the search query from the user
    query= st.text_input("Enter the Search Query", type="default")
    
    if query:
        # Search the web using the AI Assistant
        response = assistant.run(query, stream=False)
        st.write(response)