"""
ArXiv Adapter - Fetches recent AI/ML research papers.

This is a simplified, stateless adapter for the DevPulseAI reference implementation.
ArXiv API is public and requires no authentication.
"""

import httpx
import xml.etree.ElementTree as ET
from typing import List, Dict, Any


def fetch_arxiv_papers(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch recent AI/ML papers from ArXiv.
    
    Args:
        limit: Maximum number of papers to return.
        
    Returns:
        List of signal dictionaries with standardized schema.
    """
    base_url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": "cat:cs.AI OR cat:cs.LG",
        "start": 0,
        "max_results": limit,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    
    signals = []
    
    try:
        response = httpx.get(base_url, params=params, timeout=15.0)
        response.raise_for_status()
        
        # Parse Atom XML response
        root = ET.fromstring(response.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        
        for entry in root.findall("atom:entry", ns):
            title_elem = entry.find("atom:title", ns)
            summary_elem = entry.find("atom:summary", ns)
            id_elem = entry.find("atom:id", ns)
            published_elem = entry.find("atom:published", ns)
            
            title = title_elem.text.strip() if title_elem is not None else "Untitled"
            summary = summary_elem.text.strip() if summary_elem is not None else ""
            arxiv_id = id_elem.text.strip() if id_elem is not None else ""
            published = published_elem.text if published_elem is not None else ""
            
            # Get PDF link
            pdf_link = arxiv_id
            link_elem = entry.find("atom:link[@title='pdf']", ns)
            if link_elem is not None:
                pdf_link = link_elem.attrib.get("href", arxiv_id)
            
            signal = {
                "id": arxiv_id,
                "source": "arxiv",
                "title": title,
                "description": summary[:500] + "..." if len(summary) > 500 else summary,
                "url": arxiv_id,
                "metadata": {
                    "pdf": pdf_link,
                    "published": published
                }
            }
            signals.append(signal)
            
    except httpx.HTTPError as e:
        print(f"[ArXiv Adapter] HTTP error: {e}")
    except ET.ParseError as e:
        print(f"[ArXiv Adapter] XML parse error: {e}")
    except Exception as e:
        print(f"[ArXiv Adapter] Error: {e}")
    
    return signals


if __name__ == "__main__":
    # Quick test
    results = fetch_arxiv_papers(limit=3)
    for r in results:
        print(f"- {r['title'][:60]}...")
