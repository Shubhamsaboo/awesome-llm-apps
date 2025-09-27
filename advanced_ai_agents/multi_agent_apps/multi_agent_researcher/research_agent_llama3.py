# Import the required libraries
import streamlit as st
from agno.agent import Agent
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from agno.tools.newspaper4k import Newspaper4kTools
from agno.models.ollama import Ollama

# Set up the Streamlit app
st.title("Multi-Agent AI Researcher using Llama-3 🔍🤖")
st.caption("This app allows you to research top stories and users on HackerNews and write blogs, reports and social posts.")

# Create the specialized agents
hn_researcher = Agent(
    name="HackerNews Researcher",
    model=Ollama(id="llama3.2", max_tokens=1024),
    role="Gets top stories from hackernews.",
    tools=[HackerNewsTools()],
)

web_searcher = Agent(
    name="Web Searcher",
    model=Ollama(id="llama3.2", max_tokens=1024),
    role="Searches the web for information on a topic",
    tools=[DuckDuckGoTools()],
    add_datetime_to_instructions=True,
)

article_reader = Agent(
    name="Article Reader",
    model=Ollama(id="llama3.2", max_tokens=1024),
    role="Reads articles from URLs.",
    tools=[Newspaper4kTools()],
)

hackernews_team = Team(
    name="HackerNews Team",
    mode="coordinate",
    model=Ollama(id="llama3.2", max_tokens=1024),
    members=[hn_researcher, web_searcher, article_reader],
    instructions=[
        "First, search hackernews for what the user is asking about.",
        "Then, ask the article reader to read the links for the stories to get more information.",
        "Important: you must provide the article reader with the links to read.",
        "Then, ask the web searcher to search for each story to get more information.",
        "Finally, provide a thoughtful and engaging summary.",
    ],
    show_tool_calls=True,
    markdown=True,
    debug_mode=True,
    show_members_responses=True,
)

# Input field for the report query
query = st.text_input("Enter your report query")

if query:
    # Get the response from the assistant
    response = hackernews_team.run(query, stream=False)
    st.write(response.content)