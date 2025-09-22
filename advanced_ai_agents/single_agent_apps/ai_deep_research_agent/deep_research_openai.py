import asyncio
import streamlit as st
from typing import Dict, Any, List
from agents import Agent, Runner, trace
from agents import set_default_openai_key
from firecrawl import FirecrawlApp
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

# Replace the entire deep_research tool with this
@function_tool
async def deep_research(query: str, max_depth: int, time_limit: int, max_urls: int) -> Dict[str, Any]:
    """
    Perform comprehensive web research using Firecrawl by combining Search and Scrape.
    This replaces the old deep_research call that is not available in current SDKs.
    """
    try:
        firecrawl_app = FirecrawlApp(api_key=st.session_state.firecrawl_api_key)

        # 1) Search for relevant pages
        st.write("Searching the web...")
        search = firecrawl_app.search(query=query, limit=max_urls)

        # Normalize possible return shapes
        web_results: List[Dict[str, Any]] = []
        if isinstance(search, dict):
            if "data" in search and isinstance(search["data"], dict) and "web" in search["data"]:
                web_results = search["data"]["web"]
            elif "web" in search:
                web_results = search["web"]
        elif isinstance(search, list):
            web_results = search

        if not web_results:
            return {"success": False, "error": "No search results", "sources": []}

        # 2) Scrape each result to get content
        st.write(f"Found {len(web_results)} candidates. Extracting content...")
        sources = []
        for item in web_results[:max_urls]:
            try:
                url = item.get("url") if isinstance(item, dict) else str(item)
                if not url:
                    continue
                doc = firecrawl_app.scrape(url=url, formats=["markdown"])

                # Normalize markdown field
                if isinstance(doc, dict):
                    md = doc.get("data", {}).get("markdown") or doc.get("markdown") or ""
                else:
                    md = str(doc)

                title = item.get("title", url) if isinstance(item, dict) else url
                sources.append({"url": url, "title": title, "markdown": md})
                st.write(f"Scraped: {title}")
            except Exception as e:
                st.write(f"Skipping one URL due to error: {e}")
                continue

        if not sources:
            return {"success": False, "error": "Could not scrape any sources", "sources": []}

        # 3) Build an initial report string for the agent pipeline
        joined = "\n\n".join(
            f"# {s['title']}\nSource: {s['url']}\n\n{s['markdown'][:4000]}"
            for s in sources
        )

        initial_report = f"""
You are a precise research writer. Read the sources and produce an "Initial Research Report" for the topic.

Topic: {query}

Include:
- Executive Summary with 5 to 7 bullets
- Key developments and examples with short evidence
- Practical implications for consumers, SMEs, and banks
- Inline citations like [1], [2] that match a Sources list at the end

Sources:
{joined}
"""

        return {
            "success": True,
            "final_analysis": initial_report,
            "sources_count": len(sources),
            "sources": [{"url": s["url"], "title": s["title"]} for s in sources],
        }

    except Exception as e:
        st.error(f"Deep research error: {str(e)}")
        return {"error": str(e), "success": False}


# Keep the original agents
research_agent = Agent(
    name="research_agent",
    instructions="""You are a research assistant that can perform deep web research on any topic.

    When given a research topic or question:
    1. Use the deep_research tool to gather comprehensive information
       - Always use these parameters:
         * max_depth: 3 (for moderate depth)
         * time_limit: 180 (3 minutes)
         * max_urls: 10 (sufficient sources)
    2. The tool will search the web, analyze multiple sources, and provide a synthesis
    3. Review the research results and organize them into a well-structured report
    4. Include proper citations for all sources
    5. Highlight key findings and insights
    """,
    tools=[deep_research]
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