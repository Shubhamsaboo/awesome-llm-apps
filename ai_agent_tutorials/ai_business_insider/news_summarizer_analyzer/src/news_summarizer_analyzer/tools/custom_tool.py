from crewai_tools import BaseTool
import requests
from typing import List, Dict, Literal
from pydantic import Field

class NewsAPITool(BaseTool):
    name: str = "News API"
    description: str = (
        "Fetches the latest news articles based on a given query using the News API."
    )
    api_key: str = Field(..., description="API key for the News API")
    base_url: Literal["https://newsapi.org/v2/everything"] = "https://newsapi.org/v2/everything"

    def _run(self, query: str) -> List[Dict[str, str]]:
        """Fetches news articles based on a query"""
        params = {
            'q': query,
            'apiKey': self.api_key
        }
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            articles = response.json().get('articles', [])
            return [
                {
                    "title": article["title"],
                    "url": article["url"],
                    "source": article["source"]["name"],
                    "published_date": article["publishedAt"],
                    "snippet": article["description"]
                }
                for article in articles[:10]
            ]
        except requests.RequestException as e:
            raise Exception(f"Error fetching news articles: {str(e)}")

    async def _arun(self, query: str) -> List[Dict[str, str]]:
        """Async implementation of the tool"""
        return self._run(query)
