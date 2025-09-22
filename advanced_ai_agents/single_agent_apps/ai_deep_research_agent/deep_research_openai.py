import os, json, time, asyncio, requests
from typing import Any, Dict, List
from urllib.parse import urlparse

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
    tavily_api_key = st.text_input("Tavily API Key", value=st.session_state.get("tavily_api_key",""), type="password")
    if tavily_api_key:
        st.session_state["tavily_api_key"] = tavily_api_key
        st.caption("Tavily enabled")

    if openai_api_key:
        st.session_state.openai_api_key = openai_api_key
        set_default_openai_key(openai_api_key)
    if firecrawl_api_key:
        st.session_state.firecrawl_api_key = firecrawl_api_key

    st.subheader("Search options")
    st.session_state["allow_any_domain"] = st.checkbox("Open Search Mode", value=True)
    st.session_state["max_pages"] = st.number_input("Max pages", min_value=6, max_value=25, value=12, step=1)
    st.session_state["start_date"] = st.text_input("Start date (YYYY-MM-DD)", value=st.session_state.get("start_date",""))
    st.session_state["end_date"] = st.text_input("End date (YYYY-MM-DD)", value=st.session_state.get("end_date",""))
    st.session_state["domains_text"] = st.text_area(
        "Domains to search (one per line)",
        value=st.session_state.get("domains_text","visa.com/newsroom\nmastercard.com/news\nswift.com/news\nbis.org\nimf.org\nfatf-gafi.org\necb.europa.eu\nbanxico.org.mx\nwise.com\nremitly.com\nwesternunion.com"),
        height=120
    )
    dom_count = len([l for l in st.session_state["domains_text"].splitlines() if l.strip()])
    win = ""
    if st.session_state["start_date"] and st.session_state["end_date"]:
        win = f"  Window: {st.session_state['start_date']} to {st.session_state['end_date']}"
    st.caption(f"Domains loaded: {dom_count}.{win}")
# --- Helper functions ---
def host_of(u: str) -> str:
    try:
        return (urlparse(u).hostname or "").lower()
    except:
        return ""

def _rank_score(url: str, title: str) -> int:
    h = host_of(url)
    s = 0
    if any(k in h for k in ["news","press","blog"]): s += 3
    if any(x in (title or "") for x in ["2025","2024","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]): s += 2
    return s

def tavily_search(topic: str, max_results: int = 12, days: int | None = None, api_key: str | None = None) -> List[Dict[str, Any]]:
    """
    Use Tavily Search API to get results with content snippets.
    Returns a list of dicts: {url, title, content}
    """
    if not api_key:
        return []
    try:
        payload = {
            "api_key": api_key,
            "query": topic,
            "include_answer": False,
            "max_results": max_results,
            "include_raw_content": False,
            "search_depth": "advanced"
        }
        if days is not None:
            payload["days"] = days
        r = requests.post("https://api.tavily.com/search", json=payload, timeout=25)
        r.raise_for_status()
        data = r.json()
        out = []
        for it in data.get("results", []) or []:
            url = it.get("url")
            if not url:
                continue
            out.append({
                "url": url,
                "title": it.get("title") or url,
                "content": it.get("content") or ""
            })
        return out
    except Exception:
        return []

async def safe_search_firecrawl(app, q: str, limit: int, retries: int = 2):
    for i in range(retries + 1):
        try:
            return app.search(query=q, limit=limit)
        except Exception as e:
            msg = str(e)
            if "Rate limit" in msg or "rate limit" in msg:
                await asyncio.sleep(12 * (i + 1))
                continue
            return {"data":{"web":[]}}
    return {"data":{"web":[]}}

# Inserted OpenAI client block
import os
from openai import OpenAI

# Ensure both the OpenAI client and the Agents SDK see the key

# Set OpenAI environment variables for both OpenAI and Agents SDK
if st.session_state.openai_api_key:
    os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key
    os.environ["AGENTS_PROVIDER"] = "openai"
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
    Perform comprehensive web research using Tavily as primary, Firecrawl as fallback, with strict caps and formal cited output.
    """
    try:
        # Read user settings
        allow_any = bool(st.session_state.get("allow_any_domain", True))
        max_pages = int(st.session_state.get("max_pages", 12))
        start_date = st.session_state.get("start_date", "")
        end_date = st.session_state.get("end_date", "")
        domains_text = st.session_state.get("domains_text", "")
        tavily_key = st.session_state.get("tavily_api_key")

        # 4a) Build a human-readable topic string with optional dates from sidebar
        topic_hint = query
        days = None
        try:
            if start_date and end_date and len(start_date)==10 and len(end_date)==10:
                from datetime import date
                sd = date.fromisoformat(start_date); ed = date.fromisoformat(end_date)
                days = max(1, (ed - sd).days)
        except Exception:
            days = None

        # 4b) Try Tavily first
        st.write("Searching with Tavily...")
        tavily_hits = tavily_search(topic_hint, max_results=max_pages, days=days, api_key=tavily_key)

        # De-dupe and rank Tavily results
        seen, candidates = set(), []
        for it in tavily_hits:
            u = it["url"].strip()
            if u and u not in seen:
                seen.add(u)
                candidates.append({"url": u, "title": it["title"], "content": it.get("content","")})

        candidates.sort(key=lambda x: _rank_score(x["url"], x["title"]), reverse=True)
        candidates = candidates[:max_pages]

        # 4c) If Tavily is empty, fall back to Firecrawl with strict caps
        if not candidates:
            st.write("Tavily returned no usable results, falling back to Firecrawl...")
            firecrawl_app = FirecrawlApp(api_key=st.session_state.firecrawl_api_key)
            MAX_SEARCH_CALLS = 6
            PER_QUERY_LIMIT = 3
            search_calls = 0

            if allow_any:
                queries_to_run = [query]
                if start_date and end_date:
                    queries_to_run.append(f"{query} after:{start_date} before:{end_date}")
            else:
                doms = [d.strip() for d in domains_text.splitlines() if d.strip()]
                if not doms:
                    st.warning("No domains provided, enable Open Search Mode or add domains")
                    return {"success": False, "error": "No domains", "sources": []}
                queries_to_run = [f"{query} site:{d}" for d in doms]

            web_results: List[Dict[str, Any]] = []
            for q in queries_to_run[:MAX_SEARCH_CALLS]:
                res = await safe_search_firecrawl(firecrawl_app, q, PER_QUERY_LIMIT)
                search_calls += 1
                items = res.get("data", {}).get("web") or res.get("web") or res
                for it in items or []:
                    url = (it.get("url") or it.get("link") or str(it)).strip()
                    if url and url not in seen:
                        seen.add(url)
                        web_results.append({"url": url, "title": it.get("title", url)})

            # simple press-wire fallback if still empty
            if not web_results:
                for fq in [f"{query} site:prnewswire.com", f"{query} site:businesswire.com", f"{query} site:globenewswire.com", f"{query} site:reuters.com"]:
                    res = await safe_search_firecrawl(firecrawl_app, fq, PER_QUERY_LIMIT)
                    items = res.get("data", {}).get("web") or res.get("web") or res
                    for it in items or []:
                        url = (it.get("url") or it.get("link") or str(it)).strip()
                        if url and url not in seen:
                            seen.add(url)
                            web_results.append({"url": url, "title": it.get("title", url)})

            # rank Firecrawl candidates
            web_results.sort(key=lambda x: _rank_score(x["url"], x["title"]), reverse=True)
            candidates = web_results[:max_pages]

        # 4d) Extract content, prefer Tavily content, else Firecrawl scrape
        sources: List[Dict[str, Any]] = []
        firecrawl_app = firecrawl_app if 'firecrawl_app' in locals() else FirecrawlApp(api_key=st.session_state.firecrawl_api_key)
        st.write(f"Extracting content from up to {len(candidates)} pages...")
        for c in candidates:
            url, title = c["url"], c["title"]
            # skip known JS-heavy calculator pages
            if any(x in url.lower() for x in ["/calculator", "/estimator", "/pricing", "/price"]):
                continue
            text = c.get("content","") or ""
            if not text:
                try:
                    doc = firecrawl_app.scrape(url=url, formats=["markdown"])
                    text = (doc.get("data", {}).get("markdown") or doc.get("markdown") or "") if isinstance(doc, dict) else str(doc)
                except Exception:
                    continue
            if not text:
                continue
            sources.append({"url": url, "title": title, "markdown": text[:4000]})
            if len(sources) >= max_pages:
                break

        if not sources:
            return {"success": False, "error": "No readable sources", "sources": []}

        # 4e) Visible summary for the user
        st.success(f"Sources scraped: {len(sources)}")
        for i, s in enumerate(sources, 1):
            st.write(f"[{i}] {s['title']} — {s['url']}")

        # 4f) Build materials and strict instructions
        materials = "\n\n".join(f"# [{i}] {s['title']}\nSource: {s['url']}\n\n{s['markdown']}" for i, s in enumerate(sources, 1))
        bibliography = "\n".join(f"[{i}] {s['title']} — {s['url']}" for i, s in enumerate(sources, 1))

        initial_materials = f"""### COLLECTED MATERIALS
Use ONLY the materials and Sources below. Do not invent sources.

Topic: {query}

Output a formal report with sections:
- Executive Summary
- Key Developments
- Implications for stakeholders
- Watchlist

Rules:
- Every claim must have an inline citation like [n] that maps to the Sources list.
- Extract an ISO date from each page. If no visible date, write "date unknown" and mark that line "uncertain".
- Keep it concise and factual.

{materials}

### Sources
{bibliography}
"""

        return {
            "success": True,
            "final_analysis": initial_materials,
            "sources_count": len(sources),
            "sources": [{"url": s["url"], "title": s["title"]} for s in sources],
        }

    except Exception as e:
        st.error(f"Deep research error: {str(e)}")
        return {"error": str(e), "success": False}


# Keep the original agents

research_agent = Agent(
    name="research_agent",
    model="gpt-4o-mini",
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
    model="gpt-4o-mini",
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



    # OpenAI sanity ping: visible 200-token completion
    if client:
        try:
            test = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Write exactly 150 tokens of the letter A."},
                    {"role": "user", "content": "Go"}
                ],
                temperature=0
            )
            st.caption("OpenAI sanity ping model: gpt-4o-mini, approx tokens: ~150")
        except Exception as e:
            st.warning(f"OpenAI sanity ping failed: {e}")

    # Step 1: Initial Research
    with st.spinner("Conducting initial research..."):
        research_result = await Runner.run(research_agent, topic)
        try:
            m = getattr(research_result, "model", "unknown")
            u = getattr(research_result, "usage", None)
            st.caption(f"Research model: {m}")
            if u:
                st.caption(f"Research tokens — prompt: {u.get('prompt_tokens')}, output: {u.get('completion_tokens')}, total: {u.get('total_tokens')}")
        except Exception:
            pass
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
        try:
            m = getattr(elaboration_result, "model", "unknown")
            u = getattr(elaboration_result, "usage", None)
            st.caption(f"Elaboration model: {m}")
            if u:
                st.caption(f"Elaboration tokens — prompt: {u.get('prompt_tokens')}, output: {u.get('completion_tokens')}, total: {u.get('total_tokens')}")
        except Exception:
            pass
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