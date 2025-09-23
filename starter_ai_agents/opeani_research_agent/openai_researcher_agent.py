# --- DIAGNOSTICS TAB ---
import os
tab_live, tab_brief, tab_diag = st.tabs(["Live research", "Brief", "Diagnostics"])
with tab_diag:
    st.header("Diagnostics")
    # Env var checks
    envs = [
        ("PERPLEXITY_API_KEY", os.environ.get("PERPLEXITY_API_KEY")),
        ("TAVILY_API_KEY", os.environ.get("TAVILY_API_KEY")),
        ("FIRECRAWL_API_KEY", os.environ.get("FIRECRAWL_API_KEY")),
    ]
    for k, v in envs:
        if v:
            st.success(f"{k}: ✅ Present")
        else:
            st.error(f"{k}: ❌ Missing")

    # Perplexity dry run
    if st.button("Perplexity dry run"):
        try:
            results = search_perplexity("site:reuters.com payments last 7 days", 3)
            st.write("Top Perplexity URLs:")
            for r in results:
                st.write(r.get("url"))
        except Exception as e:
            st.error(f"Perplexity error: {e}")

    # Tavily dry run
    if st.button("Tavily dry run"):
        try:
            results = search_tavily("ECB instant payments last 30 days", 3)
            st.write("Top Tavily URLs:")
            for r in results:
                st.write(r.get("url"))
        except Exception as e:
            st.error(f"Tavily error: {e}")

    # Firecrawl dry fetch
    if st.button("Firecrawl dry fetch"):
        try:
            data = fetch_firecrawl("https://www.ecb.europa.eu/press/")
            st.code(data.get("content_md", "")[:200])
        except Exception as e:
            st.error(f"Firecrawl error: {e}")
import streamlit as st
from tools.search_perplexity import search_perplexity
from tools.search_tavily import search_tavily
from tools.fetch_firecrawl import fetch_firecrawl as _fetch_firecrawl

# Cache Firecrawl to save cost
@st.cache_data(ttl=600)
def fetch_firecrawl(url: str):
    return _fetch_firecrawl(url)

# --- DEEP SEARCH (API-FIRST) UI PATH ---
st.title("Deep Search (API-first)")
topic = st.sidebar.text_input("Topic", "cross-border payments fintech")
days = st.sidebar.radio("Days window", [7, 30, 90], index=2)
max_items = st.sidebar.slider("Max items", 6, 10, 8)

if st.sidebar.button("Run Deep Search", type="primary"):
    st.info("Planning queries...")
    sub_angles = ["regulation policy","rails networks","product launches","funding M&A"]
    regulator_sites = ["reuters.com","europa.eu","bis.org","swift.com"]
    queries = []
    for sub in sub_angles:
        queries.append(f"{topic} {sub} last {days} days")
        queries.append(f"{topic} {sub} September 2025")
        for site in regulator_sites:
            queries.append(f"{topic} {sub} site:{site}")

    st.write(f"**Total queries:** {len(queries)}")
    st.write(queries)
    st.info("Collecting search results...")
    all_results = []
    seen_urls = set()
    for q in queries:
        for search_fn in (search_perplexity, search_tavily):
            try:
                results = search_fn(q, max_results=10)
                for r in results:
                    url = r.get("url")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(r)
            except Exception as e:
                st.warning(f"Search error for '{q}': {e}")
    st.write(f"**Total unique URLs:** {len(seen_urls)}")
    # Dedupe by URL, keep ~20
    url_map = {}
    for r in all_results:
        u = r.get("url")
        if u and u not in url_map:
            url_map[u] = r
    top_urls = list(url_map.keys())[:20]
    st.info("Fetching content for top URLs...")
    items = []
    for url in top_urls[:12]:
        try:
            data = fetch_firecrawl(url)
            result = url_map[url]
            title = result.get("title") or url
            one_liner = (data.get("content_md"," ").strip().replace("\n"," ")[:160]).strip()
            d = iso_or_none(result.get("date"))
            # host_of, dedupe_by_key, verify_gate helpers must be defined or imported
            try:
                h = host_of(url)
            except Exception:
                from urllib.parse import urlparse
                def host_of(url: str) -> str:
                    try:
                        return urlparse(url).netloc.lower()
                    except Exception:
                        return ""
                h = host_of(url)
            items.append({
                "date": d, "title": title, "one_liner": one_liner,
                "url": url, "source": h, "region": infer_region(url, one_liner)
            })
        except Exception as e:
            st.warning(f"Firecrawl error for {url}: {e}")
    # ACT: score, dedupe, sort
    for it in items:
        it["score"] = score_item(it["date"], it["source"])

    # Ensure dedupe_by_key is defined
    def dedupe_by_key(items: list[dict]) -> list[dict]:
        seen = {}
        for it in items:
            k = f"{it.get('title','')[:80]}|{host_of(it.get('url',''))}|{it.get('date')}"
            if k not in seen or it.get("score",0) > seen[k].get("score",0):
                seen[k] = it
        return list(seen.values())
    items = dedupe_by_key(items)
    items.sort(key=lambda x: x.get("score",0), reverse=True)
    items = items[:max_items]

    # Ensure verify_gate is defined
    def verify_gate(items: list[dict], days: int, min_items: int = 5, min_unique_publishers: int = 3, min_fresh_ratio: float = 0.8) -> tuple[bool, dict]:
        if len(items) < min_items:
            return False, {"reason": f"Only {len(items)} items (<{min_items})."}
        pubs = { host_of(x.get("url","")) for x in items if x.get("url") }
        if len(pubs) < min_unique_publishers:
            return False, {"reason": f"Only {len(pubs)} unique publishers (<{min_unique_publishers})."}
        fresh = 0
        today = date.today()
        for x in items:
            d = x.get("date")
            if not d: continue
            try:
                age = (today - datetime.fromisoformat(d).date()).days
                if age <= days:
                    fresh += 1
            except Exception:
                pass
        ratio = fresh / max(1, len(items))
        if ratio < min_fresh_ratio:
            return False, {"reason": f"Freshness ratio {ratio:.2f} < {min_fresh_ratio:.2f} within {days}d."}
        if any(not x.get("url") for x in items):
            return False, {"reason": "Some items missing URL."}
        return True, {"publishers": len(pubs), "fresh_ratio": ratio}
    ok, meta = verify_gate(items, days)
    if not ok:
        st.warning(f"Gate not passed: {meta.get('reason')}")
        # Second pass: emphasize missing regions or regulators
        missing_regs = [r for r in ["europa.eu","ecb.europa.eu","bis.org","swift.com","imf.org"] if not any(r in it["source"] for it in items)]
        st.info(f"Missing regulator domains: {', '.join(missing_regs) if missing_regs else 'None'}")
        # Could re-query or re-rank here
    # DONE: Brief
    st.success("Deep Search Complete!")
    st.subheader("Executive Summary")
    st.markdown(f"This brief covers recent developments in **{topic}** across regulation, networks, products, and funding.")
    st.subheader(f"What changed in the last {days} days")
    for it in items:
        st.markdown(f"- {it['date'] or '?'} — {it['title']}: {it['one_liner']} [{it['source']}]")
    st.subheader("Gaps & limitations")
    gaps = []
    if not ok:
        gaps.append(meta.get('reason'))
    if len(set(it["region"] for it in items)) < 3:
        gaps.append("Thin region diversity.")
    if len(set(it["source"] for it in items)) < 3:
        gaps.append("Thin publisher diversity.")
    if gaps:
        for g in gaps:
            st.markdown(f"- {g}")
    # Download buttons
    import json
    st.download_button(
        label="Download JSON",
        data=json.dumps(items, indent=2),
        file_name=f"deep_search_{topic.replace(' ', '_')}.json",
        mime="application/json"
    )
    md = f"# Executive Summary\nThis brief covers recent developments in **{topic}** across regulation, networks, products, and funding.\n\n## What changed in the last {days} days\n" + "\n".join([f"- {it['date'] or '?'} — {it['title']}: {it['one_liner']} [{it['source']}]" for it in items]) + "\n\n## Gaps & limitations\n" + "\n".join([f"- {g}" for g in gaps])
    st.download_button(
        label="Download Markdown",
        data=md,
        file_name=f"deep_search_{topic.replace(' ', '_')}.md",
        mime="text/markdown"
    )
def verify_gate(items: list[dict], days: int, min_items: int = 5, min_unique_publishers: int = 3, min_fresh_ratio: float = 0.8) -> tuple[bool, dict]:
    if len(items) < min_items:
        return False, {"reason": f"Only {len(items)} items (<{min_items})."}

    pubs = { host_of(x.get("url","")) for x in items if x.get("url") }
    if len(pubs) < min_unique_publishers:
        return False, {"reason": f"Only {len(pubs)} unique publishers (<{min_unique_publishers})."}

    fresh = 0
    today = date.today()
    for x in items:
        d = x.get("date")
        if not d: 
            continue
        try:
            age = (today - datetime.fromisoformat(d).date()).days
            if age <= days:
                fresh += 1
        except Exception:
            pass

    ratio = fresh / max(1, len(items))
    if ratio < min_fresh_ratio:
        return False, {"reason": f"Freshness ratio {ratio:.2f} < {min_fresh_ratio:.2f} within {days}d."}

    # require URL for all
    if any(not x.get("url") for x in items):
        return False, {"reason": "Some items missing URL."}

    return True, {"publishers": len(pubs), "fresh_ratio": ratio}
# This is a stub for openai_researcher_agent.py, as the file does not exist in the workspace.
# Please move this code to the correct file if needed.

import time
from typing import List, Dict, Any, Optional
from helpers import infer_region, iso_or_none, score_item
from tools.search_perplexity import search_perplexity
from tools.search_tavily import search_tavily
from tools.fetch_firecrawl import fetch_firecrawl
from urllib.parse import urlparse
from datetime import datetime, timezone, date

HIGH_AUTH = (
  "reuters.com","bloomberg.com","ft.com","imf.org","oecd.org","bis.org",
  "ecb.europa.eu","europa.eu","eba.europa.eu","bankofengland.co.uk",
  "federalreserve.gov","treasury.gov","who.int","swift.com"
)

def host_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""

def infer_region(url: str, text: str) -> str:
    h = host_of(url)
    # quick heuristic
    if any(t in h for t in ["mx","latam","br","ar","cl","pe","uy","co",".mx",".br",".ar",".cl",".pe",".co"]): return "AMER"
    if any(t in h for t in ["eu","de","fr","it","es","uk",".eu",".de",".fr",".it",".es",".uk"]): return "EMEA"
    if any(t in h for t in ["jp","sg","hk","au","in",".jp",".sg",".hk",".au",".in"]): return "APAC"
    return "GLOBAL"

def iso_or_none(s: str|None) -> str|None:
    if not s: return None
    try:
        # accept YYYY-MM-DD or RFC-like strings
        return datetime.fromisoformat(s[:10]).date().isoformat()
    except Exception:
        return None

def score_item(date_iso: str|None, host: str) -> float:
    # recency up to +0.6, authority up to +0.4
    s = 0.0
    if date_iso:
        try:
            days = (date.today() - datetime.fromisoformat(date_iso).date()).days
            s += max(0.0, (120 - min(days, 120)) / 200.0)  # 0..0.6
        except Exception:
            pass
    if any(a in host for a in HIGH_AUTH): s += 0.4
    return min(s, 1.0)

def dedupe_by_key(items: list[dict]) -> list[dict]:
    seen = {}
    for it in items:
        k = f"{it.get('title','')[:80]}|{host_of(it.get('url',''))}|{it.get('date')}"
        if k not in seen or it.get("score",0) > seen[k].get("score",0):
            seen[k] = it
    return list(seen.values())
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
