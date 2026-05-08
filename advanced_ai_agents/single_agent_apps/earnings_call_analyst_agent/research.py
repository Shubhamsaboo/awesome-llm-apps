from __future__ import annotations

import json
import os
import re
import xml.etree.ElementTree as ET
from functools import lru_cache
from typing import Any

import requests

from .adk_runtime import run_adk_agent_text
from .schemas import ResearchDocument, ResearchPack, TranscriptSegment, VideoMetadata


SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
YAHOO_NEWS_RSS = "https://feeds.finance.yahoo.com/rss/2.0/headline"
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"
MODEL = os.getenv("EARNINGS_GEMINI_MODEL", "gemini-3-flash-preview")
SEARCH_MODEL = os.getenv("EARNINGS_SEARCH_GEMINI_MODEL", "gemini-2.5-flash")


try:
    from google.adk.agents import Agent
    from google.adk.tools import google_search

    identity_agent = Agent(
        name="earnings_identity_agent",
        model=MODEL,
        description="Identifies the company, ticker, fiscal period, and peer set for an earnings-call video.",
        instruction=(
            "Identify public-company context from YouTube metadata and transcript openings. "
            "Return strict JSON only with keys: company, ticker, fiscal_period, peers, confidence. "
            "Use a ticker only when evidence is strong. Peers must be ticker symbols."
        ),
    )
    market_news_agent = Agent(
        name="earnings_market_news_agent",
        model=SEARCH_MODEL,
        description="Uses Google Search to find current investor-relevant news for a public company.",
        instruction=(
            "Use Google Search for current market news. Return strict JSON only with key items. "
            "Each item must have title, source, url, and summary. Include only real URLs from credible sources. "
            "Exclude forums, social posts, promotional pages, and duplicates."
        ),
        tools=[google_search],
    )
except Exception:
    identity_agent = None
    market_news_agent = None


def build_research_pack(
    metadata: VideoMetadata, transcript: list[TranscriptSegment], max_news: int = 8
) -> ResearchPack:
    sample = " ".join(segment.text for segment in transcript[:24])
    identity = infer_company_identity(metadata.title, metadata.author_name, sample)
    ticker = str(identity.get("ticker") or "").upper().strip()
    company = str(identity.get("company") or "").strip() or _clean_company_name(metadata)

    documents: list[ResearchDocument] = []
    notes: list[str] = []

    if ticker:
        sec_docs, sec_notes = fetch_sec_documents(ticker)
        documents.extend(sec_docs)
        notes.extend(sec_notes)

    news = fetch_market_news(ticker, company, max_news=max_news) if ticker else []
    peers = identity.get("peers", [])
    if not isinstance(peers, list):
        peers = []

    if not documents:
        notes.append("No SEC filing links were resolved automatically.")
    if not news:
        notes.append("No recent market headlines were resolved automatically.")

    return ResearchPack(
        company=company,
        ticker=ticker,
        fiscal_period=str(identity.get("fiscal_period") or ""),
        confidence=float(identity.get("confidence", 0.35)),
        documents=documents,
        peers=[str(peer).upper().strip() for peer in peers if str(peer).strip()][:8],
        news=news,
        notes=notes,
    )


def infer_company_identity(title: str, channel: str, transcript_sample: str) -> dict[str, Any]:
    heuristic = _infer_identity_heuristically(title, channel, transcript_sample)
    if not _has_gemini_key() or identity_agent is None:
        return heuristic

    prompt = f"""
Identify the public company and context for this earnings-call video.
Return strict JSON with keys: company, ticker, fiscal_period, peers, confidence.
Use a stock ticker only when you have strong evidence. Peers should be ticker symbols.

Title: {title}
Channel: {channel}
Transcript opening:
{transcript_sample[:4000]}
"""
    try:
        parsed = _parse_json_object(run_adk_agent_text(identity_agent, prompt))
        if parsed.get("company") or parsed.get("ticker"):
            return {**heuristic, **parsed}
    except Exception:
        return heuristic

    return heuristic


def fetch_sec_documents(ticker: str) -> tuple[list[ResearchDocument], list[str]]:
    notes: list[str] = []
    cik = ticker_to_cik(ticker)
    if not cik:
        return [], [f"SEC CIK lookup did not find ticker {ticker}."]

    headers = {"User-Agent": os.getenv("EARNINGS_USER_AGENT", "earnings-call-analyst-agent")}
    try:
        response = requests.get(
            SEC_SUBMISSIONS_URL.format(cik=cik), headers=headers, timeout=10
        )
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        return [], [f"SEC submissions request failed for {ticker}: {exc}"]

    filings = data.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    accession_numbers = filings.get("accessionNumber", [])
    primary_docs = filings.get("primaryDocument", [])
    filing_dates = filings.get("filingDate", [])

    docs: list[ResearchDocument] = []
    seen_forms: set[str] = set()
    for form, accession, primary_doc, filing_date in zip(
        forms, accession_numbers, primary_docs, filing_dates
    ):
        if form not in {"10-K", "10-Q", "8-K"} or form in seen_forms:
            continue
        accession_path = str(accession).replace("-", "")
        url = (
            f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
            f"{accession_path}/{primary_doc}"
        )
        docs.append(
            ResearchDocument(
                title=f"{ticker} {form} filed {filing_date}",
                kind=form,
                url=url,
                summary="Latest SEC filing resolved from company submissions.",
            )
        )
        seen_forms.add(form)
        if len(docs) >= 3:
            break

    return docs, notes


def fetch_market_news(ticker: str, company: str = "", max_news: int = 8) -> list[ResearchDocument]:
    grounded_items = fetch_adk_grounded_news(ticker, company, max_news=max_news)
    if grounded_items:
        return grounded_items
    yahoo_items = fetch_yahoo_news(ticker, max_news=max_news)
    if yahoo_items:
        return yahoo_items
    return fetch_google_news(ticker, company, max_news=max_news)


def fetch_adk_grounded_news(
    ticker: str, company: str = "", max_news: int = 8
) -> list[ResearchDocument]:
    if not _has_gemini_key() or market_news_agent is None:
        return []

    company_label = company or ticker
    prompt = f"""
Use Google Search to find the latest market-moving news about {company_label} ({ticker}) stock.
Focus on investor-relevant headlines from the last 7 days: earnings, guidance, deliveries,
analyst actions, regulation, major product/business updates, executive news, or stock-moving events.

Return only strict JSON. No markdown.
Schema:
{{
  "items": [
    {{
      "title": "headline",
      "source": "publisher",
      "url": "https://...",
      "summary": "one sentence explaining why this matters to investors"
    }}
  ]
}}

Rules:
- Return at most {max_news} items.
- Include only items with a real public URL.
- Exclude forums, social posts, promotional pages, and duplicate headlines.
"""
    try:
        text = run_adk_agent_text(market_news_agent, prompt)
    except Exception:
        return []

    parsed = _parse_json_object(text)
    raw_items = parsed.get("items", [])
    if not isinstance(raw_items, list):
        return []

    items: list[ResearchDocument] = []
    seen_urls: set[str] = set()
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        title = " ".join(str(raw.get("title") or "").split())
        source = " ".join(str(raw.get("source") or "").split())
        url = str(raw.get("url") or "").strip()
        summary = " ".join(str(raw.get("summary") or "").split())[:260]
        if not title or not url.startswith(("http://", "https://")):
            continue
        if url in seen_urls or _is_low_quality_news_title(title):
            continue
        label = f"{title} - {source}" if source and not title.endswith(f" - {source}") else title
        items.append(
            ResearchDocument(
                title=label,
                kind="news",
                url=url,
                summary=summary or "Latest market context resolved with Gemini Google Search grounding.",
            )
        )
        seen_urls.add(url)
        if len(items) >= max_news:
            break
    return items


def fetch_yahoo_news(ticker: str, max_news: int = 8) -> list[ResearchDocument]:
    try:
        response = requests.get(
            YAHOO_NEWS_RSS,
            params={"s": ticker, "region": "US", "lang": "en-US"},
            timeout=8,
        )
        response.raise_for_status()
        root = ET.fromstring(response.text)
    except Exception:
        return []

    items: list[ResearchDocument] = []
    for item in root.findall(".//item")[:max_news]:
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        description = re.sub("<[^>]+>", "", item.findtext("description") or "")
        if title:
            items.append(
                ResearchDocument(
                    title=title,
                    kind="news",
                    url=link,
                    summary=" ".join(description.split())[:260],
                )
            )
    return items


def fetch_google_news(ticker: str, company: str = "", max_news: int = 8) -> list[ResearchDocument]:
    query = " ".join(part for part in [company, ticker, "stock", "when:7d"] if part).strip()
    headers = {"User-Agent": os.getenv("EARNINGS_USER_AGENT", "earnings-call-analyst-agent")}
    try:
        response = requests.get(
            GOOGLE_NEWS_RSS,
            params={"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"},
            headers=headers,
            timeout=8,
        )
        response.raise_for_status()
        root = ET.fromstring(response.text)
    except Exception:
        return []

    items: list[ResearchDocument] = []
    for item in root.findall(".//item"):
        title = " ".join((item.findtext("title") or "").split())
        link = item.findtext("link") or ""
        description = re.sub("<[^>]+>", "", item.findtext("description") or "")
        if not title or not link or _is_low_quality_news_title(title):
            continue
        items.append(
            ResearchDocument(
                title=title,
                kind="news",
                url=link,
                summary=" ".join(description.split())[:260],
            )
        )
        if len(items) >= max_news:
            break
    return items


def _is_low_quality_news_title(title: str) -> bool:
    low_quality_sources = {"moomoo", "reddit", "stocktwits"}
    source = title.rsplit(" - ", 1)[-1].strip().lower() if " - " in title else ""
    return source in low_quality_sources


@lru_cache(maxsize=1)
def _sec_ticker_map() -> dict[str, str]:
    headers = {"User-Agent": os.getenv("EARNINGS_USER_AGENT", "earnings-call-analyst-agent")}
    response = requests.get(SEC_TICKERS_URL, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
    return {
        str(row.get("ticker", "")).upper(): str(row.get("cik_str", "")).zfill(10)
        for row in data.values()
        if row.get("ticker") and row.get("cik_str")
    }


def ticker_to_cik(ticker: str) -> str:
    try:
        return _sec_ticker_map().get(ticker.upper(), "")
    except Exception:
        return ""


def _infer_identity_heuristically(title: str, channel: str, transcript_sample: str) -> dict[str, Any]:
    text = f"{title} {channel} {transcript_sample[:1200]}"
    ticker = ""
    ticker_match = re.search(r"\(([A-Z]{1,5})\)|\bNYSE:\s*([A-Z]{1,5})\b|\bNASDAQ:\s*([A-Z]{1,5})\b", text)
    if ticker_match:
        ticker = next(group for group in ticker_match.groups() if group)

    company = _clean_company_name(VideoMetadata(video_id="", title=title, author_name=channel))
    quarter = ""
    quarter_match = re.search(r"\b(Q[1-4]\s*(?:FY)?\s*20\d{2}|20\d{2}\s*Q[1-4])\b", text, re.I)
    if quarter_match:
        quarter = quarter_match.group(1).upper()

    return {
        "company": company,
        "ticker": ticker,
        "fiscal_period": quarter,
        "peers": [],
        "confidence": 0.45 if ticker else 0.25,
    }


def _clean_company_name(metadata: VideoMetadata) -> str:
    title = metadata.title
    title = re.sub(r"\b(Q[1-4]|FY|20\d{2}|earnings|call|results|conference|webcast|transcript)\b", "", title, flags=re.I)
    title = re.sub(r"\([^)]*\)", "", title)
    title = re.sub(r"[-|:]+", " ", title)
    words = [word for word in title.split() if word.strip()]
    return " ".join(words[:5]) or metadata.author_name or "Unknown company"


def _has_gemini_key() -> bool:
    return bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))


def _parse_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.I | re.S)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        return {}
    try:
        data = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}
