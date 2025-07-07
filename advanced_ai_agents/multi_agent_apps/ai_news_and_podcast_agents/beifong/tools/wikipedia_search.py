from agno.agent import Agent


def wikipedia_search(agent: Agent, query: str, srlimit: int = 5) -> str:
    """
    Search Wikipedia for articles using Wikipedia API.
    Returns only links and short summaries without fetching full content.

    Args:
        agent: The agent instance
        query: The search query
        srlimit: The number of results to return

    Returns:
        A formatted string response with the search results (link and gist only)
    """
    import requests
    import html
    import json
    
    print("Wikipedia Search Input:", query)
    try:
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": srlimit,
            "utf8": 1,
        }
        search_response = requests.get(search_url, params=search_params)
        search_data = search_response.json()
        if (
            "query" not in search_data
            or "search" not in search_data["query"]
            or not search_data["query"]["search"]
        ):
            print(f"No Wikipedia results found for query: {query}")
            return "No relevant Wikipedia articles found for this topic."
        results = []
        for item in search_data["query"]["search"]:
            title = item["title"]
            snippet = html.unescape(
                item["snippet"]
                .replace('<span class="searchmatch">', "")
                .replace("</span>", "")
            )
            url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
            result = {
                "title": title,
                "url": url,
                "gist": snippet,
                "source": "Wikipedia",
            }
            results.append(result)
        if not results:
            return "No Wikipedia search results found."
        return f"for all results is_scrapping_required: True, results: {json.dumps(results, ensure_ascii=False, indent=2)}"
    except Exception as e:
        print(f"Error during Wikipedia search: {str(e)}")
        return f"Error in Wikipedia search: {str(e)}"
