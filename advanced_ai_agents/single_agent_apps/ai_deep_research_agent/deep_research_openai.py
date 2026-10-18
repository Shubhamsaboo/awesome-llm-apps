import asyncio
import streamlit as st
from typing import Dict, Any, List
from agents import Agent, Runner, trace
from agents import set_default_openai_key
from firecrawl import AsyncFirecrawl
from firecrawl.types import Document, ScrapeOptions
from agents.tool import function_tool

# Set page configuration
st.set_page_config(
    page_title="OpenAI Deep Research Agent",
    page_icon="📘",
    layout="wide"
)

# Initialize session state for API keys if not exists
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = ""
if "firecrawl_api_key" not in st.session_state:
    st.session_state.firecrawl_api_key = ""

# Sidebar for API keys
with st.sidebar:
    st.title("API Configuration")
    openai_api_key = st.text_input(
        "OpenAI API Key", 
        value=st.session_state.openai_api_key,
        type="password"
    )
    firecrawl_api_key = st.text_input(
        "Firecrawl API Key", 
        value=st.session_state.firecrawl_api_key,
        type="password"
    )
    
    if openai_api_key:
        st.session_state.openai_api_key = openai_api_key
        set_default_openai_key(openai_api_key)
    if firecrawl_api_key:
        st.session_state.firecrawl_api_key = firecrawl_api_key

# Main content
st.title("📘 OpenAI Deep Research Agent")
st.markdown("This OpenAI Agent from the OpenAI Agents SDK performs deep research on any topic using Firecrawl")

# Research topic input
research_topic = st.text_input("Enter your research topic:", placeholder="e.g., Latest developments in AI")

# Firecrawl search tool: finds sources and returns each page as markdown
@function_tool
async def search_web(query: str) -> Dict[str, Any]:
    """
    Search the web with Firecrawl and return the title, URL and page content of the top 5 results.
    """
    try:
        # Initialize Firecrawl with the API key from session state
        firecrawl_app = AsyncFirecrawl(api_key=st.session_state.firecrawl_api_key, origin="awesome-llm-apps")

        # Search and scrape the result pages in one call
        with st.spinner(f"Searching: {query}"):
            results = await firecrawl_app.search(
                query,
                limit=5,
                scrape_options=ScrapeOptions(formats=["markdown"], only_main_content=True)
            )

        sources = []
        for result in results.web or []:
            if isinstance(result, Document):  # page was scraped
                meta = result.metadata
                title = meta.title if meta else None
                url = (meta.url or meta.source_url) if meta else None
                content = result.markdown or ""
            else:  # page could not be scraped, keep the search snippet
                title, url, content = result.title, result.url, result.description or ""
            if url:
                # Truncate each page so the agent's context stays bounded
                sources.append({"title": title, "url": url, "content": content[:4000]})

        st.write(f"[search] {query}: {len(sources)} sources")
        return {
            "success": True,
            "sources_count": len(sources),
            "sources": sources
        }
    except Exception as e:
        st.error(f"Search error: {str(e)}")
        return {"error": str(e), "success": False}

# Keep the original agents
research_agent = Agent(
    name="research_agent",
    instructions="""You are a research assistant that can perform deep web research on any topic.

    When given a research topic or question:
    1. Break the topic into 3 to 5 focused search queries that cover different angles
    2. Use the search_web tool for each query
       - Each result includes the page title, URL and page content
       - Run follow-up searches if the first results leave gaps
       - Run at most 6 searches in total
    3. Read and compare the sources, then organize the findings into a well-structured report
    4. Include proper citations (title and URL) for all sources
    5. Highlight key findings and insights
    """,
    tools=[search_web]
)

elaboration_agent = Agent(
    name="elaboration_agent",
    instructions="""You are an expert content enhancer specializing in research elaboration.

    When given a research report:
    1. Analyze the structure and content of the report
    2. Enhance the report by:
       - Adding more detailed explanations of complex concepts
       - Including relevant examples, case studies, and real-world applications
       - Expanding on key points with additional context and nuance
       - Adding visual elements descriptions (charts, diagrams, infographics)
       - Incorporating latest trends and future predictions
       - Suggesting practical implications for different stakeholders
    3. Maintain academic rigor and factual accuracy
    4. Preserve the original structure while making it more comprehensive
    5. Ensure all additions are relevant and valuable to the topic
    """
)

async def run_research_process(topic: str):
    """Run the complete research process."""
    # Step 1: Initial Research
    with st.spinner("Conducting initial research..."):
        research_result = await Runner.run(research_agent, topic)
        initial_report = research_result.final_output
    
    # Display initial report in an expander
    with st.expander("View Initial Research Report"):
        st.markdown(initial_report)
    
    # Step 2: Enhance the report
    with st.spinner("Enhancing the report with additional information..."):
        elaboration_input = f"""
        RESEARCH TOPIC: {topic}
        
        INITIAL RESEARCH REPORT:
        {initial_report}
        
        Please enhance this research report with additional information, examples, case studies, 
        and deeper insights while maintaining its academic rigor and factual accuracy.
        """
        
        elaboration_result = await Runner.run(elaboration_agent, elaboration_input)
        enhanced_report = elaboration_result.final_output
    
    return enhanced_report

# Main research process
if st.button("Start Research", disabled=not (openai_api_key and firecrawl_api_key and research_topic)):
    if not openai_api_key or not firecrawl_api_key:
        st.warning("Please enter both API keys in the sidebar.")
    elif not research_topic:
        st.warning("Please enter a research topic.")
    else:
        try:
            # Create placeholder for the final report
            report_placeholder = st.empty()
            
            # Run the research process
            enhanced_report = asyncio.run(run_research_process(research_topic))
            
            # Display the enhanced report
            report_placeholder.markdown("## Enhanced Research Report")
            report_placeholder.markdown(enhanced_report)
            
            # Add download button
            st.download_button(
                "Download Report",
                enhanced_report,
                file_name=f"{research_topic.replace(' ', '_')}_report.md",
                mime="text/markdown"
            )
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Powered by OpenAI Agents SDK and Firecrawl") 