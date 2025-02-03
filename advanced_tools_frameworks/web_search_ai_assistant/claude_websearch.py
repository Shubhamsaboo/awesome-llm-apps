# Import the required libraries
import streamlit as st
from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.models.anthropic import Claude

# Set up the Streamlit app
st.title("Claude Sonnet + AI Web Search 🤖")
st.caption("This app allows you to search the web using Claude Sonnet 3.5")

# Get Anthropic API key from user
anthropic_api_key = st.text_input("Anthropic's Claude API Key", type="password")

# If Anthropic API key is provided, create an instance of Assistant
if anthropic_api_key:
    assistant = Agent(
    model=Claude(
        id="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        temperature=0.3,
        api_key=anthropic_api_key) , tools=[DuckDuckGoTools()], show_tool_calls=True
    )
    # Get the search query from the user
    query= st.text_input("Enter the Search Query", type="default")
    
    if query:
        # Search the web using the AI Assistant
        response = assistant.run(query, stream=False)
        st.write(response.content)