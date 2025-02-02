# Import the required libraries
import streamlit as st
from agno.agent import Agent
from agno.tools.hackernews import HackerNewsTools
from agno.models.openai import OpenAIChat

# Set up the Streamlit app
st.title("Multi-Agent AI Researcher 🔍🤖")
st.caption("This app allows you to research top stories and users on HackerNews and write blogs, reports and social posts.")

# Get OpenAI API key from user
openai_api_key = st.text_input("OpenAI API Key", type="password")

if openai_api_key:
    # Create instances of the Assistant
    story_researcher = Agent(
        name="HackerNews Story Researcher",
        role="Researches hackernews stories and users.",
        tools=[HackerNewsTools()],
    )

    user_researcher = Agent(
        name="HackerNews User Researcher",
        role="Reads articles from URLs.",
        tools=[HackerNewsTools()],
    )

    hn_assistant = Agent(
        name="Hackernews Team",
        team=[story_researcher, user_researcher],
        model=OpenAIChat(
            id="gpt-4o",
            max_tokens=1024,
            temperature=0.5,
            api_key=openai_api_key
        )
    )

    # Input field for the report query
    query = st.text_input("Enter your report query")

    if query:
        # Get the response from the assistant
        response = hn_assistant.run(query, stream=False)
        st.write(response.content)