"""
Tavily-based Tools for Deep Research Agent

Provides web search with content using the Tavily API.
The search returns full page content, eliminating the need for separate scraping.

The research() tool wraps an internal Deep Agent that runs in a separate thread
to prevent subagent text from leaking to the frontend via LangChain callback propagation.
"""

import os
from typing import Any
from concurrent.futures import ThreadPoolExecutor
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from tavily import TavilyClient


def _do_internet_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Core search logic - callable as regular function.

    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 5)

    Returns:
        List of dicts with url, title, and content for each result
    """
    print(f"[TOOL] internet_search: query='{query}', max_results={max_results}")

    tavily_key = os.environ.get("TAVILY_API_KEY")
    if not tavily_key:
        raise RuntimeError("TAVILY_API_KEY not set")

    try:
        client = TavilyClient(api_key=tavily_key)
        results = client.search(
            query=query,
            max_results=max_results,
            include_raw_content=False,  # Disable raw content for performance
            topic="general",
        )

        # Format results for agent consumption
        formatted_results = []
        for r in results.get("results", []):
            formatted_results.append(
                {
                    "url": r.get("url", ""),
                    "title": r.get("title", ""),
                    "content": (r.get("content") or "")[
                        :3000
                    ],  # Truncate to 3000 chars
                }
            )

        print(f"[TOOL] internet_search: found {len(formatted_results)} results")
        return formatted_results

    except Exception as e:
        print(f"[TOOL] internet_search error: {e}")
        return [{"error": str(e)}]


@tool
def internet_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Search the web and return results with content.

    Use this tool to find relevant web pages about a topic.
    Returns search results including the page content for analysis.

    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 5)

    Returns:
        List of dicts with url, title, and content for each result
    """
    return _do_internet_search(query, max_results)


@tool
def research(query: str) -> dict:
    """
    Research a topic using web search. Returns structured data with sources.

    This tool creates an internal Deep Agent that runs in a SEPARATE THREAD to prevent
    LangChain callback propagation. The thread has isolated execution context, so the
    internal agent's events don't leak to the parent's astream_events() stream.

    Args:
        query: The research query/topic to investigate

    Returns:
        dict: {
            "summary": str - Prose summary of findings,
            "sources": list[dict] - [{url, title, content, status}, ...]
        }
    """
    print(f"[TOOL] research: query='{query}' (using thread isolation)")

    from deepagents import create_deep_agent
    from langchain_openai import ChatOpenAI

    def _run_research_isolated():
        """
        Runs in separate thread with no inherited LangChain context.
        This breaks callback propagation at the OS level.
        """
        # Capture internet_search results
        search_results = []

        # Wrapper to capture results while passing through to agent
        def internet_search_tracked(query: str, max_results: int = 5):
            """Search the web and return results with content.

            Args:
                query: The search query string
                max_results: Maximum number of results to return (default: 5)

            Returns:
                List of dicts with url, title, and content for each result
            """
            results = _do_internet_search(query, max_results)
            search_results.extend(results)
            return results

        model_name = os.environ.get("OPENAI_MODEL", "gpt-5.5")
        llm = ChatOpenAI(
            model=model_name,
            temperature=0.7,
            api_key=os.environ.get("OPENAI_API_KEY"),
        )

        # System prompt for the internal researcher
        researcher_prompt = """You are a Research Specialist.

Use internet_search to find information. Return a prose summary of findings.

Rules:
- Call internet_search ONCE with a focused query
- Analyze the returned content
- Return a brief summary (2-3 sentences) of key findings
- No JSON, no code blocks, just prose"""

        research_agent = create_deep_agent(
            model=llm,
            system_prompt=researcher_prompt,
            tools=[internet_search_tracked],  # Use tracked version
            # No middleware - this runs in isolated thread
        )

        # Run in isolated thread context - no callback inheritance possible
        result = research_agent.invoke({"messages": [HumanMessage(content=query)]})

        summary = result["messages"][-1].content

        # Format sources for frontend
        sources = [
            {
                "url": r["url"],
                "title": r.get("title", ""),
                "content": r.get("content", "")[:3000],  # Include content preview
                "status": "found",
            }
            for r in search_results
            if "url" in r and not r.get("error")
        ]

        return {"summary": summary, "sources": sources}

    # Run in thread pool to isolate from parent async context
    # This blocks the tool execution until research completes, which is acceptable
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run_research_isolated)
        result = future.result()  # Blocks until complete

    print(f"[TOOL] research: completed with {len(result['sources'])} sources")
    return result
