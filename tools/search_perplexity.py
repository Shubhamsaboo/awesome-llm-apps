import os
import time
import httpx
from typing import List, Dict, Optional

PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


def search_perplexity(query: str, max_results: int = 8) -> List[Dict]:
    """
    Search Perplexity with a web-enabled model and return normalized results.
    Returns a list of dicts: {title, url, snippet, date}
    """
    if not PERPLEXITY_API_KEY:
        raise RuntimeError("PERPLEXITY_API_KEY not set in environment.")

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "pplx-70b-online",
        "messages": [
            {"role": "user", "content": query}
        ],
        "search": True,
        "filter": "recency",
        "max_tokens": 256,
    }

    for attempt in range(3):
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(PERPLEXITY_API_URL, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                # Try to extract web results from the response
                web_results = []
                for item in data.get("web_results", []) or []:
                    web_results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("snippet", ""),
                        "date": item.get("date", None)
                    })
                return web_results[:max_results]
        except httpx.HTTPStatusError as e:
            if e.response.status_code in {429, 500, 502, 503, 504} and attempt < 2:
                time.sleep(1.5)
                continue
            raise RuntimeError(f"Perplexity search failed: {e}")
        except Exception as e:
            if attempt < 2:
                time.sleep(1.5)
                continue
            raise RuntimeError(f"Perplexity search failed: {e}")
    return []
