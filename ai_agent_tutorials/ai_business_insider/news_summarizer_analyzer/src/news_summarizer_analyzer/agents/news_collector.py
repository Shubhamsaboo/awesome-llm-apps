from crewai_tools import BaseTool
import requests
from typing import List, Dict, Literal
from pydantic import Field
import os

class NewsAPITool(BaseTool):
    name: str = "News API"
    description: str = (
        "Fetches the latest news articles based on a given query using the News API."
    )
    api_key: str = Field(default_factory=lambda: os.getenv("NEWS_API_KEY", ""), description="API key for the News API")
    base_url: Literal["https://newsapi.org/v2/everything"] = "https://newsapi.org/v2/everything"

    def __post_init__(self):
        if not self.api_key:
            raise ValueError("API key for News API is not set in the environment variables.")

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
                }
                for article in articles[:5]
            ]
        except requests.RequestException as e:
            raise Exception(f"Error fetching news articles: {str(e)}")

    async def _arun(self, query: str) -> List[Dict[str, str]]:
        """Async implementation of the tool"""
        return self._run(query)

# def news_collector():
#     api_key = os.getenv("NEWS_API_KEY")
#     if not api_key:
#         raise ValueError("API key for News API is not set in the environment variables.")
    
#     tools = [NewsAPITool(api_key=api_key)]
#     # ... rest of the code ...
