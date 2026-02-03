"""
HackerNews Adapter - Fetches top AI/ML stories from HackerNews.

This is a simplified, stateless adapter for the DevPulseAI reference implementation.
Uses the Algolia HN API for better search capabilities.
"""

import httpx
from typing import List, Dict, Any


def fetch_hackernews_stories(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch recent AI/ML related stories from HackerNews.
    
    Args:
        limit: Maximum number of stories to return.
        
    Returns:
        List of signal dictionaries with standardized schema.
    """
    base_url = "https://hn.algolia.com/api/v1/search_by_date"
    params = {
        "query": "AI OR LLM OR Machine Learning OR GPT",
        "tags": "story",
        "hitsPerPage": limit,
        "numericFilters": "points>5"
    }
    
    signals = []
    
    try:
        response = httpx.get(base_url, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        for hit in data.get("hits", []):
            # Skip stories without URLs (Ask HN, etc.)
            if not hit.get("url") and not hit.get("story_text"):
                continue
            
            external_id = str(hit.get("objectID", ""))
            hn_url = f"https://news.ycombinator.com/item?id={external_id}"
            
            signal = {
                "id": external_id,
                "source": "hackernews",
                "title": hit.get("title", "Untitled"),
                "description": hit.get("story_text", "")[:300] if hit.get("story_text") else "",
                "url": hit.get("url") or hn_url,
                "metadata": {
                    "points": hit.get("points", 0),
                    "comments": hit.get("num_comments", 0),
                    "author": hit.get("author", "unknown"),
                    "hn_url": hn_url
                }
            }
            signals.append(signal)
            
    except httpx.HTTPError as e:
        print(f"[HackerNews Adapter] HTTP error: {e}")
    except Exception as e:
        print(f"[HackerNews Adapter] Error: {e}")
    
    return signals


if __name__ == "__main__":
    # Quick test
    results = fetch_hackernews_stories(limit=3)
    for r in results:
        print(f"- {r['title']}: {r['metadata']['points']} points")
