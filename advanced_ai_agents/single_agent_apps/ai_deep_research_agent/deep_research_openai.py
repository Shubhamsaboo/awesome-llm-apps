import asyncio
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

import streamlit as st
from agents import Agent, Runner, set_default_openai_key
from agents.tool import function_tool
from firecrawl import FirecrawlApp

# ---------- Page ----------
st.set_page_config(page_title="OpenAI Deep Research Agent", page_icon="📘", layout="wide")

# ---------- Session defaults ----------
st.session_state.setdefault("openai_api_key", "")
st.session_state.setdefault("firecrawl_api_key", "")

# ---------- Sidebar ----------
with st.sidebar:
    st.title("API Configuration")

    openai_api_key = st.text_input("OpenAI API Key", value=st.session_state.openai_api_key, type="password")
    firecrawl_api_key = st.text_input("Firecrawl API Key", value=st.session_state.firecrawl_api_key, type="password")

    if openai_api_key:
        st.session_state.openai_api_key = openai_api_key
        set_default_openai_key(openai_api_key)

    if firecrawl_api_key:
        st.session_state.firecrawl_api_key = firecrawl_api_key

# ---------- Main ----------
st.title("📘 OpenAI Deep Research Agent")
st.markdown("Deep web research using Firecrawl search plus scrape, then an agentized write-up.")

# Research topic input
research_topic = st.text_input("Enter your research topic:", placeholder="e.g., Instant cross-border payouts in LATAM, last 30 days")

# ---------- Helpers ----------
def _host(u: str) -> str:
    try:
        return (urlparse(u).hostname or "").lower()
    except Exception:
        return ""

def _rank(url: str, title: str) -> int:
    h = _host(url)
    s = 0
    if any(k in h for k in ["news", "press", "blog"]): s += 3
    if any(x in (title or "") for x in ["2025", "2024", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]): s += 2
    return s

async def _safe_search(app: FirecrawlApp, q: str, limit: int, retries: int = 2):
    for i in range(retries + 1):
        try:
            return app.search(query=q, limit=limit)
        except Exception as e:
            msg = str(e)
            if "Rate limit" in msg or "rate limit" in msg:
                # simple backoff
                await asyncio.sleep(8 * (i + 1))
                continue
            return {"data": {"web": []}}
    return {"data": {"web": []}}

async def _safe_scrape(app: FirecrawlApp, url: str) -> str:
    try:
        doc = app.scrape(url=url, formats=["markdown"])
        if isinstance(doc, dict):
            return doc.get("data", {}).get("markdown") or doc.get("markdown") or ""
        return str(doc)
    except Exception:
        return ""

# ---------- Tool ----------
@function_tool
async def deep_research(query: str, max_depth: int, time_limit: int, max_urls: int) -> Dict[str, Any]:
    """
    Search, then scrape, then return curated materials with a Sources list.
    We do NOT use the deprecated firecrawl.deep_research.
    """
    try:
        firecrawl_app = FirecrawlApp(api_key=st.session_state.firecrawl_api_key)

        # 1) Search
        st.write("Searching the web…")
        # One primary query plus a light variant in case the first is thin
        queries = [query, f"{query} site:newsroom OR site:press"]
        seen, candidates = set(), []

        for q in queries:
            res = await _safe_search(firecrawl_app, q, limit=min(10, max_urls))
            items = res.get("data", {}).get("web") or res.get("web") or []
            for it in items:
                url = (it.get("url") or it.get("link") or "").strip()
                title = it.get("title") or url
                if not url or url in seen:
                    continue
                seen.add(url)
                candidates.append({"url": url, "title": title})

        if not candidates:
            return {"success": False, "error": "No search results", "sources": []}

        # 2) Rank and cap
        candidates.sort(key=lambda x: _rank(x["url"], x["title"]), reverse=True)
        candidates = candidates[:max_urls]

        # 3) Scrape
        st.write(f"Extracting content from up to {len(candidates)} pages…")
        sources: List[Dict[str, Any]] = []
        for c in candidates:
            url, title = c["url"], c["title"]
            low = url.lower()
            # Skip heavy JS calculators that usually break
            if any(x in low for x in ["/calculator", "/estimator", "/pricing", "/price"]):
                continue
            md = await _safe_scrape(firecrawl_app, url)
            if not md:
                continue
            sources.append({"url": url, "title": title, "markdown": md[:4000]})
            if len(sources) >= max_urls:
                break

        if not sources:
            return {"success": False, "error": "No readable sources", "sources": []}

        # 4) Show what we actually scraped
        st.success(f"Sources scraped: {len(sources)}")
        for i, s in enumerate(sources, 1):
            st.write(f"[{i}] {s['title']} — {s['url']}")

        # 5) Build materials for the agent with a numbered Sources list
        materials = "\n\n".join(
            f"# [{i}] {s['title']}\nSource: {s['url']}\n\n{s['markdown']}"
            for i, s in enumerate(sources, 1)
        )
        sources_list = "\n".join(f"[{i}] {s['title']} — {s['url']}" for i, s in enumerate(sources, 1))

        final = f"""### COLLECTED MATERIALS
Use ONLY the materials and Sources below. Do not invent sources.

Topic: {query}

{materials}

### Sources
{sources_list}
"""

        return {
            "success": True,
            "final_analysis": final,
            "sources_count": len(sources),
            "sources": [{"url": s["url"], "title": s["title"]} for s in sources],
        }

    except Exception as e:
        st.error(f"Deep research error: {str(e)}")
        return {"error": str(e), "success": False}

# ---------- Agents ----------
research_agent = Agent(
    name="research_agent",
    instructions=(
        "You are a research analyst. You will receive COLLECTED MATERIALS that include a numbered Sources list.\n"
        "Rules:\n"
        "1) Use ONLY the provided materials, do not add outside sources.\n"
        "2) Write a concise report with sections: Executive Summary, Key Developments, Implications, Watchlist.\n"
        "3) Every claim must cite a source inline like [n] that matches the Sources list.\n"
        "4) Prefer dated, first-party items. If a page has no date, state 'date unknown' and mark that line 'uncertain'."
    ),
    tools=[deep_research],
)

elaboration_agent = Agent(
    name="elaboration_agent",
    instructions=(
        "You are an editor. Improve clarity and structure of the report you are given.\n"
        "Keep all citations [n] intact and do not introduce new sources.\n"
        "Add concise phrasing, tighten bullets, and ensure sections are clearly separated.\n"
        "If something is uncertain, leave it marked as uncertain."
    ),
)

# ---------- Pipeline ----------
async def run_research_process(topic: str) -> str:
    # Step 1: Initial research
    with st.spinner("Conducting initial research…"):
        res = await Runner.run(research_agent, topic)
        initial_report = res.final_output

    with st.expander("View Initial Research Report"):
        st.markdown(initial_report)

    # Step 2: Editorial pass
    with st.spinner("Enhancing the report…"):
        elaboration_input = (
            "Use ONLY the text below and keep citations [n] intact.\n\n"
            f"{initial_report}"
        )
        res2 = await Runner.run(elaboration_agent, elaboration_input)
        enhanced = res2.final_output

    return enhanced

# ---------- UI action ----------
btn_enabled = bool(openai_api_key and firecrawl_api_key and research_topic)
if st.button("Start Research", disabled=not btn_enabled):
    if not openai_api_key:
        st.warning("Please enter your OpenAI API key.")
    elif not firecrawl_api_key:
        st.warning("Please enter your Firecrawl API key.")
    elif not research_topic:
        st.warning("Please enter a research topic.")
    else:
        try:
            output = asyncio.run(run_research_process(research_topic))
            st.markdown("## Enhanced Research Report")
            st.markdown(output)
            st.download_button(
                "Download Report",
                output,
                file_name=f"{research_topic.replace(' ', '_')}_report.md",
                mime="text/markdown",
            )
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

st.markdown("---")
st.markdown("Powered by OpenAI Agents SDK and Firecrawl")
