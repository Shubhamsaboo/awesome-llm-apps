# Import the required libraries
import streamlit as st
from phi.assistant import Assistant
from phi.tools.hackernews import HackerNews
from phi.llm.ollama import Ollama

# Set up the Streamlit app
st.title("Multi-Agent AI Researcher using Llama-3 🔍🤖")
st.caption("This app allows you to research top stories and users on HackerNews and write blogs, reports and social posts.")

# Create instances of the Assistant
story_researcher = Assistant(
    name="HackerNews Story Researcher",
    role="Researches hackernews stories and users.",
    tools=[HackerNews()],
    llm=Ollama(model="llama3:instruct", max_tokens=1024)
)

user_researcher = Assistant(
    name="HackerNews User Researcher",
    role="Reads articles from URLs.",
    tools=[HackerNews()],
    llm=Ollama(model="llama3:instruct", max_tokens=1024)
)

hn_assistant = Assistant(
    name="Hackernews Team",
    team=[story_researcher, user_researcher],
    llm=Ollama(model="llama3:instruct", max_tokens=1024)
)

# Input field for the report query
query = st.text_input("Enter your report query")

if query:
    # Get the response from the assistant
    response = hn_assistant.run(query, stream=False)
    st.write(response)