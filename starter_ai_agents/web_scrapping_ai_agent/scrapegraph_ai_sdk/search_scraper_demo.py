"""
ScrapeGraph AI SearchScraper Demo
AI-powered web search with structured data extraction
"""

import os
from scrapegraph_py import Client
from pydantic import BaseModel
from typing import List
import json


class SearchResult(BaseModel):
    """Schema for search results."""
    title: str
    url: str
    description: str


class SearchResults(BaseModel):
    """Schema for multiple search results."""
    results: List[SearchResult]


def basic_search_example():
    """Basic AI-powered web search."""
    
    print("=" * 80)
    print("🔍 SCRAPEGRAPH AI - SEARCH SCRAPER DEMO")
    print("=" * 80)
    
    api_key = os.getenv("SGAI_API_KEY")
    if not api_key:
        print("\n❌ Error: SGAI_API_KEY environment variable not set")
        print("💡 Get your API key at: https://scrapegraphai.com")
        return
    
    client = Client(api_key=api_key)
    
    # Check credits
    try:
        balance = client.get_credits()
        print(f"\n💳 Available credits: {balance.credits}")
    except Exception as e:
        print(f"\n⚠️  Could not check credits: {e}")
    
    print("\n" + "=" * 80)
    print("Example 1: Basic Web Search")
    print("=" * 80)
    
    query = "Top 5 AI news websites"
    print(f"\n🔍 Query: {query}")
    
    try:
        response = client.smartscraper(
            user_prompt=query,
            num_results=5
        )
        
        print("\n✅ Results:")
        print(json.dumps(response.result, indent=2))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def structured_search_example():
    """Search with structured output schema."""
    
    print("\n" + "=" * 80)
    print("Example 2: Structured Search Results")
    print("=" * 80)
    
    api_key = os.getenv("SGAI_API_KEY")
    if not api_key:
        return
    
    client = Client(api_key=api_key)
    
    query = "Find the best Python web scraping libraries with their GitHub stars and documentation links"
    print(f"\n🔍 Query: {query}")
    
    schema = {
        "type": "object",
        "properties": {
            "libraries": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "github_url": {"type": "string"},
                        "stars": {"type": "string"},
                        "docs_url": {"type": "string"}
                    }
                }
            }
        }
    }
    
    try:
        response = client.smartscraper(
            user_prompt=query,
            num_results=5,
            output_schema=schema
        )
        
        print("\n✅ Structured Results:")
        print(json.dumps(response.result, indent=2))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def competitive_intelligence_example():
    """Use search for competitive intelligence."""
    
    print("\n" + "=" * 80)
    print("Example 3: Competitive Intelligence")
    print("=" * 80)
    
    api_key = os.getenv("SGAI_API_KEY")
    if not api_key:
        return
    
    client = Client(api_key=api_key)
    
    query = "Top SaaS companies in the web scraping space with pricing and features"
    print(f"\n🔍 Query: {query}")
    
    schema = {
        "type": "object",
        "properties": {
            "companies": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "company_name": {"type": "string"},
                        "website": {"type": "string"},
                        "pricing_model": {"type": "string"},
                        "key_features": {"type": "array", "items": {"type": "string"}},
                        "target_market": {"type": "string"}
                    }
                }
            }
        }
    }
    
    try:
        response = client.smartscraper(
            user_prompt=query,
            num_results=5,
            output_schema=schema
        )
        
        print("\n✅ Competitive Analysis:")
        if "companies" in response.result:
            for company in response.result["companies"]:
                print(f"\n  🏢 {company.get('company_name', 'N/A')}")
                print(f"     Website: {company.get('website', 'N/A')}")
                print(f"     Pricing: {company.get('pricing_model', 'N/A')}")
                if 'key_features' in company:
                    print(f"     Features: {', '.join(company['key_features'][:3])}")
        else:
            print(json.dumps(response.result, indent=2))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def news_aggregation_example():
    """Aggregate news articles on a topic."""
    
    print("\n" + "=" * 80)
    print("Example 4: News Aggregation")
    print("=" * 80)
    
    api_key = os.getenv("SGAI_API_KEY")
    if not api_key:
        return
    
    client = Client(api_key=api_key)
    
    query = "Latest AI breakthroughs in 2024 with article titles, dates, and summaries"
    print(f"\n🔍 Query: {query}")
    
    schema = {
        "type": "object",
        "properties": {
            "articles": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "source": {"type": "string"},
                        "url": {"type": "string"},
                        "date": {"type": "string"},
                        "summary": {"type": "string"}
                    }
                }
            }
        }
    }
    
    try:
        response = client.smartscraper(
            user_prompt=query,
            num_results=5,
            output_schema=schema
        )
        
        print("\n✅ News Articles:")
        if "articles" in response.result:
            for i, article in enumerate(response.result["articles"], 1):
                print(f"\n  📰 Article {i}: {article.get('title', 'N/A')}")
                print(f"     Source: {article.get('source', 'N/A')}")
                print(f"     Date: {article.get('date', 'N/A')}")
                print(f"     URL: {article.get('url', 'N/A')}")
                summary = article.get('summary', 'N/A')
                if len(summary) > 100:
                    summary = summary[:100] + "..."
                print(f"     Summary: {summary}")
        else:
            print(json.dumps(response.result, indent=2))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def market_research_example():
    """Perform market research using search."""
    
    print("\n" + "=" * 80)
    print("Example 5: Market Research")
    print("=" * 80)
    
    api_key = os.getenv("SGAI_API_KEY")
    if not api_key:
        return
    
    client = Client(api_key=api_key)
    
    query = "E-commerce platforms for small businesses with features and pricing"
    print(f"\n🔍 Query: {query}")
    
    try:
        response = client.smartscraper(
            user_prompt=query,
            num_results=5
        )
        
        print("\n✅ Market Research Results:")
        print(json.dumps(response.result, indent=2))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def main():
    """Run all search examples."""
    
    # Basic search
    basic_search_example()
    
    # Structured search
    structured_search_example()
    
    # Competitive intelligence
    competitive_intelligence_example()
    
    # News aggregation
    news_aggregation_example()
    
    # Market research
    market_research_example()
    
    print("\n" + "=" * 80)
    print("🎉 Search Demo completed!")
    print("\n💡 Use Cases:")
    print("   - Competitive analysis")
    print("   - Market research")
    print("   - News aggregation")
    print("   - Lead generation")
    print("   - Content discovery")
    print("\n🔗 Resources:")
    print("   - GitHub: https://github.com/ScrapeGraphAI/scrapegraph-sdk")
    print("   - Docs: https://docs.scrapegraphai.com")
    print("=" * 80)


if __name__ == "__main__":
    main()

