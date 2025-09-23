from .tools.search_perplexity import search_perplexity
from .tools.search_tavily import search_tavily
from .tools.fetch_firecrawl import fetch_firecrawl
# Add any additional helpers as needed

def deep_search_api_first(topic: str, days: int, max_items: int) -> dict:
    """
    Returns a dict like:
    {
      "summary": str,
      "items": [
        {"date": "YYYY-MM-DD", "title": str, "one_liner": str, "url": str, "source": str, "region": str, "confidence": float}
      ],
      "search_log": [{"query": str, "results": [{"url": str, "title": str}]}]
    }
    """
    # This function should orchestrate Perplexity + Tavily + Firecrawl via the tools modules
    # and must NOT import streamlit or call st.* anywhere.
    # ...existing backend logic goes here...
    return {"summary": "Stub summary.", "items": [], "search_log": []}
