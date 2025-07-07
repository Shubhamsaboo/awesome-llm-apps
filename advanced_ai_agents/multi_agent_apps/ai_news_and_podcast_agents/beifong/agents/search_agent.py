from typing import List
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from agno.tools.duckduckgo import DuckDuckGoTools
from textwrap import dedent
from tools.wikipedia_search import wikipedia_search
from tools.google_news_discovery import google_news_discovery_run
from tools.jikan_search import jikan_search
from tools.embedding_search import embedding_search
from tools.social_media_search import social_media_search, social_media_trending_search
from tools.search_articles import search_articles
from tools.web_search import run_browser_search


load_dotenv()


class ReturnItem(BaseModel):
    url: str = Field(..., description="The URL of the search result")
    title: str = Field(..., description="The title of the search result")
    description: str = Field(..., description="A brief description or summary of the search result content")
    source_name: str = Field(
        ...,
        description="The name/type of the source (e.g., 'wikipedia', 'general', or any reputable source tag)",
    )
    tool_used: str = Field(
        ...,
        description="The tools used to generate the search results, unknown if not used or not applicable",
    )
    published_date: str = Field(
        ...,
        description="The published date of the content in ISO format, if not available keep it empty",
    )
    is_scrapping_required: bool = Field(
        ...,
        description="Set to True if the content need scraping, False otherwise, default keep it True if not sure",
    )


class SearchResults(BaseModel):
    items: List[ReturnItem] = Field(..., description="A list of search result items")


SEARCH_AGENT_DESCRIPTION = "You are a helpful assistant that can search the web for information."
SEARCH_AGENT_INSTRUCTIONS = dedent("""
    You are a helpful assistant that can search the web or any other sources for information.
    You should create topic for the search from the given query instead of blindly apply the query to the search tools.
    For a given topic, your job is to search the web or any other sources and return the top 5 to 10 sources about the topic.
    Keep the search sources of high quality and reputable, and sources should be relevant to the asked topic.
    Sources should be from diverse platforms with no duplicates.
    IMPORTANT: User queries might be fuzzy or misspelled. Understand the user's intent and act accordingly.
    IMPORTANT: The output source_name field can be one of ["wikipedia", "general", or any source tag used"].
    IMPORTANT: You have access to different search tools use them when appropriate which one is best for the given search query. Don't use particular tool if not required.
    IMPORTANT: Make sure you are able to detect what tool to use and use it available tool tags = ["google_news_discovery", "duckduckgo", "wikipedia_search", "jikan_search", "social_media_search", "social_media_trending_search", "browser_search", "unknown"].
    IMPORTANT: If query is news related please prefere google news over other news tools.
    IMPORTANT: If returned sources are not of high quality or not relevant to the asked topic, don't include them in the returned sources.
    IMPORTANT: Never include dates to the search query unless user explicitly asks for it.
    IMPORTANT: You are allowed to use appropriate tools to get the best results even the single tool return enough results diverse check is better.
    IMPORTANT: You have access to browser agent for searching as well use it when other source can't suitable for the given tasks but input should detailed instruction to the run_browser_search agent to get the best results and also use it conservatively because it's expensive process.
    """)


def search_agent_run(agent: Agent, query: str) -> str:
    """
    Search Agent which searches the web and other sources for relevant sources about the given topic or query.
    Args:
        agent: The agent instance
        query: The search query
    Returns:
        A formatted string response with the search results (link and gist only)
    """
    print("Search Agent Input:", query)
    session_id = agent.session_id
    from services.internal_session_service import SessionService

    session = SessionService.get_session(session_id)
    current_state = session["state"]
    search_agent = Agent(
        model=OpenAIChat(id="gpt-4o-mini"),
        instructions=SEARCH_AGENT_INSTRUCTIONS,
        description=SEARCH_AGENT_DESCRIPTION,
        use_json_mode=True,
        response_model=SearchResults,
        tools=[
            google_news_discovery_run,
            DuckDuckGoTools(),
            wikipedia_search,
            jikan_search,
            embedding_search,
            social_media_search,
            social_media_trending_search,
            search_articles,
            run_browser_search,
        ],
        session_id=session_id,
    )
    response = search_agent.run(query, session_id=session_id)
    response_dict = response.to_dict()
    current_state["stage"] = "search"
    current_state["search_results"] = response_dict["content"]["items"]
    SessionService.save_session(session_id, current_state)
    has_results = "search_results" in current_state and current_state["search_results"]
    return f"Found {len(response_dict['content']['items'])} sources about {query} {'and added to the search_results' if has_results else ''}"