import os
import time
import httpx
from typing import List, Dict, Optional

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
TAVILY_API_URL = "https://api.tavily.com/search"

def search_tavily(query: str, max_results: int = 8) -> List[Dict]:
    """
    Search Tavily API and return normalized results: {title, url, snippet, date=None}
    """
    if not TAVILY_API_KEY:
        raise RuntimeError("TAVILY_API_KEY not set in environment.")

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "max_results": max_results,
        "search_depth": "advanced",
        "include_answer": False,
        "include_raw_content": False,
    }
    for attempt in range(3):
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(TAVILY_API_URL, json=payload)
                resp.raise_for_status()
                data = resp.json()
                out = []
                for item in data.get("results", []) or []:
                    out.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("content", ""),
                        "date": None
                    })
                return out[:max_results]
        except httpx.HTTPStatusError as e:
            if e.response.status_code in {429, 500, 502, 503, 504} and attempt < 2:
                time.sleep(1.5)
                continue
            raise RuntimeError(f"Tavily search failed: {e}")
        except Exception as e:
            if attempt < 2:
                time.sleep(1.5)
                continue
            raise RuntimeError(f"Tavily search failed: {e}")
    return []
