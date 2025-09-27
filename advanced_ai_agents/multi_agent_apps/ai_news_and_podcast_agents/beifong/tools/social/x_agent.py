from typing import List
from pydantic import BaseModel, Field
from enum import Enum
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv
import uuid


load_dotenv()


class SentimentType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    CRITICAL = "critical"


class Category(str, Enum):
    POLITICS = "politics"
    TECHNOLOGY = "technology"
    ENTERTAINMENT = "entertainment"
    SPORTS = "sports"
    BUSINESS = "business"
    HEALTH = "health"
    SCIENCE = "science"
    EDUCATION = "education"
    ENVIRONMENT = "environment"
    SOCIAL_ISSUES = "social_issues"
    PERSONAL = "personal"
    NEWS = "news"
    OTHER = "other"


class AnalyzedPost(BaseModel):
    post_id: str = Field(..., description="The unique identifier for the post")
    sentiment: SentimentType = Field(..., description="The sentiment of the post")
    categories: List[Category] = Field(..., description="List of categories that best describe this post")
    tags: List[str] = Field(..., description="List of relevant tags or keywords extracted from the post")
    reasoning: str = Field(..., description="Brief explanation of why these sentiments and categories were assigned")


class AnalysisResponse(BaseModel):
    analyzed_posts: List[AnalyzedPost] = Field(..., description="List of analyzed posts with sentiment and categorization")


SENTIMENT_AGENT_DESCRIPTION = "Expert sentiment analyzer and content categorizer for social media posts."
SENTIMENT_AGENT_INSTRUCTIONS = dedent("""
    You are an expert sentiment analyzer and content categorizer for social media posts.
    
    You will receive a batch of social media posts, each with a unique post_id. Your task is to analyze each post and return:
    
    1. The EXACT same post_id that was provided (this is critical for matching)
    2. The sentiment (positive, negative, neutral, or critical)
    3. Relevant categories from the predefined list
    4. Generated tags or keywords
    5. Brief reasoning for your analysis
    
    Guidelines for sentiment classification:
    - POSITIVE: Expresses joy, gratitude, excitement, optimism, or other positive emotions
    - NEGATIVE: Expresses sadness, anger, disappointment, fear, or other negative emotions
    - NEUTRAL: Factual, objective, or balanced without strong emotional tone
    - CRITICAL: Contains criticism, skepticism, or questioning, but in a constructive or analytical way
    
    IMPORTANT: You MUST maintain the exact post_id provided for each post in your analysis.
    IMPORTANT: Categories must be chosen ONLY from the predefined list.
    IMPORTANT: Return analysis for ALL posts provided in the input.
    IMPORTANT: You can add news tag if you think that could you be used to write news articles.
""")


def analyze_posts_sentiment(posts_data):
    session_id = str(uuid.uuid4())
    analysis_agent = Agent(
        model=OpenAIChat(id="gpt-4o"),
        instructions=SENTIMENT_AGENT_INSTRUCTIONS,
        description=SENTIMENT_AGENT_DESCRIPTION,
        use_json_mode=True,
        response_model=AnalysisResponse,
        session_id=session_id,
    )
    posts_prompt = "Analyze the sentiment and categorize the following social media posts:\n\n"
    valid_posts = []
    for post in posts_data:
        post_text = post.get("post_text", "")
        post_id = post.get("post_id", "")
        if post_text and post_id:
            valid_posts.append(post)
            posts_prompt += f"POST (ID: {post_id}):\n{post_text}\n\n"
    if not valid_posts:
        return []
    response = analysis_agent.run(posts_prompt, session_id=session_id)
    analysis_results = response.to_dict()["content"]["analyzed_posts"]
    validated_results = []
    valid_post_ids = {post.get("post_id") for post in valid_posts}
    for analysis in analysis_results:
        if analysis.get("post_id") in valid_post_ids:
            validated_results.append(analysis)
        else:
            print(f"Warning: Analysis returned with invalid post_id: {analysis.get('post_id')}")
    return validated_results