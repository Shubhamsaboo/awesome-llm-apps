"""
GitHub Adapter - Fetches trending repositories from GitHub.

This is a simplified, stateless adapter for the DevPulseAI reference implementation.
No authentication required for basic public API access.
"""

import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Any


def fetch_github_trending(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch trending GitHub repositories created in the last 24 hours.
    
    Args:
        limit: Maximum number of repositories to return.
        
    Returns:
        List of signal dictionaries with standardized schema.
    """
    base_url = "https://api.github.com/search/repositories"
    date_query = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    params = {
        "q": f"created:>{date_query} sort:stars",
        "per_page": limit
    }
    
    signals = []
    
    try:
        response = httpx.get(base_url, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        for item in data.get("items", []):
            signal = {
                "id": str(item["id"]),
                "source": "github",
                "title": item["full_name"],
                "description": item.get("description") or "No description",
                "url": item["html_url"],
                "metadata": {
                    "stars": item["stargazers_count"],
                    "language": item.get("language"),
                    "topics": item.get("topics", [])
                }
            }
            signals.append(signal)
            
    except httpx.HTTPError as e:
        print(f"[GitHub Adapter] HTTP error: {e}")
    except Exception as e:
        print(f"[GitHub Adapter] Error: {e}")
    
    return signals


if __name__ == "__main__":
    # Quick test
    results = fetch_github_trending(limit=3)
    for r in results:
        print(f"- {r['title']}: {r['metadata']['stars']} stars")
