from crewai_tools import BaseTool
from typing import Dict, List, Type
from pydantic import Field
import requests
import os

from pydantic import BaseModel, Field

class Article(BaseModel):
    title: str
    url: str
    snippet: str

class FactCheckerInput(BaseModel):
    articles: List[Article] = Field(
        ..., 
        description="List of articles to fact-check",
        example=[{
            "title": "Sample Article",
            "url": "https://example.com",
            "snippet": "Sample article content"
        }]
    )

class FactCheckerTool(BaseTool):
    name: str = "Fact Checker"
    description: str = "Verifies the factual accuracy of news articles using Google Fact Check API."
    args_schema: Type[BaseModel] = FactCheckerInput
    api_key: str = Field(default_factory=lambda: os.getenv("GOOGLE_FACT_CHECK_API_KEY", ""), description="API key for Google Fact Check API")
    base_url: str = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

    def _run(self, articles: List[Article]) -> List[str]:
        """
        Verifies the factual accuracy of news articles.

        Args:
            articles: A list of Article objects to fact-check.

        Returns:
            A list of titles of articles that are considered factual.
        """
        # Ensuring articles is a list of Article objects
        if isinstance(articles, str):
            raise ValueError("Expected a list of Article objects, got a string")
            
        if not isinstance(articles, list):
            raise ValueError("Expected a list of Article objects")
        
        factual_articles = []
        for article in articles:
            query = f"{article.title} {article.snippet}"
            params = {
                'key': self.api_key,
                'query': query
            }
            try:
                response = requests.get(self.base_url, params=params)
                response.raise_for_status()
                fact_checks = response.json().get('claims', [])
                
                # If no fact checks found, consider the article potentially factual
                if not fact_checks:
                    factual_articles.append(article.title)
                    continue

                # Check each claim review
                for check in fact_checks:
                    claim_reviews = check.get('claimReview', [])
                    if not claim_reviews:
                        continue
                    
                    rating = claim_reviews[0].get('textualRating', '').lower()
                    # Consider article factual if no clear false/fake indicators
                    if not any(indicator in rating for indicator in ['false', 'fake', 'pants on fire', 'incorrect']):
                        factual_articles.append(article.title)
                        break

            except requests.RequestException as e:
                print(f"Error checking facts for article '{article.title}': {str(e)}")
                # In case of API error, we'll include the article but log the error
                factual_articles.append(article.title)

        return factual_articles

    async def _arun(self, articles: List[Dict[str, str]]) -> List[str]:
        """Async implementation of the tool"""
        return self._run(articles)
