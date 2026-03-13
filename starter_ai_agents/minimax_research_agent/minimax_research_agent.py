from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
import streamlit as st

st.title("AI Research Agent with MiniMax")
st.caption("Research any topic using MiniMax M2.5 with 204K context window and DuckDuckGo search")

minimax_api_key = st.text_input("Enter MiniMax API Key", type="password")

if minimax_api_key:
    researcher = Agent(
        name="MiniMax Research Agent",
        role="Researches topics by searching the web and synthesizing findings into comprehensive reports",
        model=OpenAIChat(
            id="MiniMax-M2.5",
            api_key=minimax_api_key,
            base_url="https://api.minimax.io/v1",
        ),
        tools=[DuckDuckGoTools()],
        instructions=[
            "Search the web for the given topic using multiple relevant queries.",
            "Analyze and cross-reference the search results.",
            "Produce a well-structured research report with key findings, supporting evidence, and sources.",
            "Use markdown formatting with headers, bullet points, and tables where appropriate.",
        ],
        show_tool_calls=True,
        markdown=True,
    )

    topic = st.text_input("Enter a research topic")

    if st.button("Research"):
        with st.spinner("Researching your topic with MiniMax M2.5..."):
            response = researcher.run(topic, stream=False)
            st.markdown(response.content)
