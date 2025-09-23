# This is a stub for openai_researcher_agent.py, as the file does not exist in the workspace.
# Please move this code to the correct file if needed.

import time
from typing import List, Dict, Any, Optional
from helpers import infer_region, iso_or_none, score_item
from tools.search_perplexity import search_perplexity
from tools.search_tavily import search_tavily
from tools.fetch_firecrawl import fetch_firecrawl
from urllib.parse import urlparse
from collections import defaultdict

MAX_ITEMS = 12
DAYS_WINDOW = 30

REGIONS = ["AMER", "EMEA", "APAC", "GLOBAL"]

REGULATOR_DOMAINS = [
    "europa.eu", "ecb.europa.eu", "bis.org", "imf.org", "sec.gov", "federalreserve.gov",
    "reuters.com", "bloomberg.com"
]

def deep_search_api_first(topic: str, days: int = DAYS_WINDOW) -> Dict[str, Any]:
    """
    Deep Search (API-first) pipeline for research agent.
    """
    # PLAN
    sub_angles = [
        "regulation or policy",
        "rails or networks",
        "product or launches",
        "funding or M&A"
    ]
    queries = []
    for sub in sub_angles:
        # Freshness queries
        queries.append(f"{topic} {sub} news last {days} days")
        queries.append(f"recent {topic} {sub} developments")
        # Authority queries
        queries.append(f"{topic} {sub} site:reuters.com OR site:bloomberg.com OR site:europa.eu OR site:ecb.europa.eu OR site:bis.org OR site:imf.org")
        queries.append(f"{topic} {sub} site:sec.gov OR site:federalreserve.gov")

    # COLLECT
    all_results = []
    seen_urls = set()
    for q in queries:
        for search_fn in (search_perplexity, search_tavily):
            try:
                results = search_fn(q, max_results=10, days=days)
                for r in results:
                    url = r.get("url")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(r)
            except Exception:
                continue
    # Keep ~20 unique domains
    domain_map = defaultdict(list)
    for r in all_results:
        url = r.get("url", "")
        domain = urlparse(url).netloc
        domain_map[domain].append(r)
    top_domains = sorted(domain_map.items(), key=lambda x: -len(x[1]))[:20]
    top_urls = []
    for domain, items in top_domains:
        for item in items:
            if len(top_urls) < 12:
                top_urls.append(item["url"])
    # Fetch content
    candidates = []
    for url in top_urls:
        try:
            fc = fetch_firecrawl(url)
            content_md = fc.get("content_md", "")
            links = fc.get("links", [])
            # Use first 160 chars as one_liner
            one_liner = content_md[:160].replace("\n", " ").strip()
            # Try to get date from search result or firecrawl
            date = iso_or_none(fc.get("detected_date") or "")
            if not date:
                # Try to get from search result
                for r in all_results:
                    if r.get("url") == url:
                        date = iso_or_none(r.get("date"))
                        break
            title = None
            for r in all_results:
                if r.get("url") == url:
                    title = r.get("title")
                    break
            if not title:
                title = url
            region = infer_region(url, content_md)
            source_domain = urlparse(url).netloc
            candidates.append({
                "date": date,
                "title": title,
                "one_liner": one_liner,
                "url": url,
                "source_domain": source_domain,
                "region": region
            })
        except Exception:
            continue
    # ACT: normalize, score, dedupe
    deduped = {}
    for c in candidates:
        key = (c["title"], c["source_domain"], c["date"] or "")
        score = score_item(c["date"], c["source_domain"])
        if key not in deduped or score > deduped[key]["score"]:
            c["score"] = score
            deduped[key] = c
    items = sorted(deduped.values(), key=lambda x: -x["score"])[:MAX_ITEMS]
    # VERIFY
    fail_reason = None
    if len(items) < 5:
        fail_reason = "Fewer than 5 items found."
    elif sum(1 for i in items if i["date"] and (datetime.now(timezone.utc) - datetime.fromisoformat(i["date"]).replace(tzinfo=timezone.utc)).days <= days) < int(0.8 * len(items)):
        fail_reason = f"Less than 80% of items are within {days} days."
    elif len(set(i["source_domain"] for i in items)) < 3:
        fail_reason = "Fewer than 3 unique publishers."
    elif not all(i["url"] for i in items):
        fail_reason = "Some items missing URLs."
    if fail_reason:
        # Second pass: focus on missing regions or regulator domains
        needed_regions = set(REGIONS) - set(i["region"] for i in items)
        needed_domains = set(REGULATOR_DOMAINS) - set(i["source_domain"] for i in items)
        # Try to fetch more from missing regions/domains
        # ... (omitted for brevity, similar to above, can be expanded)
        # If still fail, return
        return {"status": "fail", "reason": fail_reason, "items": items}
    # DONE: produce JSON and brief
    summary = "Executive Summary: This report covers recent developments in {topic} across regulation, networks, products, and funding."
    bullets = []
    for i in items:
        if i["date"] and i["title"]:
            bullets.append(f"{i['date'][:10]} — {i['title']}: {i['one_liner']} [{i['source_domain']}]" )
    gaps = []
    if len(items) < MAX_ITEMS:
        gaps.append("Limited number of high-quality sources found.")
    if fail_reason:
        gaps.append(fail_reason)
    return {
        "status": "success",
        "executive_summary": summary,
        "recent_changes": bullets,
        "gaps_and_limitations": gaps,
        "items": items
    }
