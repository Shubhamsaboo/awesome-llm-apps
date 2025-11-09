# Import the required libraries
from textwrap import dedent
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.tools.serpapi import SerpApiTools
from agno.tools.newspaper4k import Newspaper4kTools
import streamlit as st
from agno.models.openai import OpenAIChat

# Set up the Streamlit app
st.title("AI Journalist Agent 🗞️")
st.caption("Generate High-quality articles with AI Journalist by researching, wriritng and editing quality articles on autopilot using GPT-4o")

# Get OpenAI API key from user
openai_api_key = st.text_input("Enter OpenAI API Key to access GPT-4o", type="password")

# Get SerpAPI key from the user
serp_api_key = st.text_input("Enter Serp API Key for Search functionality", type="password")

if openai_api_key and serp_api_key:
    searcher = Agent(
        name="Searcher",
        role="Searches for top URLs based on a topic",
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        description=dedent(
            """\
        You are a world-class journalist for the New York Times. Given a topic, generate a list of 3 search terms
        for writing an article on that topic. Then search the web for each term, analyse the results
        and return the 10 most relevant URLs.
        """
        ),
        instructions=[
            "Given a topic, first generate a list of 3 search terms related to that topic.",
            "For each search term, `search_google` and analyze the results."
            "From the results of all searcher, return the 10 most relevant URLs to the topic.",
            "Remember: you are writing for the New York Times, so the quality of the sources is important.",
        ],
        tools=[SerpApiTools(api_key=serp_api_key)],
        add_datetime_to_context=True,
    )
    writer = Agent(
        name="Writer",
        role="Retrieves text from URLs and writes a high-quality article",
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        description=dedent(
            """\
        You are a senior writer for the New York Times. Given a topic and a list of URLs,
        your goal is to write a high-quality NYT-worthy article on the topic.
        """
        ),
        instructions=[
            "Given a topic and a list of URLs, first read the article using `get_article_text`."
            "Then write a high-quality NYT-worthy article on the topic."
            "The article should be well-structured, informative, and engaging",
            "Ensure the length is at least as long as a NYT cover story -- at a minimum, 15 paragraphs.",
            "Ensure you provide a nuanced and balanced opinion, quoting facts where possible.",
            "Remember: you are writing for the New York Times, so the quality of the article is important.",
            "Focus on clarity, coherence, and overall quality.",
            "Never make up facts or plagiarize. Always provide proper attribution.",
        ],
        tools=[Newspaper4kTools()],
        add_datetime_to_context=True,
        markdown=True,
    )

    editor = Agent(
        name="Editor",
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        team=[searcher, writer],
        description="You are a senior NYT editor. Given a topic, your goal is to write a NYT worthy article.",
        instructions=[
            "Given a topic, ask the search journalist to search for the most relevant URLs for that topic.",
            "Then pass a description of the topic and URLs to the writer to get a draft of the article.",
            "Edit, proofread, and refine the article to ensure it meets the high standards of the New York Times.",
            "The article should be extremely articulate and well written. "
            "Focus on clarity, coherence, and overall quality.",
            "Ensure the article is engaging and informative.",
            "Remember: you are the final gatekeeper before the article is published.",
        ],
        add_datetime_to_context=True,
        markdown=True,
    )

    # Input field for the report query
    query = st.text_input("What do you want the AI journalist to write an Article on?")

    if query:
        with st.spinner("Processing..."):
            # Get the response from the assistant
            response: RunOutput = editor.run(query, stream=False)
            st.write(response.content)