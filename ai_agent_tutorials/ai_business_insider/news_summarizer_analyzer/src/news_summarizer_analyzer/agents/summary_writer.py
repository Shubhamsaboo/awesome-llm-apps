from crewai_tools import BaseTool
from typing import Dict, List, Any, Type
from pydantic import Field, BaseModel
from openai import OpenAI
import os

class Article(BaseModel):
    name: str

class SummaryWriterInput(BaseModel):
    articles: str  # Changed from List[Article] to str because of an errorr

class SummaryWriterTool(BaseTool):
    name: str = "Summary Writer"
    description: str = "Generates concise summaries of news articles."
    api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""), description="API key for OpenAI")
    args_schema: Type[BaseModel] = SummaryWriterInput

    def _run(self, articles: str) -> Dict[str, Any]:  # Change parameter type to str
        """
        Generate a summary for the given articles using OpenAI API.
        
        :param articles: A string containing article names.
        :return: A dictionary with summary and metadata.
        """
        client = OpenAI(api_key=self.api_key)
        
        # Use the articles string directly
        combined_content = articles
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Summarize the following article titles and provide key points: {combined_content}"}
            ],
            max_tokens=300
        )
        summary_text = response.choices[0].message.content.strip()
        
        # Split the summary into summary and key points
        parts = summary_text.split("Key points:")
        summary = parts[0].strip()
        key_points = parts[1].strip().split("\n") if len(parts) > 1 else []

        return {
            "title": "Summary of articles",
            "summary": summary,
            "key_points": key_points,
            "sources": combined_content.split(", ")  # Assuming articles are comma-separated
        }

    async def _arun(self, articles: str) -> Dict[str, Any]:  # Change parameter type to str
        return self._run(articles)
