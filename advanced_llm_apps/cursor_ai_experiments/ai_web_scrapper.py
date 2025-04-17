import streamlit as st
from scrapegraphai.graphs import SmartScraperGraph

# Streamlit app title
st.title("AI Web Scraper")

# Input fields for user prompt and source URL
prompt = st.text_input("Enter the information you want to extract:")
source_url = st.text_input("Enter the source URL:")

# Input field for OpenAI API key
api_key = st.text_input("Enter your OpenAI API key:", type="password")

# Configuration for the scraping pipeline
graph_config = {
    "llm": {
        "api_key": api_key,
        "model": "openai/gpt-4o-mini",
    },
    "verbose": True,
    "headless": False,
}

# Button to start the scraping process
if st.button("Scrape"):
    if prompt and source_url and api_key:
        # Create the SmartScraperGraph instance
        smart_scraper_graph = SmartScraperGraph(
            prompt=prompt,
            source=source_url,
            config=graph_config
        )

        # Run the pipeline
        result = smart_scraper_graph.run()

        # Display the result
        st.write(result)
    else:
        st.error("Please provide all the required inputs.")

# Instructions for the user
st.markdown("""
### Instructions
1. Enter the information you want to extract in the first input box.
2. Enter the source URL from which you want to extract the information.
3. Enter your OpenAI API key.
4. Click on the "Scrape" button to start the scraping process.
""")