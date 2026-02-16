import json

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from helper_functions import create_complete_reel, create_pexels_image_with_text


def _make_tools(pexels_api_key: str) -> list:
    """Create agent tools that wrap create_pexels_image_with_text and create_complete_reel."""

    @tool
    def create_image(caption: str, search_query: str) -> str:
        """Create a single image with text overlay. Use when the user wants a quote image,
        thumbnail, poster-style graphic, or any single visual (not a multi-clip video). Keep the text short and concise.
        caption: text to display on the image. search_query: Pexels search term for the background photo."""
        result = create_pexels_image_with_text(pexels_api_key, search_query, caption)
        return result or "Failed to create image"

    @tool
    def create_reel(items_json: str) -> str:
        """Create a multi-clip video reel. Use when the user wants a short vertical video
        with multiple clips (3-7 items). items_json: JSON string like
        [{"line": "narration text", "search_query": "pexels video query"}, ...]"""
        try:
            items = json.loads(items_json)
            result = create_complete_reel(items, pexels_api_key)
            return result or "Failed to create reel"
        except json.JSONDecodeError as e:
            return f"Invalid JSON: {e}"
        except Exception as e:
            return f"Error: {e}"

    return [create_image, create_reel]


def _create_agent(openai_api_key: str, pexels_api_key: str):
    """Create a LangChain agent using create_agent from langchain_core."""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        max_tokens=1000,
        api_key=openai_api_key,
    )

    tools = _make_tools(pexels_api_key)

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=(
            "You are a social media content creator. Your job is to interpret the user's request "
            "and produce exactly one output using the appropriate tool.\n\n"
            "**Tool selection:**\n"
            "- create_image: Use for single visuals—quotes, motivational posters, thumbnails, "
            "infographics, or any request for one static image with text overlay.\n"
            "- create_reel: Use for short vertical videos with multiple clips (3–7 segments). "
            "Choose this when the user wants a video, reel, montage, or content that tells a story across several scenes.\n\n"
            "**Parameters:**\n"
            "- Pexels search terms: Use 1 relevant, descriptive word that matches the mood or topic "
            "(e.g., 'sunset', 'coding', 'motivation'). Avoid long phrases.\n"
            "- For create_reel: Each item needs 'line' (narration text) and 'search_query' (Pexels video term). "
            "Keep lines concise; vary search queries across clips for visual variety.\n\n"
            "Always call exactly one tool with well-chosen parameters. Never call both tools."
        )
    )

    return agent
