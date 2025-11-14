"""
ScrapeGraph AI Interactive Streamlit App
Comprehensive web scraping interface with all features
"""

import streamlit as st
from scrapegraph_py import Client
import json
import os
from typing import Optional
import time


def init_client() -> Optional[Client]:
    """Initialize ScrapeGraph AI client."""
    api_key = st.session_state.get("api_key") or os.getenv("SGAI_API_KEY")
    
    if not api_key:
        st.error("❌ Please enter your ScrapeGraph AI API key")
        st.info("Get your API key at: https://scrapegraphai.com")
        return None
    
    try:
        client = Client(api_key=api_key)
        # Try to get credits to verify key
        balance = client.get_credits()
        st.sidebar.success(f"💳 Credits: {balance.credits}")
        return client
    except Exception as e:
        st.error(f"❌ Error initializing client: {e}")
        return None


def smart_scraper_tab(client: Client):
    """SmartScraper interface."""
    st.header("🤖 SmartScraper")
    st.markdown("Extract structured data from websites using natural language")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        url = st.text_input("Website URL", placeholder="https://example.com")
    
    with col2:
        render_js = st.checkbox("Render JavaScript", help="Enable for SPAs")
    
    prompt = st.text_area(
        "What to extract?",
        placeholder="Extract product names, prices, and availability",
        height=100
    )
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        use_html = st.checkbox("Use HTML input instead of URL")
        
        if use_html:
            html_content = st.text_area("HTML Content", height=200)
        
        use_schema = st.checkbox("Define output schema")
        
        if use_schema:
            schema_input = st.text_area(
                "JSON Schema",
                value='{\n  "type": "object",\n  "properties": {\n    "items": {"type": "array"}\n  }\n}',
                height=200
            )
        
        stealth = st.checkbox("Enable stealth mode")
    
    if st.button("🚀 Extract Data", key="smart_scraper_btn"):
        if not prompt:
            st.error("Please enter an extraction prompt")
            return
        
        if not use_html and not url:
            st.error("Please enter a URL")
            return
        
        if use_html and not html_content:
            st.error("Please enter HTML content")
            return
        
        with st.spinner("Extracting data..."):
            try:
                # Prepare parameters
                params = {
                    "user_prompt": prompt,
                    "render_heavy_js": render_js,
                }
                
                if use_html:
                    params["website_html"] = html_content
                else:
                    params["website_url"] = url
                
                if use_schema:
                    try:
                        params["output_schema"] = json.loads(schema_input)
                    except json.JSONDecodeError:
                        st.error("Invalid JSON schema")
                        return
                
                if stealth:
                    params["stealth"] = True
                
                # Make request
                response = client.smartscraper(**params)
                
                # Display results
                st.success("✅ Data extracted successfully!")
                
                st.subheader("📊 Results")
                st.json(response.result)
                
                # Download button
                st.download_button(
                    label="💾 Download JSON",
                    data=json.dumps(response.result, indent=2),
                    file_name="scraped_data.json",
                    mime="application/json"
                )
                
            except Exception as e:
                st.error(f"❌ Error: {e}")


def search_scraper_tab(client: Client):
    """SearchScraper interface."""
    st.header("🔍 SearchScraper")
    st.markdown("AI-powered web search with structured results")
    
    query = st.text_area(
        "Search Query",
        placeholder="Find the top 5 AI news websites with descriptions",
        height=100
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        num_results = st.slider("Number of results", 1, 10, 5)
    
    with col2:
        use_schema = st.checkbox("Define result schema")
    
    if use_schema:
        schema_input = st.text_area(
            "JSON Schema",
            value='{\n  "type": "object",\n  "properties": {\n    "results": {"type": "array"}\n  }\n}',
            height=200
        )
    
    if st.button("🔍 Search", key="search_btn"):
        if not query:
            st.error("Please enter a search query")
            return
        
        with st.spinner("Searching..."):
            try:
                params = {
                    "user_prompt": query,
                    "num_results": num_results
                }
                
                if use_schema:
                    try:
                        params["output_schema"] = json.loads(schema_input)
                    except json.JSONDecodeError:
                        st.error("Invalid JSON schema")
                        return
                
                response = client.smartscraper(**params)
                
                st.success("✅ Search completed!")
                
                st.subheader("📊 Results")
                st.json(response.result)
                
                st.download_button(
                    label="💾 Download Results",
                    data=json.dumps(response.result, indent=2),
                    file_name="search_results.json",
                    mime="application/json"
                )
                
            except Exception as e:
                st.error(f"❌ Error: {e}")


def markdownify_tab(client: Client):
    """Markdownify interface."""
    st.header("📝 Markdownify")
    st.markdown("Convert any webpage to clean markdown")
    
    url = st.text_input("Website URL", placeholder="https://example.com/article")
    
    render_js = st.checkbox("Render JavaScript", help="Enable for SPAs")
    
    if st.button("🔄 Convert to Markdown", key="markdown_btn"):
        if not url:
            st.error("Please enter a URL")
            return
        
        with st.spinner("Converting..."):
            try:
                response = client.markdownify(
                    website_url=url,
                    render_heavy_js=render_js
                )
                
                st.success("✅ Converted successfully!")
                
                st.subheader("📄 Markdown Output")
                st.code(response.result, language="markdown")
                
                st.download_button(
                    label="💾 Download Markdown",
                    data=response.result,
                    file_name="content.md",
                    mime="text/markdown"
                )
                
            except Exception as e:
                st.error(f"❌ Error: {e}")


def smart_crawler_tab(client: Client):
    """SmartCrawler interface."""
    st.header("🕷️ SmartCrawler")
    st.markdown("Intelligently crawl and extract from multiple pages")
    
    st.warning("⚠️ SmartCrawler is asynchronous and may take several minutes")
    
    url = st.text_input("Start URL", placeholder="https://example.com")
    
    prompt = st.text_area(
        "What to extract?",
        placeholder="Extract all page titles and descriptions",
        height=100
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        max_pages = st.number_input("Max pages", 1, 100, 10)
    
    with col2:
        depth = st.number_input("Crawl depth", 1, 5, 2)
    
    with col3:
        same_domain = st.checkbox("Same domain only", value=True)
    
    col_mode1, col_mode2 = st.columns(2)
    
    with col_mode1:
        extraction_mode = st.selectbox("Mode", ["ai", "markdown"])
    
    if st.button("🚀 Start Crawler", key="crawler_btn"):
        if not url:
            st.error("Please enter a URL")
            return
        
        with st.spinner("Starting crawler..."):
            try:
                params = {
                    "url": url,
                    "extraction_mode": extraction_mode,
                    "max_pages": max_pages,
                    "depth": depth,
                    "same_domain_only": same_domain
                }
                
                if extraction_mode == "ai" and prompt:
                    params["prompt"] = prompt
                
                request_id = client.smartcrawler(**params)
                
                st.success(f"✅ Crawler started!")
                st.info(f"Request ID: `{request_id}`")
                
                st.markdown("### ⏳ Fetching results...")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Poll for results
                max_attempts = 30
                for i in range(max_attempts):
                    try:
                        results = client.smartcrawler_get(request_id)
                        
                        if results:
                            progress_bar.progress(100)
                            status_text.success("✅ Crawl completed!")
                            
                            st.subheader("📊 Results")
                            st.json(results)
                            
                            st.download_button(
                                label="💾 Download Results",
                                data=json.dumps(results, indent=2),
                                file_name="crawl_results.json",
                                mime="application/json"
                            )
                            break
                    except Exception as e:
                        if "not ready" in str(e).lower():
                            progress = int((i + 1) / max_attempts * 100)
                            progress_bar.progress(progress)
                            status_text.text(f"Processing... ({i + 1}/{max_attempts})")
                            time.sleep(2)
                        else:
                            raise
                else:
                    st.warning("⏰ Crawler is still processing. Check back later with the request ID.")
                
            except Exception as e:
                st.error(f"❌ Error: {e}")


def main():
    st.set_page_config(
        page_title="ScrapeGraph AI SDK",
        page_icon="🕷️",
        layout="wide"
    )
    
    st.title("🕷️ ScrapeGraph AI SDK")
    st.markdown("Intelligent web scraping powered by AI")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        api_key = st.text_input(
            "API Key",
            type="password",
            value=os.getenv("SGAI_API_KEY", ""),
            help="Get your API key at scrapegraphai.com"
        )
        
        if api_key:
            st.session_state.api_key = api_key
        
        st.markdown("---")
        
        st.markdown("### 🔗 Links")
        st.markdown("[GitHub](https://github.com/ScrapeGraphAI/scrapegraph-sdk)")
        st.markdown("[Documentation](https://docs.scrapegraphai.com)")
        st.markdown("[Get API Key](https://scrapegraphai.com)")
        
        st.markdown("---")
        
        st.markdown("### 💡 Features")
        st.markdown("""
        - 🤖 SmartScraper
        - 🔍 SearchScraper
        - 📝 Markdownify
        - 🕷️ SmartCrawler
        """)
    
    # Initialize client
    client = init_client()
    
    if not client:
        st.info("👆 Please enter your API key in the sidebar to get started")
        return
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🤖 SmartScraper",
        "🔍 SearchScraper",
        "📝 Markdownify",
        "🕷️ SmartCrawler"
    ])
    
    with tab1:
        smart_scraper_tab(client)
    
    with tab2:
        search_scraper_tab(client)
    
    with tab3:
        markdownify_tab(client)
    
    with tab4:
        smart_crawler_tab(client)


if __name__ == "__main__":
    main()

