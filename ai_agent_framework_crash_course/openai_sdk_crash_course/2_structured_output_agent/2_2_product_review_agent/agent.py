from typing import List, Optional
from enum import Enum
from agents import Agent
from pydantic import BaseModel, Field

class Sentiment(str, Enum):
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"

class ProductReview(BaseModel):
    product_name: Optional[str] = Field(description="Product name if mentioned", default=None)
    rating: int = Field(description="Star rating (1-5)", ge=1, le=5)
    sentiment: Sentiment = Field(description="Overall sentiment of the review")
    main_positives: List[str] = Field(description="Main positive points mentioned", default=[])
    main_negatives: List[str] = Field(description="Main negative points mentioned", default=[])
    would_recommend: Optional[bool] = Field(description="Whether reviewer would recommend", default=None)
    summary: str = Field(description="Brief summary of the review")

root_agent = Agent(
    name="Product Review Analyzer",
    instructions="""
    You are a product review analysis expert that extracts structured data 
    from customer product reviews.
    
    Analyze the review text and extract:
    - Product name if mentioned
    - Star rating (1-5) based on review tone
    - Sentiment classification (very_positive to very_negative)
    - Main positive and negative points
    - Whether they would recommend (if stated or implied)
    - Brief summary
    
    RATING GUIDELINES:
    - 5 stars: Excellent, highly satisfied, "amazing", "perfect"
    - 4 stars: Good, satisfied, minor issues
    - 3 stars: Okay, mixed feelings, "decent"
    - 2 stars: Poor, unsatisfied, significant issues
    - 1 star: Terrible, very unsatisfied, "worst"
    
    IMPORTANT: Response must be valid JSON matching the ProductReview schema.
    """,
    output_type=ProductReview
)
