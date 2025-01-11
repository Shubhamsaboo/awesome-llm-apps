import streamlit as st
from exa_py import Exa
from phi.agent import Agent
from phi.tools.firecrawl import FirecrawlTools
from phi.model.openai import OpenAIChat
from phi.tools.duckduckgo import DuckDuckGo

# Streamlit UI
st.set_page_config(page_title="AI Competitor Intelligence Agent", layout="wide")

# Sidebar for API keys
st.sidebar.title("API Keys")
openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
firecrawl_api_key = st.sidebar.text_input("Firecrawl API Key", type="password")
exa_api_key = st.sidebar.text_input("Exa API Key", type="password")

# Store API keys in session state
if openai_api_key and firecrawl_api_key and exa_api_key:
    st.session_state.openai_api_key = openai_api_key
    st.session_state.firecrawl_api_key = firecrawl_api_key
    st.session_state.exa_api_key = exa_api_key
else:
    st.sidebar.warning("Please enter all API keys to proceed.")

# Main UI
st.title("AI Competitor Intelligence Agent")
st.info(
    """
    This app helps businesses analyze their competitors by extracting structured data from competitor websites and generating insights using AI.
    - Provide a **URL** or a **description** of your company.
    - The app will fetch competitor URLs, extract relevant information, and generate a detailed analysis report.
    """
)

# Input fields for URL and description
url = st.text_input("Enter your company URL (optional):")
description = st.text_area("Enter a description of your company (if URL is not available):")

# Initialize API keys and tools
if "openai_api_key" in st.session_state and "firecrawl_api_key" in st.session_state and "exa_api_key" in st.session_state:
    exa = Exa(api_key=st.session_state.exa_api_key)

    firecrawl_tools = FirecrawlTools(
        api_key=st.session_state.firecrawl_api_key,
        scrape=False,
        crawl=True,
        limit=5
    )

    firecrawl_agent = Agent(
        model=OpenAIChat(id="gpt-4", api_key=st.session_state.openai_api_key),
        tools=[firecrawl_tools, DuckDuckGo()],
        show_tool_calls=True,
        markdown=True
    )

    analysis_agent = Agent(
        model=OpenAIChat(id="gpt-4", api_key=st.session_state.openai_api_key),
        show_tool_calls=True,
        markdown=True
    )

    def get_competitor_urls(url=None, description=None):
        if url:
            result = exa.find_similar(
                url=url,
                num_results=3,
                exclude_source_domain=True,
                category="company"
            )
        elif description:
            result = exa.search(
                description,
                type="neural",
                category="company",
                use_autoprompt=True,
                num_results=3
            )
        else:
            raise ValueError("Please provide either a URL or a description.")
        
        competitor_urls = [item.url for item in result.results]
        return competitor_urls

    def extract_competitor_info(competitor_url: str):
        try:
            crawl_response = firecrawl_agent.run(f"Crawl and summarize {competitor_url}")
            crawled_data = crawl_response.content
            
            structured_info = firecrawl_agent.run(
                f"""Extract the following information from the crawled data:
                - Product pricing and features: Extract exact pricing numbers from their pricing page.
                - Technology stack information
                - Marketing messaging/positioning
                - Customer testimonials/case studies
                - Latest news and developments (use DuckDuckGo to search for the latest news and developments)

                Crawled Data:
                {crawled_data}
                """
            )
            
            return {
                "competitor": competitor_url,
                "data": structured_info.content
            }
        except Exception as e:
            return {
                "competitor": competitor_url,
                "error": str(e)
            }

    def generate_analysis_report(competitor_data: list):
        combined_data = "\n\n".join([str(data) for data in competitor_data])
        
        report = analysis_agent.run(
            f"""Analyze the following competitor data and identify market opportunities to improve my own company:
            {combined_data}

            Tasks:
            1. Identify market gaps and opportunities based on competitor offerings
            2. Analyze competitor weaknesses that we can capitalize on
            3. Recommend unique features or capabilities we should develop
            4. Suggest pricing and positioning strategies to gain competitive advantage
            5. Outline specific growth opportunities in underserved market segments
            6. Provide actionable recommendations for product development and go-to-market strategy

            Focus on finding opportunities where we can differentiate and do better than competitors.
            Highlight any unmet customer needs or pain points we can address.
            """
        )
        return report.content

    # Run analysis when the user clicks the button
    if st.button("Analyze Competitors"):
        if url or description:
            with st.spinner("Fetching competitor URLs..."):
                competitor_urls = get_competitor_urls(url=url, description=description)
                st.write(f"Competitor URLs: {competitor_urls}")
            
            competitor_data = []
            for url in competitor_urls:
                with st.spinner(f"Analyzing Competitor: {url}..."):
                    competitor_info = extract_competitor_info(url)
                    competitor_data.append(competitor_info)
            
            with st.spinner("Generating analysis report..."):
                analysis_report = generate_analysis_report(competitor_data)
            
            st.success("Analysis complete!")
            st.subheader("Competitor Analysis Report")
            st.markdown(analysis_report)
        else:
            st.error("Please provide either a URL or a description.")