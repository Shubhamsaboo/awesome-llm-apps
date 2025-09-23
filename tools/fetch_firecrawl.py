import os
import time
import httpx
from typing import Dict, Any

FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY")
FIRECRAWL_API_URL = "https://api.firecrawl.dev/v1/scrape"

def fetch_firecrawl(url: str) -> Dict[str, Any]:
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

    for attempt in range(3):
        try:
            with httpx.Client(timeout=45.0) as client:
                resp = client.post(FIRECRAWL_API_URL, headers=headers, json=payload)
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
        except httpx.HTTPStatusError as e:
            if e.response.status_code in {429, 500, 502, 503, 504} and attempt < 2:
                time.sleep(1.5)
                continue
            raise RuntimeError(f"Firecrawl fetch failed: {e}")
        except Exception as e:
            if attempt < 2:
                time.sleep(1.5)
                continue
            raise RuntimeError(f"Firecrawl fetch failed: {e}")
    return {"url": url, "content_md": "", "links": [], "detected_date": None}
