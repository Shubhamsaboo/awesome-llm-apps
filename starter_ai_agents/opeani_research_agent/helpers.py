from typing import Optional
import re
from datetime import datetime, timezone

def infer_region(url: str, text: str) -> str:
    """
    Infer region from url or text. Returns one of: 'AMER', 'EMEA', 'APAC', 'GLOBAL'.
    """
    url = url.lower()
    text = text.lower()
    # Simple heuristics
    amer_keywords = ["us", "usa", "america", "canada", "brazil", "nytimes", "reuters.com", "bloomberg.com"]
    emea_keywords = ["europe", "eu", "uk", "germany", "france", "italy", "spain", "europa.eu", "ecb.europa.eu", "bis.org", "imf.org"]
    apac_keywords = ["asia", "china", "japan", "india", "australia", "singapore", "hong kong", "apac"]
    
    for k in amer_keywords:
        if k in url or k in text:
            return "AMER"
    for k in emea_keywords:
        if k in url or k in text:
            return "EMEA"
    for k in apac_keywords:
        if k in url or k in text:
            return "APAC"
    return "GLOBAL"

def iso_or_none(s: str) -> Optional[str]:
    """
    Normalize date string to ISO 8601, or return None if invalid.
    """
    if not s:
        return None
    try:
        # Try parsing common date formats
        dt = None
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                dt = datetime.strptime(s, fmt)
                break
            except Exception:
                continue
        if dt is None:
            # Try ISO parse
            dt = datetime.fromisoformat(s)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except Exception:
        return None

def score_item(date_iso: Optional[str], host: str) -> float:
    """
    Score item favoring recent dates and authoritative domains.
    """
    score = 0.0
    # Date recency: max 1.0, decays over 2 years
    if date_iso:
        try:
            dt = datetime.fromisoformat(date_iso)
            now = datetime.now(timezone.utc)
            days = (now - dt).days
            recency = max(0.0, 1.0 - days / 730.0)  # 2 years
            score += recency
        except Exception:
            pass
    # Authority bonus
    host = host.lower()
    authority_domains = [
        "reuters.com", "bloomberg.com", "europa.eu", "ecb.europa.eu", "bis.org", "imf.org"
    ]
    for domain in authority_domains:
        if domain in host:
            score += 1.0
            break
    return score
