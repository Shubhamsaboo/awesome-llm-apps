from agno.agent import Agent
import requests
import time
from typing import List, Dict, Any, Optional
import html
import json


def jikan_search(agent: Agent, query: str) -> str:
    """
    Search for anime information using the Jikan API (MyAnimeList API).
    This provides anime data, reviews, and recommendations to enhance podcast content.
    
    Jikan scrapes public MyAnimeList pages.
    The service consists of two core parts
    
    Args:
        agent: The agent instance
        query: The search query

    Returns:
        Search results
    """
    print("Jikan Search:", query)

    try:
        formatted_query = query.replace(" ", "%20")
        anime_results = _search_anime(formatted_query)
        if not anime_results:
            return "No relevant anime found for this topic. Continuing with other search methods."
        results = []
        for anime in anime_results[:5]:
            anime_id = anime.get("mal_id")
            if not anime_id:
                continue
            anime_details = _get_anime_details(anime_id)
            if anime_details:
                results.append(anime_details)
            time.sleep(0.5)
        if not results:
            return "No detailed anime information could be retrieved. Continuing with other search methods."
        return f"Found {len(results)} anime titles related to your topic. results {json.dumps(results, indent=2)}."
    except Exception as e:
        return f"Error in anime search: {str(e)}. Continuing with other search methods."


def _search_anime(query: str) -> List[Dict[str, Any]]:
    try:
        search_url = f"https://api.jikan.moe/v4/anime?q={query}&sfw=true&order_by=popularity&sort=asc&limit=10"
        response = requests.get(search_url)
        if response.status_code == 429:
            time.sleep(0.5)
            response = requests.get(search_url)
        if response.status_code != 200:
            return []
        data = response.json()
        if "data" not in data:
            return []
        return data["data"]
    except Exception as _:
        return []


def _get_anime_details(anime_id: int) -> Optional[Dict[str, Any]]:
    try:
        details_url = f"https://api.jikan.moe/v4/anime/{anime_id}/full"
        details_response = requests.get(details_url)
        if details_response.status_code == 429:
            time.sleep(0.5)
            details_response = requests.get(details_url)
        if details_response.status_code != 200:
            return None
        details_data = details_response.json()
        if "data" not in details_data:
            return None
        anime = details_data["data"]
        return _format_anime_info(anime)
    except Exception as _:
        return None


def _get_anime_recommendations(anime_id: int) -> List[Dict[str, Any]]:
    try:
        recs_url = f"https://api.jikan.moe/v4/anime/{anime_id}/recommendations"
        recs_response = requests.get(recs_url)
        if recs_response.status_code == 429:
            time.sleep(0.5)
            recs_response = requests.get(recs_url)
        if recs_response.status_code != 200:
            return []
        recs_data = recs_response.json()
        if "data" not in recs_data:
            return []

        recommendations = []
        for rec in recs_data["data"][:5]:
            if "entry" in rec:
                title = rec["entry"].get("title", "")
                if title:
                    recommendations.append(title)
        return recommendations
    except Exception as _:
        return []


def _format_anime_info(anime: Dict[str, Any]) -> Dict[str, Any]:
    try:
        mal_id = anime.get("mal_id")
        title = anime.get("title", "Unknown Anime")
        title_english = anime.get("title_english")
        if title_english and title_english != title:
            title_display = f"{title} ({title_english})"
        else:
            title_display = title

        url = anime.get("url", f"https://myanimelist.net/anime/{mal_id}")
        synopsis = anime.get("synopsis", "No synopsis available.")
        synopsis = html.unescape(synopsis)
        episodes = anime.get("episodes", "Unknown")
        status = anime.get("status", "Unknown")
        aired_string = anime.get("aired", {}).get("string", "Unknown")
        score = anime.get("score", "N/A")
        scored_by = anime.get("scored_by", 0)
        rank = anime.get("rank", "N/A")
        popularity = anime.get("popularity", "N/A")
        studios = []
        for studio in anime.get("studios", []):
            if "name" in studio:
                studios.append(studio["name"])
        studio_text = ", ".join(studios) if studios else "Unknown"
        genres = []
        for genre in anime.get("genres", []):
            if "name" in genre:
                genres.append(genre["name"])
        genre_text = ", ".join(genres) if genres else "Unknown"
        themes = []
        for theme in anime.get("themes", []):
            if "name" in theme:
                themes.append(theme["name"])
        demographics = []
        for demo in anime.get("demographics", []):
            if "name" in demo:
                demographics.append(demo["name"])
        content = f"Title: {title_display}\n"
        content += f"Score: {score} (rated by {scored_by:,} users)\n"
        content += f"Rank: {rank}, Popularity: {popularity}\n"
        content += f"Episodes: {episodes}\n"
        content += f"Status: {status}\n"
        content += f"Aired: {aired_string}\n"
        content += f"Studio: {studio_text}\n"
        content += f"Genres: {genre_text}\n"
        if themes:
            content += f"Themes: {', '.join(themes)}\n"
        if demographics:
            content += f"Demographics: {', '.join(demographics)}\n"
        content += f"\nSynopsis:\n{synopsis}\n"
        if mal_id:
            recommendations = _get_anime_recommendations(mal_id)
            if recommendations:
                content += f"\nSimilar Anime: {', '.join(recommendations)}\n"
        summary = f"{title_display} - {genre_text} anime with {episodes} episodes. "
        summary += f"Rating: {score}/10. "
        if synopsis:
            short_synopsis = synopsis[:150] + "..." if len(synopsis) > 150 else synopsis
            summary += short_synopsis
        categories = ["anime", "japanese animation", "entertainment"]
        if genres:
            categories.extend(genres[:5])
        if themes:
            categories.extend(themes[:2])
        return {
            "id": f"jikan_{mal_id}",
            "title": f"{title_display} (Anime)",
            "url": url,
            "published_date": aired_string.split(" to ")[0] if " to " in aired_string else aired_string,
            "description": content,
            "source_id": "jikan",
            "source_name": "MyAnimeList",
            "categories": categories,
            "is_scrapping_required": False,

        }
    except Exception as _:
        return {
            "id": f"jikan_{anime.get('mal_id', 'unknown')}",
            "title": f"{anime.get('title', 'Unknown Anime')} (Anime)",
            "url": anime.get("url", "https://myanimelist.net"),
            "published_date": None,
            "description": anime.get("synopsis", "No information available."),
            "source_id": "jikan",
            "source_name": "MyAnimeList",
            "categories": ["anime", "japanese animation", "entertainment"],
            "is_scrapping_required": False,
        }
        
        
if __name__ == "__main__":
    print(jikan_search({}, "One Piece anime overview and details"))
    