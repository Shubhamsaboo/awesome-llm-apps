# Import the required libraries
import streamlit as st
from langchain_openai import ChatOpenAI
from scrapegraphai.graphs import SmartScraperGraph

# Set up the Streamlit app
st.title("Web Scrapping AI Agent 🕵️‍♂️")
st.caption("This app allows you to scrape a website using OpenRouter free models")

# Get OpenRouter API key from user
openrouter_api_key = st.text_input("OpenRouter API Key", type="password")

if openrouter_api_key:
    # Free models, live-checked via https://openrouter.ai/api/v1/models
    # openrouter/free auto-routes to a working free model (most resilient).
    FREE_MODELS = [
        "openrouter/free",
        "google/gemma-4-26b-a4b-it:free",
        "google/gemma-4-31b-it:free",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "nvidia/nemotron-3-ultra-550b-a55b:free",
        "nex-agi/nex-n2.5-pro:free",
    ]
    model = st.selectbox(
        "Select the model",
        FREE_MODELS,
        index=0,
    )
    llm = ChatOpenAI(
        model=model,
        api_key=openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0,
        default_headers={
            "HTTP-Referer": "https://github.com/tushar-hatwar/awesome-llm-apps_test",
            "X-Title": "Web Scraping AI Agent",
        },
    )
    graph_config = {
        "llm": {
            "model_instance": llm,
            "model_tokens": 32000,
        },
    }
    # Get the URL of the website to scrape
    url = st.text_input("Enter the URL of the website you want to scrape")
    # Get the user prompt
    user_prompt = st.text_input("What you want the AI agent to scrape from the website?")
    
    # Create a SmartScraperGraph object
    smart_scraper_graph = SmartScraperGraph(
        prompt=user_prompt,
        source=url,
        config=graph_config
    )
    # Scrape the website
    if st.button("Scrape"):
        result = smart_scraper_graph.run()
        st.write(result)