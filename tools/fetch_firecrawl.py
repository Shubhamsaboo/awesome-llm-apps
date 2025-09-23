import os
import requests
import time
from typing import Dict, Any, Optional

FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY")
FIRECRAWL_API_URL = "https://api.firecrawl.dev/v1/scrape"


def fetch_firecrawl(url: str, max_retries: int = 3, backoff: float = 1.0) -> Dict[str, Any]:
    """
    Fetches content from Firecrawl API and returns a normalized dict:
    {url, content_md, links, detected_date=None}
    """
    if not FIRECRAWL_API_KEY:
        raise RuntimeError("FIRECRAWL_API_KEY environment variable not set.")

    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "url": url,
        "formats": ["markdown"],
        "includeLinks": True,
    }

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(FIRECRAWL_API_URL, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            content_md = data.get("markdown", "")
            links = data.get("links", [])
            return {
                "url": url,
                "content_md": content_md,
                "links": links,
                "detected_date": None,
            }
        except Exception as e:
            if attempt == max_retries:
                raise
            time.sleep(backoff * attempt)

# Example usage (for testing only):
# if __name__ == "__main__":
#     print(fetch_firecrawl("https://en.wikipedia.org/wiki/Artificial_intelligence"))
