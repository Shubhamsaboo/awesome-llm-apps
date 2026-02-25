"""
Medium Adapter - Fetches tech blogs from Medium and other RSS feeds.

This is a simplified, stateless adapter for the DevPulseAI reference implementation.
Uses feedparser to fetch from RSS/Atom feeds.
"""

import feedparser
from typing import List, Dict, Any


# Tech blog feeds to monitor
FEEDS = [
    "https://medium.com/feed/tag/artificial-intelligence",
    "https://medium.com/feed/tag/machine-learning",
    "https://medium.com/feed/@netflixtechblog",
    "https://engineering.fb.com/feed/",
]


def fetch_medium_blogs(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch recent tech blogs from Medium and engineering blogs.
    
    Args:
        limit: Maximum number of entries per feed.
        
    Returns:
        List of signal dictionaries with standardized schema.
    """
    signals = []
    
    for feed_url in FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:limit]:
                # Get summary or description
                summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
                
                # Clean HTML tags from summary (simple approach)
                if summary:
                    import re
                    summary = re.sub(r'<[^>]+>', '', summary)[:500]
                
                signal = {
                    "id": entry.get("id", entry.link),
                    "source": "medium",
                    "title": entry.title,
                    "description": summary,
                    "url": entry.link,
                    "metadata": {
                        "published": getattr(entry, "published", ""),
                        "author": getattr(entry, "author", "Unknown"),
                        "feed": feed_url
                    }
                }
                signals.append(signal)
                
        except Exception as e:
            print(f"[Medium Adapter] Error fetching {feed_url}: {e}")
    
    return signals


if __name__ == "__main__":
    # Quick test
    results = fetch_medium_blogs(limit=2)
    for r in results:
        print(f"- {r['title'][:60]}...")
