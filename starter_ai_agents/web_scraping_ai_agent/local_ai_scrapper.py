# Import the required libraries
import asyncio
import sys
import time

import streamlit as st
from scrapegraphai.graphs import SmartScraperGraph

# Streamlit sets the Selector event loop on Windows, which can't spawn the
# Playwright browser subprocess; switch back to the Proactor loop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Set up the Streamlit app
st.title("Web Scrapping AI Agent 🕵️‍♂️")
st.caption("This app allows you to scrape a website using Llama 3.2")

# Set up the configuration for the SmartScraperGraph
graph_config = {
    "llm": {
        "model": "ollama/llama3.2:latest",
        "temperature": 0,
        "format": "json",  # Ollama needs the format to be specified explicitly
        "base_url": "http://localhost:11434",  # set Ollama URL
    },
    "embeddings": {
        "model": "ollama/nomic-embed-text",
        "base_url": "http://localhost:11434",  # set Ollama URL
    },
    "verbose": True,
}
# Get the URL of the website to scrape
url = st.text_input("Enter the URL of the website you want to scrape")
# Get the user prompt
user_prompt = st.text_input("What you want the AI agent to scrape from the website?")

# Friendly labels for the SmartScraperGraph steps
STEP_LABELS = {
    "Fetch": "🌐 Loading the page in the browser",
    "ParseNode": "✂️ Splitting the page into chunks",
    "GenerateAnswer": "🤖 Asking Llama 3.2 to extract the data",
}


def track_progress(graph, status):
    """Wrap each graph node so the status box shows which step is running."""
    for node in graph.graph.nodes:
        label = STEP_LABELS.get(node.node_name, node.node_name)

        def execute(state, _run=node.execute, _label=label):
            status.update(label=f"{_label}...")
            start = time.time()
            result = _run(state)
            status.write(f"✅ {_label} ({time.time() - start:.1f}s)")
            return result

        node.execute = execute


# Scrape the website
if st.button("Scrape"):
    if not url or not user_prompt:
        st.warning("Please enter both a URL and what you want to scrape.")
    else:
        # Create a SmartScraperGraph object
        smart_scraper_graph = SmartScraperGraph(
            prompt=user_prompt,
            source=url,
            config=graph_config
        )
        with st.status("Starting the scraper...", expanded=True) as status:
            track_progress(smart_scraper_graph, status)
            start = time.time()
            try:
                result = smart_scraper_graph.run()
            except Exception as e:
                status.update(label="Scraping failed", state="error")
                st.exception(e)
                st.stop()
            status.update(
                label=f"Done in {time.time() - start:.1f}s", state="complete", expanded=False
            )
        st.write(result)
