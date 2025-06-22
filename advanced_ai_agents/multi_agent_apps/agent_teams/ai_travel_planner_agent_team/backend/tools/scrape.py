from firecrawl import FirecrawlApp, ScrapeOptions
import os
from agno.tools import tool
from loguru import logger
from config.logger import logger_hook

app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))


@tool(
    name="scrape_website",
    description="Scrape a website and return the markdown content.",
    tool_hooks=[logger_hook],
)
def scrape_website(url: str) -> str:
    """Scrape a website and return the markdown content.

    Args:
        url (str): The URL of the website to scrape.

    Returns:
        str: The markdown content of the website.

    Example:
        >>> scrape_website("https://www.google.com")
        "## Google"
    """
    scrape_status = app.scrape_url(
        url,
        formats=["markdown"],
        wait_for=30000,
        timeout=60000,
    )
    return scrape_status.markdown
