import streamlit as st
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.models.google import Gemini
from agno.tools.newspaper4k import Newspaper4kTools

# Setting up Streamlit app
st.title("AI Startup Trend Analysis Agent 📈")
st.caption("Get the latest trend analysis and startup opportunities based on your topic of interest in a click!.")

topic = st.text_input("Enter the area of interest for your Startup:")
google_api_key = st.sidebar.text_input("Enter Google API Key", type="password")

if st.button("Generate Analysis"):
    if not google_api_key:
        st.warning("Please enter the required API key.")
    else:
        with st.spinner("Processing your request..."):
            try:
                # Initialize Gemini model
                gemini_model = Gemini(id="gemini-2.5-flash", api_key=google_api_key)

                # Define News Collector Agent - Duckduckgo_search tool enables an Agent to search the web for information.
                search_tool = DuckDuckGoTools()
                news_collector = Agent(
                    name="News Collector",
                    role="Collects recent news articles on the given topic",
                    tools=[search_tool],
                    model=gemini_model,
                    instructions=["Gather latest articles on the topic"],
                    markdown=True,
                )

                # Define Summary Writer Agent
                news_tool = Newspaper4kTools(enable_read_article=True, include_summary=True)
                summary_writer = Agent(
                    name="Summary Writer",
                    role="Summarizes collected news articles",
                    tools=[news_tool],
                    model=gemini_model,
                    instructions=["Provide concise summaries of the articles"],
                    markdown=True,
                )

                # Define Trend Analyzer Agent
                trend_analyzer = Agent(
                    name="Trend Analyzer",
                    role="Analyzes trends from summaries",
                    model=gemini_model,
                    instructions=["Identify emerging trends and startup opportunities"],
                    markdown=True,
                )

                # Executing the workflow
                # Step 1: Collect news
                news_response: RunOutput = news_collector.run(f"Collect recent news on {topic}")
                articles = news_response.content

                # Step 2: Summarize articles
                summary_response: RunOutput = summary_writer.run(f"Summarize the following articles:\n{articles}")
                summaries = summary_response.content

                # Step 3: Analyze trends
                trend_response: RunOutput = trend_analyzer.run(f"Analyze trends from the following summaries:\n{summaries}")
                analysis = trend_response.content

                # Display results - if incase you want to use this furthur, you can uncomment the below 2 lines to get the summaries too!
                # st.subheader("News Summaries")
                # # st.write(summaries)

                st.subheader("Trend Analysis and Potential Startup Opportunities")
                st.write(analysis)

            except Exception as e:
                st.error(f"An error occurred: {e}")
else:
    st.info("Enter the topic and API keys, then click 'Generate Analysis' to start.")
