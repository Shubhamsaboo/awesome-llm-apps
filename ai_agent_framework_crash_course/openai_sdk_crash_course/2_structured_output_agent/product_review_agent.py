"""
OpenAI Agents SDK Tutorial 2: Structured Output Agent - Product Reviews

This module demonstrates extracting structured data from product reviews
using complex nested Pydantic models.
"""

import os
from typing import List, Optional
from enum import Enum
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator
from agents import Agent, Runner

# Load environment variables
load_dotenv()

class Sentiment(str, Enum):
    """Review sentiment classification"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"

class ProductCategory(str, Enum):
    """Product category classification"""
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    HOME = "home"
    BOOKS = "books"
    FOOD = "food"
    BEAUTY = "beauty"
    SPORTS = "sports"
    AUTOMOTIVE = "automotive"
    OTHER = "other"

class ProductInfo(BaseModel):
    """Product information extracted from review"""
    name: Optional[str] = Field(description="Product name if mentioned", default=None)
    category: ProductCategory = Field(description="Inferred product category")
    brand: Optional[str] = Field(description="Brand name if mentioned", default=None)
    price_mentioned: Optional[str] = Field(description="Price if mentioned in review", default=None)

class ReviewMetrics(BaseModel):
    """Quantitative review metrics"""
    rating: int = Field(description="Star rating (1-5)", ge=1, le=5)
    sentiment: Sentiment = Field(description="Overall sentiment of the review")
    confidence_score: float = Field(description="Confidence in sentiment analysis (0-1)", ge=0, le=1)
    word_count: int = Field(description="Approximate word count of review", ge=0)

class ReviewAspects(BaseModel):
    """Specific aspects mentioned in the review"""
    quality: Optional[str] = Field(description="Quality assessment if mentioned", default=None)
    value_for_money: Optional[str] = Field(description="Value assessment if mentioned", default=None)
    shipping: Optional[str] = Field(description="Shipping experience if mentioned", default=None)
    customer_service: Optional[str] = Field(description="Customer service experience if mentioned", default=None)
    ease_of_use: Optional[str] = Field(description="Usability assessment if mentioned", default=None)

class ProductReview(BaseModel):
    """Complete structured product review analysis"""
    product_info: ProductInfo
    metrics: ReviewMetrics
    aspects: ReviewAspects
    
    # Key insights
    main_positives: List[str] = Field(description="Main positive points mentioned", default=[])
    main_negatives: List[str] = Field(description="Main negative points mentioned", default=[])
    would_recommend: Optional[bool] = Field(description="Whether reviewer would recommend", default=None)
    
    # Summary
    summary: str = Field(description="Brief summary of the review")
    key_phrases: List[str] = Field(description="Important phrases from the review", default=[])

    @validator('key_phrases')
    def limit_key_phrases(cls, v):
        """Limit key phrases to maximum of 5"""
        return v[:5] if len(v) > 5 else v

# Create the product review agent
product_review_agent = Agent(
    name="Product Review Analyzer",
    instructions="""
    You are a product review analysis expert that extracts structured data 
    from customer product reviews.
    
    Analyze the review text and extract:
    
    PRODUCT INFO:
    - Product name, brand, category, and price if mentioned
    - Infer category from context if not explicitly stated
    
    REVIEW METRICS:
    - Star rating (1-5) based on review tone
    - Sentiment classification (very_positive to very_negative)
    - Confidence score for sentiment analysis
    - Approximate word count
    
    REVIEW ASPECTS:
    - Quality, value for money, shipping, customer service, ease of use
    - Only include aspects that are actually mentioned
    
    KEY INSIGHTS:
    - Main positive and negative points
    - Whether they would recommend (if stated or implied)
    - Brief summary and key phrases
    
    RATING GUIDELINES:
    - 5 stars: Excellent, highly satisfied, "amazing", "perfect"
    - 4 stars: Good, satisfied, minor issues
    - 3 stars: Okay, mixed feelings, "decent"
    - 2 stars: Poor, unsatisfied, significant issues
    - 1 star: Terrible, very unsatisfied, "worst"
    
    SENTIMENT GUIDELINES:
    - very_positive: Extremely enthusiastic, highly recommended
    - positive: Generally satisfied, good experience
    - neutral: Mixed or balanced opinion
    - negative: Generally unsatisfied, disappointed
    - very_negative: Extremely dissatisfied, angry
    
    Always return a valid JSON object matching the ProductReview schema.
    """,
    output_type=ProductReview
)

def demonstrate_review_analysis():
    """Demonstrate the product review agent with various examples"""
    print("🎯 OpenAI Agents SDK - Tutorial 2: Product Review Agent")
    print("=" * 60)
    print()
    
    # Test cases with different types of reviews
    test_reviews = [
        {
            "title": "Positive Electronics Review",
            "review": "This MacBook Pro M2 is absolutely incredible! The battery life lasts all day, the screen is gorgeous, and it's lightning fast. Worth every penny of the $2,499 I paid. Apple really knocked it out of the park. The build quality is premium and it handles video editing like a dream. Highly recommend to any creative professional!"
        },
        {
            "title": "Mixed Clothing Review", 
            "review": "The Nike running shoes are decent for the price ($120). Comfortable for short runs but the sizing runs a bit small. Quality seems okay but not amazing. Shipping was fast though, arrived in 2 days. Customer service was helpful when I had questions. Would maybe recommend if you size up."
        },
        {
            "title": "Negative Food Review",
            "review": "Terrible experience with this organic coffee subscription. The beans taste stale and bitter, nothing like the description. Customer service ignored my complaints for weeks. Way overpriced at $35/month for this quality. Save your money and buy local. Will not be ordering again."
        },
        {
            "title": "Neutral Home Product Review",
            "review": "The IKEA desk lamp does its job. Easy to assemble and decent lighting for work. Not the brightest but sufficient. Build quality is what you'd expect for $25. The cord could be longer. It's an okay purchase, nothing special but functional."
        }
    ]
    
    for i, test_case in enumerate(test_reviews, 1):
        print(f"=== Review Analysis {i}: {test_case['title']} ===")
        print("Original Review:")
        print(f'"{test_case["review"]}"')
        print()
        
        try:
            # Analyze the review
            result = Runner.run_sync(product_review_agent, test_case["review"])
            analysis = result.final_output
            
            print("📊 STRUCTURED ANALYSIS:")
            print(f"🏷️  Product: {analysis.product_info.name or 'Not specified'}")
            print(f"🏢 Brand: {analysis.product_info.brand or 'Not specified'}")
            print(f"📱 Category: {analysis.product_info.category.value.title()}")
            if analysis.product_info.price_mentioned:
                print(f"💰 Price: {analysis.product_info.price_mentioned}")
            
            print(f"\n⭐ Rating: {analysis.metrics.rating}/5 stars")
            print(f"😊 Sentiment: {analysis.metrics.sentiment.value.replace('_', ' ').title()}")
            print(f"🎯 Confidence: {analysis.metrics.confidence_score:.1%}")
            print(f"📝 Word Count: ~{analysis.metrics.word_count}")
            
            if analysis.main_positives:
                print(f"\n✅ Positives: {', '.join(analysis.main_positives)}")
            if analysis.main_negatives:
                print(f"❌ Negatives: {', '.join(analysis.main_negatives)}")
            
            if analysis.would_recommend is not None:
                recommend_text = "Yes" if analysis.would_recommend else "No"
                print(f"👍 Would Recommend: {recommend_text}")
            
            print(f"\n📋 Summary: {analysis.summary}")
            
            if analysis.key_phrases:
                print(f"🔑 Key Phrases: {', '.join(analysis.key_phrases)}")
            
            # Show aspects that were mentioned
            aspects_mentioned = []
            if analysis.aspects.quality:
                aspects_mentioned.append(f"Quality: {analysis.aspects.quality}")
            if analysis.aspects.value_for_money:
                aspects_mentioned.append(f"Value: {analysis.aspects.value_for_money}")
            if analysis.aspects.shipping:
                aspects_mentioned.append(f"Shipping: {analysis.aspects.shipping}")
            if analysis.aspects.customer_service:
                aspects_mentioned.append(f"Service: {analysis.aspects.customer_service}")
            if analysis.aspects.ease_of_use:
                aspects_mentioned.append(f"Usability: {analysis.aspects.ease_of_use}")
            
            if aspects_mentioned:
                print(f"\n🔍 Specific Aspects: {' | '.join(aspects_mentioned)}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
        print("-" * 60)
        print()

def interactive_mode():
    """Interactive mode for analyzing product reviews"""
    print("=== Interactive Product Review Analysis ===")
    print("Paste a product review and I'll extract structured data from it.")
    print("Type 'quit' to exit.")
    print()
    
    while True:
        review_text = input("Product Review: ").strip()
        
        if review_text.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye!")
            break
        
        if not review_text:
            continue
        
        try:
            print("\nAnalyzing review...")
            result = Runner.run_sync(product_review_agent, review_text)
            analysis = result.final_output
            
            print("\n" + "="*50)
            print("📊 REVIEW ANALYSIS COMPLETE")
            print("="*50)
            
            # Product Information
            print("🏷️  PRODUCT INFO:")
            print(f"   Name: {analysis.product_info.name or 'Not specified'}")
            print(f"   Brand: {analysis.product_info.brand or 'Not specified'}")
            print(f"   Category: {analysis.product_info.category.value.title()}")
            if analysis.product_info.price_mentioned:
                print(f"   Price: {analysis.product_info.price_mentioned}")
            
            # Metrics
            print(f"\n📊 METRICS:")
            print(f"   Rating: {analysis.metrics.rating}/5 ⭐")
            print(f"   Sentiment: {analysis.metrics.sentiment.value.replace('_', ' ').title()}")
            print(f"   Confidence: {analysis.metrics.confidence_score:.1%}")
            
            # Key Points
            if analysis.main_positives:
                print(f"\n✅ POSITIVES: {', '.join(analysis.main_positives)}")
            if analysis.main_negatives:
                print(f"\n❌ NEGATIVES: {', '.join(analysis.main_negatives)}")
            
            # Summary
            print(f"\n📋 SUMMARY: {analysis.summary}")
            
            print("="*50)
            print()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print()

def main():
    """Main function"""
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please create a .env file with your OpenAI API key")
        return
    
    try:
        # Run demonstrations
        demonstrate_review_analysis()
        
        # Interactive mode
        interactive_mode()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
