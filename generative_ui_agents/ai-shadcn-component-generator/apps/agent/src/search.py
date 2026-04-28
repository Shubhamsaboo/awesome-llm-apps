import os
from langchain.tools import tool
from tavily import TavilyClient

_client: TavilyClient | None = None

def _get_client():
    global _client
    if _client is None:
        _client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    return _client

@tool
def search_internet(query: str):
    """Search the internet for a given query."""
    return _get_client().search(query)

@tool
def extract_site(website: str):
    """Extract structured content from a given website URL."""
    return _get_client().extract(website)

@tool
def crawl_site(website: str, instructions: str):
    """Crawl a website following the given instructions to gather specific information."""
    return _get_client().crawl(website, instructions)

search_tools = [search_internet, extract_site, crawl_site]
