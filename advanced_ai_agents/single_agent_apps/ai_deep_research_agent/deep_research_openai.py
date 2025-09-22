from typing import Any

async def plan_queries(topic: str) -> dict[str, Any]:
    "Use the global OpenAI client to produce diverse web search queries and site hints."
    import json
    try:
        if client is None:
            return {"queries": [topic], "hints": [], "language": "en"}
        sys = "You are a research query planner. Output compact JSON only."
        user = f"Topic: {topic}\nProduce JSON with keys: queries, hints, language.\nRules: return 8 to 12 diverse queries, some site-neutral and some site-specific, at least 2 with time windows like 'last 30 days' or exact dates; each query under 120 characters."
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":sys},{"role":"user","content":user}],
            temperature=0.2
        )
        txt = resp.choices[0].message.content.strip()
        data = json.loads(txt)
        if not isinstance(data.get("queries", []), list):
            data["queries"] = [topic]
        data.setdefault("hints", [])
        data.setdefault("language", "en")
        return data
    except Exception:
        return {"queries": [topic], "hints": [], "language": "en"}

import asyncio
import streamlit as st
from typing import Dict, Any, List
from agents import Agent, Runner, trace
from agents import set_default_openai_key
from firecrawl import FirecrawlApp
from agents.tool import function_tool
from openai import OpenAI

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

    # --- Search options controls ---
    st.subheader("Search options")
    st.session_state["allow_any_domain"] = st.checkbox("Open Search Mode", value=True)
    st.session_state["max_pages"] = st.number_input("Max pages", min_value=6, max_value=25, value=12, step=1)
    st.session_state["start_date"] = st.date_input("Start date", value=None)
    st.session_state["end_date"] = st.date_input("End date", value=None)

    st.text_area(
        "Domains to search (one per line)",
        value="visa.com/newsroom\nmastercard.com/news\nswift.com/news\nbis.org\nimf.org\nfatf-gafi.org\necb.europa.eu\nbanxico.org.mx\nwise.com\nremitly.com\nwesternunion.com",
        key="domains_text",
        height=120
    )

    dom_count = len([l for l in st.session_state["domains_text"].splitlines() if l.strip()])
    window = ""
    if st.session_state["start_date"] and st.session_state["end_date"]:
        window = f"  Window: {st.session_state['start_date']} to {st.session_state['end_date']}"
    st.caption(f"Domains loaded: {dom_count}.{window}")

# Inserted OpenAI client block
import os
from openai import OpenAI

# Ensure both the OpenAI client and the Agents SDK see the key
if st.session_state.openai_api_key:
    os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key
    st.caption("OpenAI key prefix: " + st.session_state.openai_api_key[:8] + "…")
    st.caption("Model: gpt-4o-mini")
    client = OpenAI(api_key=st.session_state.openai_api_key)
else:
    client = None

# Main content
st.title("📘 OpenAI Deep Research Agent")
st.markdown("This OpenAI Agent from the OpenAI Agents SDK performs deep research on any topic using Firecrawl")

# Research topic input
research_topic = st.text_input("Enter your research topic:", placeholder="e.g., Latest developments in AI")

async def plan_queries(topic: str) -> Dict[str, Any]:
    "Use OpenAI to produce diverse search queries and site hints."
    import json
    try:
        if client is None:
            return {"queries": [topic], "hints": [], "language": "en"}
        sys = "You are a research query planner. Output compact JSON only."
        user = f"Topic: {topic}\nProduce JSON with keys: queries, hints, language.\nRules: return 8 to 12 diverse queries, some site-neutral and some site-specific, at least 2 with time windows like 'last 30 days' or exact dates; each query under 120 chars."
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":sys},{"role":"user","content":user}],
            temperature=0.2
        )
        txt = resp.choices[0].message.content.strip()
        data = json.loads(txt)
        if not isinstance(data.get("queries", []), list):
            data["queries"] = [topic]
        data.setdefault("hints", [])
        data.setdefault("language", "en")
        return data
    except Exception:
        return {"queries": [topic], "hints": [], "language": "en"}

# Replace the entire deep_research tool with this
@function_tool
async def deep_research(query: str, max_depth: int, time_limit: int, max_urls: int) -> Dict[str, Any]:
    """
    Perform comprehensive web research using Firecrawl by combining Search and Scrape.
    Uses OpenAI to plan queries, supports open/closed search, time window, ranking, and strict citation rules.
    """
    from urllib.parse import urlparse
    def host_of(u: str) -> str:
        try: return (urlparse(u).hostname or "").lower()
        except: return ""
    def score_item(url: str, title: str, hints: list) -> int:
        h = host_of(url)
        s = 0
        if any(k in h for k in ["news","press","blog"]): s += 3
        if any(x in (title or "") for x in ["2025","2024","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]): s += 2
        if any(hint in h for hint in planned.get("hints", [])): s += 1
        return s
    try:
        # 1) Read user settings
        allow_any = bool(st.session_state.get("allow_any_domain", True))
        max_pages = int(st.session_state.get("max_pages", 12))
        domains_text = st.session_state.get("domains_text", "")
        start_date = st.session_state.get("start_date")
        end_date = st.session_state.get("end_date")

        firecrawl_app = FirecrawlApp(api_key=st.session_state.firecrawl_api_key)

        # 2) Call the planner
        planned = await plan_queries(query)

        # 3) Build queries_to_run
        if allow_any:
            queries_to_run = planned["queries"]
            if start_date and end_date:
                time_hint = f" after:{start_date} before:{end_date}"
                queries_to_run = [q + time_hint for q in queries_to_run[:4]] + queries_to_run[4:]
        else:
            doms = [d.strip() for d in domains_text.splitlines() if d.strip()]
            queries_to_run = [f"{query} site:{d}" for d in doms]
            if not doms:
                st.warning("No domains provided, enable Open Search Mode or add domains")
                return {"success": False, "error": "No domains", "sources": []}

        # 4) Run Firecrawl search for each query, deduplicate by URL
        st.write("Searching the web...")
        web_results = []
        seen_urls = set()
        for q in queries_to_run:
            try:
                search = firecrawl_app.search(query=q, limit=min(5, max_pages))
                items = []
                if isinstance(search, dict):
                    if "data" in search and isinstance(search["data"], dict) and "web" in search["data"]:
                        items = search["data"]["web"]
                    elif "web" in search:
                        items = search["web"]
                elif isinstance(search, list):
                    items = search
                for item in items:
                    url = item.get("url") if isinstance(item, dict) else str(item)
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    web_results.append(item)
            except Exception as e:
                st.write(f"Search error for query '{q}': {e}")
                continue

        if not web_results:
            return {"success": False, "error": "No search results", "sources": []}

        # 5) Rank results before scraping
        hints = planned.get("hints", [])
        def get_url_title(item):
            if isinstance(item, dict):
                return item.get("url", ""), item.get("title", "")
            return str(item), str(item)
        scored = sorted(web_results, key=lambda item: score_item(*get_url_title(item), hints), reverse=True)
        scored = scored[:max_pages]

        # 6) Scrape each result to get content (cap at max_pages, skip unwanted paths)
        st.write(f"Found {len(scored)} candidates. Extracting content...")
        sources = []
        for item in scored:
            if len(sources) >= max_pages:
                break
            try:
                url = item.get("url") if isinstance(item, dict) else str(item)
                if not url:
                    continue
                path = urlparse(url).path.lower()
                if any(x in path for x in ["calculator", "estimator", "pricing", "price"]):
                    continue
                doc = firecrawl_app.scrape(url=url, formats=["markdown"])
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

        # 7) Print sources summary
        st.success(f"Sources scraped: {len(sources)}")
        for i, s in enumerate(sources, 1):
            st.write(f"[{i}] {s['title']} — {s['url']}")

        # 8) Build an initial report string for the agent pipeline
        joined = "\n\n".join(
            f"# {s['title']}\nSource: {s['url']}\n\n{s['markdown'][:4000]}"
            for s in sources
        )

        initial_report = f"""
You are a research analyst. Use ONLY the scraped materials below.
Every claim must have an inline citation like [n] that maps to the Sources list.
Extract an ISO date from each page; if none is visible write 'date unknown' and mark that line 'uncertain'.
Do not invent sources or facts.

Topic: {query}

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
    instructions="""
You are a research analyst. Use ONLY the scraped materials provided by the deep_research tool.
Every claim must have an inline citation like [n] that maps to the Sources list at the end.
Prefer dated, first-party items. If a source has no visible date, state 'date unknown' and mark that line 'uncertain'.
Do not invent sources or facts. Do not use any information not present in the scraped materials.
Organize your report with clear sections and keep citations consistent.
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
    # OpenAI test call
    try:
        if client:
            ping = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Say OK in one word."},
                    {"role": "user", "content": "Ping"}
                ],
                temperature=0
            )
            st.caption("OpenAI test response: " + ping.choices[0].message.content)
    except Exception as e:
        st.warning(f"OpenAI test failed: {e}")

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

        Please enhance this research report by adding clarity, detail, and examples, but you must:
        - Keep all existing citations ([n]) and do not remove or change them.
        - Do not introduce any new sources or facts not present in the original report.
        - The Sources list must remain unchanged.
        - If you add new sentences, cite them to the correct [n] as in the original.
        - Your job is to elaborate and clarify, not to add new information.
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