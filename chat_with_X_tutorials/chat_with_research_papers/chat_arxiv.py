# Import the required libraries
import streamlit as st
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.arxiv import ArxivTools

# Set up the Streamlit app
st.title("Chat with Research Papers 🔎🤖")
st.caption("This app allows you to chat with arXiv research papers using OpenAI GPT-4o model.")

# Get OpenAI API key from user
openai_access_token = st.text_input("OpenAI API Key", type="password")

# If OpenAI API key is provided, create an instance of Assistant
if openai_access_token:
    # Create an instance of the Assistant
    assistant = Agent(
    model=OpenAIChat(
        id="gpt-4o",
        max_tokens=1024,
        temperature=0.9,
        api_key=openai_access_token) , tools=[ArxivTools()]
    )

    # Get the search query from the user
    query= st.text_input("Enter the Search Query", type="default")
    
    if query:
        # Search the web using the AI Assistant
        response = assistant.run(query, stream=False)
        st.write(response.content)