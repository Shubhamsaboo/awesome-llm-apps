import streamlit as st
from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools
import os

# Streamlit App Title
st.title("AI Agent with Agno and Gemini Thinking")

# Sidebar for API Key Input
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter your Google API Key", type="password")
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key

# File/URL Upload Section
st.sidebar.header("Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload a document", type=["txt", "pdf", "jpg", "png"])
web_url = st.sidebar.text_input("Enter a web URL")

# Initialize the Agent
if api_key:
    thinking_agent = Agent(
        name="Thinking Agent",
        role="Think about the problem",
        model=Gemini(id="gemini-2.0-flash-exp", api_key=api_key),
        instructions="Given the problem, think about it and provide a detailed explanation",
        show_tool_calls=True,
        markdown=True,
    )

    # Chat Interface
    st.header("Chat with the Agent")
    user_input = st.text_input("Ask a question or describe the problem:")

    if user_input:
        # Process the user's input
        if uploaded_file:
            # Handle file upload
            file_content = uploaded_file.read()
            st.write("File content:", file_content)
            # Add logic to process the file content with the agent
            response = thinking_agent.run(f"Given this file content: {file_content}, answer: {user_input}")
        elif web_url:
            # Handle web URL
            st.write("Web URL:", web_url)
            # Add logic to process the web URL with the agent
            response = thinking_agent.run(f"Given this web URL: {web_url}, answer: {user_input}")
        else:
            # Handle normal chat
            response = thinking_agent.run(user_input)

        # Display the response
        st.write("Agent's Response:")
        st.write(response.content)
else:
    st.warning("Please enter your Google API Key in the sidebar to proceed.")