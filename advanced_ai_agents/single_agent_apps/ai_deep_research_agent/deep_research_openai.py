# === Deep Research Agent (Firecrawl search+scrape, date-window filter, strict citations) ===
import asyncio
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from datetime import datetime, timedelta

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
st.markdown("Search and scrape with Firecrawl, enforce a date window, then write a cited report using only scraped materials.")

research_topic = st.text_input("Enter your research topic:", placeholder="e.g., Instant cross border payouts in LATAM, last 60 days")

# ---------- Helpers (Python 3.9-safe) ----------
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

def _parse_iso_from_text(md: str) -> Optional[str]:
    """Return ISO 'YYYY-MM-DD' if a date is visible in text, else None."""
    if not md:
        return None
    m = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", md)
    if m:
        y, mo, d = m.groups()
        try:
            datetime(int(y), int(mo), int(d))
            return f"{y}-{mo}-{d}"
        except Exception:
            pass
    m = re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2}),\s+(20\d{2})\b", md, re.I)
    if m:
        mon_map = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,"jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}
        mon = mon_map[m.group(1).lower()]
        day = int(m.group(2)); year = int(m.group(3))
        try:
            dt = datetime(year, mon, day)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return None
    return None

def _window_days_from_query(q: str, default_days: int = 60) -> int:
    m = re.search(r"last\s+(\d{1,3})\s+days", q, re.I)
    return int(m.group(1)) if m else default_days

def _within_window(iso: Optional[str], days: int) -> bool:
    if not iso:
        return False
    try:
        dt = datetime.strptime(iso, "%Y-%m-%d")
    except Exception:
        return False
    return datetime.utcnow() - timedelta(days=days) <= dt <= datetime.utcnow()

# ---------- Tool ----------
@function_tool
async def deep_research(query: str, max_depth: int, time_limit: int, max_urls: int) -> Dict[str, Any]:
    """
    Firecrawl search + scrape, rank, date-window filter, and return materials + Sources.
    """
    try:
        if not st.session_state.firecrawl_api_key:
            return {"success": False, "error": "Missing Firecrawl API key", "sources": []}

        app = FirecrawlApp(api_key=st.session_state.firecrawl_api_key)

        # 1) Search with a primary and a newsroom-biased backup
        st.write("Searching…")
        queries = [query, f"{query} site:newsroom OR site:press"]
        seen, candidates = set(), []

        for q in queries:
            res = await _safe_search(app, q, limit=min(10, max_urls))
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
            if any(x in low for x in ["/calculator", "/estimator", "/pricing", "/price"]):
                continue
            md = await _safe_scrape(app, url)
            if not md:
                continue
            sources.append({"url": url, "title": title, "markdown": md[:5000]})
            if len(sources) >= max_urls:
                break

        if not sources:
            return {"success": False, "error": "No readable sources", "sources": []}

        # 4) Time-window filter
        days_window = _window_days_from_query(query, default_days=60)
        kept, dropped = [], []
        for s in sources:
            iso = _parse_iso_from_text(s.get("markdown", ""))
            s["iso_date"] = iso if iso else "date unknown"
            if _within_window(iso, days_window):
                kept.append(s)
            else:
                dropped.append(s)

        if kept:
            sources = kept
        else:
            # if everything is out of window, keep them but mark uncertain
            for s in sources:
                if "iso_date" not in s:
                    s["iso_date"] = "date unknown"
                s["uncertain"] = True

        st.caption(f"Time window: last {days_window} days; kept {len(sources)}, discarded {len(dropped)}")

        # 5) Show scraped sources
        st.success(f"Sources scraped: {len(sources)}")
        for i, s in enumerate(sources, 1):
            st.write(f"[{i}] {s['title']} — {s['url']} — {s.get('iso_date','date unknown')}{' (uncertain)' if s.get('uncertain') else ''}")

        # 6) Build materials and Sources list
        materials = "\n\n".join(
            f"# [{i}] {s['title']}\nSource: {s['url']} — {s.get('iso_date','date unknown')}{' (uncertain)' if s.get('uncertain') else ''}\n\n{s['markdown']}"
            for i, s in enumerate(sources, 1)
        )
        sources_list = "\n".join(
            f"[{i}] {s['title']} — {s['url']} — {s.get('iso_date','date unknown')}{' (uncertain)' if s.get('uncertain') else ''}"
            for i, s in enumerate(sources, 1)
        )

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
        "You will receive COLLECTED MATERIALS that include a numbered Sources list.\n"
        "Rules:\n"
        "1) Use ONLY those materials. Do not add outside links or facts.\n"
        "2) Write a concise, formal report with sections: Executive Summary, Key Developments, Implications, Watchlist.\n"
        "3) Every claim must cite inline like [n] mapping to the Sources list.\n"
        "4) Items marked '(uncertain)' or 'date unknown' may not appear in the Executive Summary.\n"
    ),
    tools=[deep_research],
)

elaboration_agent = Agent(
    name="elaboration_agent",
    instructions=(
        "Improve clarity and structure of the report you are given.\n"
        "Keep all [n] citations intact, do not modify the Sources list, and do not add new facts."
    ),
)

# ---------- Pipeline ----------
async def run_research_process(topic: str) -> str:
    with st.spinner("Conducting initial research…"):
        res = await Runner.run(research_agent, topic)
        initial_report = res.final_output

    with st.expander("View Initial Research Report"):
        st.markdown(initial_report)

    with st.spinner("Enhancing the report…"):
        elaboration_input = (
            "Edit for clarity and structure only. Keep all [n] citations and the Sources list exactly as-is.\n\n"
            f"{initial_report}"
        )
        res2 = await Runner.run(elaboration_agent, elaboration_input)
        enhanced = res2.final_output

    return enhanced

# ---------- UI action ----------
btn_enabled = bool(openai_api_key and firecrawl_api_key and research_topic)
if st.button("Start Research", disabled=not btn_enabled):
    if not openai_api_key:
        st.warning("Please enter your OpenAI API key."); st.stop()
    if not firecrawl_api_key:
        st.warning("Please enter your Firecrawl API key."); st.stop()
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
# === End ===
# ---------- Date utilities ----------
from datetime import date, datetime, timedelta
import re

def _parse_iso_from_text(md: str) -> Optional[date]:
    # Try ISO first
    m = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", md)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except:
            pass
    # Try Month Day, Year (Sep 12, 2025)
    m = re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2}),\s+(20\d{2})\b", md, re.I)
    if m:
        try:
            mon = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"].index(m.group(1).lower())+1
            return date(int(m.group(3)), mon, int(m.group(2)))
        except:
            pass
    return None

def _window_days_from_query(q: str, default_days: int = 60) -> int:
    m = re.search(r"last\s+(\d{1,3})\s+days", q, re.I)
    return int(m.group(1)) if m else default_days

def _within_window(d: Optional[date], days: int, today: Optional[date] = None) -> bool:
    if d is None:
        return False
    today = today or date.today()
    return today - timedelta(days=days) <= d <= today
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


        # --- Filter by time window based on the user's query ---
        days_window = _window_days_from_query(query, default_days=60)
        today = date.today()

        filtered = []
        discarded = []
        for s in sources:
            d = _parse_iso_from_text(s["markdown"])
            if _within_window(d, days_window, today):
                s["iso_date"] = d.isoformat()
                filtered.append(s)
            else:
                s["iso_date"] = d.isoformat() if d else "date unknown"
                discarded.append(s)

        # If filtering killed everything, fall back to original sources but mark them uncertain
        if filtered:
            sources = filtered
        else:
            for s in sources:
                if "iso_date" not in s:
                    d = _parse_iso_from_text(s["markdown"])
                    s["iso_date"] = d.isoformat() if d else "date unknown"
                s["uncertain"] = True

        st.caption(f"Time window: last {days_window} days")
        st.caption(f"Kept {len(sources)} source(s), discarded {len(discarded)} as out-of-window")

        # 5) Build materials for the agent with a numbered Sources list (with ISO date and uncertainty)
        materials = "\n\n".join(
            f"# [{i}] {s['title']}\nSource: {s['url']}\n\n{s['markdown']}"
            for i, s in enumerate(sources, 1)
        )
        sources_list = "\n".join(
            f"[{i}] {s['title']} — {s['url']} — {s.get('iso_date','date unknown')}{' (uncertain)' if s.get('uncertain') else ''}"
            for i, s in enumerate(sources, 1)
        )

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
        "4) Prefer dated, first-party items. If a page has no date, state 'date unknown' and mark that line 'uncertain'.\n"
        "Use ONLY the provided Sources. Do not alter or add to the Sources list. If a source is marked '(uncertain)' or 'date unknown', you may mention it only outside the Executive Summary. All summary bullets must cite in-window sources."
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
            "Do not modify the Sources list. Do not add new sources. Keep all [n] citations and their mapping to Sources.\n\n"
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
