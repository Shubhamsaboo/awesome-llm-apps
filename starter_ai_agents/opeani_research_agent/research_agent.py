"""
Research Agent Backend
Implements the Deep Search (API-first) flow.
No Streamlit imports. This file can be imported safely.
"""

import datetime
from urllib.parse import urlparse

from .tools.search_perplexity import search_perplexity
from .tools.search_tavily import search_tavily
from .tools.fetch_firecrawl import fetch_firecrawl

# --- Helpers ------------------------------------------------------------

def host_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""

def infer_region(url: str, text: str) -> str:
    h = host_of(url)
    if any(t in h for t in [".mx", ".br", ".ar", ".cl", ".pe", ".co"]):
        return "AMER"
    if any(t in h for t in [".eu", ".de", ".fr", ".it", ".es", ".uk"]):
        return "EMEA"
    if any(t in h for t in [".jp", ".sg", ".hk", ".au", ".in"]):
        return "APAC"
    return "GLOBAL"

def iso_or_none(s: str | None) -> str | None:
    if not s:
        return None
    try:
        return datetime.date.fromisoformat(s[:10]).isoformat()
    except Exception:
        return None

# --- Main Deep Search ---------------------------------------------------

def deep_search_api_first(topic: str, days: int = 90, max_items: int = 8) -> dict:
    """
    Run Perplexity + Tavily + Firecrawl pipeline and return structured results.
    """
    queries = []
    subangles = ["regulation policy", "rails networks", "product launches", "funding M&A"]
    now = datetime.date.today()
    for sub in subangles:
        queries.append(f"{topic} {sub} last {days} days")
        queries.append(f"{topic} {sub} {now.strftime('%B %Y')}")
        queries.append(f"{topic} {sub} site:reuters.com")
        queries.append(f"{topic} {sub} site:europa.eu")

    # COLLECT
    results = []
    search_log = []
    for q in queries:
        perpl = search_perplexity(q, max_results=5)
        tavy = search_tavily(q, max_results=5)
        all_res = (perpl or []) + (tavy or [])
        search_log.append({"query": q, "results": all_res})
        for r in all_res:
            url = r.get("url")
            if not url:
                continue
            try:
                fetched = fetch_firecrawl(url)
                one_liner = (
                    fetched.get("content_md", "")
                    .replace("\n", " ")
                    .strip()[:160]
                )
                results.append(
                    {
                        "date": iso_or_none(r.get("date")),
                        "title": r.get("title") or url,
                        "one_liner": one_liner,
                        "url": url,
                        "source": host_of(url),
                        "region": infer_region(url, one_liner),
                        "confidence": 0.7,  # stub scoring
                    }
                )
            except Exception:
                continue

    # Deduplicate by URL
    seen = {}
    for it in results:
        k = it["url"]
        if k not in seen:
            seen[k] = it
    items = list(seen.values())[:max_items]

    # Summary
    summary = f"Deep search found {len(items)} relevant items for '{topic}' in the last {days} days."

    return {
        "summary": summary,
        "items": items,
        "search_log": search_log,
    }
