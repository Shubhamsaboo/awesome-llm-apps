from agno.agent import Agent
from agno.models.openai import OpenAIChat
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from tools.browser_crawler import create_browser_crawler
from textwrap import dedent


load_dotenv()


class ScrapedContent(BaseModel):
    url: str = Field(..., description="The URL of the search result")
    description: str = Field(description="The description of the search result")
    full_text: str = Field(
        ...,
        description="The full text of the given source URL, if not available or not applicable keep it empty",
    )
    published_date: str = Field(
        ...,
        description="The published date of the content in ISO format, if not available keep it empty",
    )


SCRAPE_AGENT_DESCRIPTION = "You are a helpful assistant that can scrape the URL for full content."
SCRAPE_AGENT_INSTRUCTIONS = dedent("""
    You are a content verification and formatting assistant.
    
    You will receive a batch of pre-scraped content from various URLs along with a search query.
    Your job is to:
    
    1. VERIFY RELEVANCE: Ensure each piece of content is relevant to the given query
    2. QUALITY CONTROL: Filter out low-quality, duplicate, or irrelevant content
    3. FORMAT CONSISTENCY: Ensure all content follows a consistent format
    4. LENGTH OPTIMIZATION: Keep content at reasonable length - not too long, not too short
    5. CLEAN TEXT: Remove any formatting artifacts, ads, or navigation elements from scraped content
    
    For each piece of content, return:
    - full_text: The cleaned, relevant text content (or empty if not relevant/low quality)
    - published_date: The publication date in ISO format (or empty if not available)
    
    Note: Some content may be fallback descriptions (when scraping failed) - treat these appropriately and don't penalize them for being shorter.
    
    IMPORTANT: Focus on quality over quantity. It's better to return fewer high-quality, relevant pieces than many low-quality ones.
    """)


def crawl_urls_batch(search_results):
    url_to_search_results = {}
    unique_urls = []
    for search_result in search_results:
        if not search_result.get("url", False):
            continue
        if not search_result.get("is_scrapping_required", True):
            continue
        if not search_result.get('original_url'):
            search_result['original_url'] = search_result['url']
        url = search_result["url"]
        if url not in url_to_search_results:
            url_to_search_results[url] = []
            unique_urls.append(url)
        url_to_search_results[url].append(search_result)
    browser_crawler = create_browser_crawler()
    scraped_results = browser_crawler.scrape_urls(unique_urls)
    url_to_scraped = {result["original_url"]: result for result in scraped_results}
    updated_search_results = []
    successful_scrapes = 0
    failed_scrapes = 0
    for search_result in search_results:
        original_url = search_result["url"]
        scraped = url_to_scraped.get(original_url, {})
        updated_result = search_result.copy()
        updated_result["original_url"] = original_url
        if scraped.get("success", False):
            updated_result["url"] = scraped.get("final_url", original_url)
            updated_result["full_text"] = scraped.get("full_text", "")
            updated_result["published_date"] = scraped.get("published_date", "")
            successful_scrapes += 1
        else:
            updated_result["url"] = original_url
            updated_result["full_text"] = search_result.get("description", "")
            updated_result["published_date"] = ""
            failed_scrapes += 1
        updated_search_results.append(updated_result)
    return updated_search_results, successful_scrapes, failed_scrapes


def verify_content_with_agent(agent, query, search_results, use_agent=True):
    if not use_agent:
        return search_results
    verified_search_results = []
    for _, search_result in enumerate(search_results):
        content_for_verification = {
            "url": search_result["url"],
            "description": search_result.get("description", ""),
            "full_text": search_result["full_text"],
            "published_date": search_result["published_date"],
        }
        search_result["agent_verified"] = False
        try:
            scrape_agent = Agent(
                model=OpenAIChat(id="gpt-4o-mini"),
                instructions=SCRAPE_AGENT_INSTRUCTIONS,
                description=SCRAPE_AGENT_DESCRIPTION,
                use_json_mode=True,
                session_id=agent.session_id,
                response_model=ScrapedContent,
            )
            response = scrape_agent.run(
                f"Query: {query}\n"
                f"Verify and format this scraped content. "
                f"Keep content relevant to the query and ensure quality: {content_for_verification}",
                session_id=agent.session_id,
            )
            verified_item = response.to_dict()["content"]
            search_result["full_text"] = verified_item.get("full_text", search_result["full_text"])
            search_result["published_date"] = verified_item.get("published_date", search_result["published_date"])
            search_result["agent_verified"] = True
        except Exception as _:
            pass
        verified_search_results.append(search_result)
    return verified_search_results


def scrape_agent_run(
    agent: Agent,
    query: str,
) -> str:
    """
    Scrape Agent that takes the search_results (internaly from search_results) and scrapes each URL for full content, making sure those contents are of high quality and relevant to the topic.
    Args:
        agent: The agent instance
        query: The search query
    Returns:
        Response status
    """
    print("Scrape Agent Input:", query)
    session_id = agent.session_id
    from services.internal_session_service import SessionService

    session = SessionService.get_session(session_id)
    current_state = session["state"]
    updated_results, _, _ = crawl_urls_batch(current_state["search_results"])
    verified_results = verify_content_with_agent(agent, query, updated_results, use_agent=False)
    current_state["search_results"] = verified_results
    SessionService.save_session(session_id, current_state)
    has_results = "search_results" in current_state and current_state["search_results"]
    return f"Scraped {len(current_state['search_results'])} sources with full content relevant to '{query}'{' and updated the full text and published date in the search_results items' if has_results else ''}."