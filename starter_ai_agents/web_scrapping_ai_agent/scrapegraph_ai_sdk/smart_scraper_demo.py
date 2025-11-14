"""
ScrapeGraph AI SmartScraper Demo
Extract structured data from websites using natural language prompts
"""

import os
from scrapegraph_py import Client
from pydantic import BaseModel, Field
from typing import List, Optional
import json


def basic_scraping_example():
    """Basic web scraping with natural language."""
    
    print("=" * 80)
    print("🕷️  SCRAPEGRAPH AI - SMART SCRAPER DEMO")
    print("=" * 80)
    
    # Initialize client
    api_key = os.getenv("SGAI_API_KEY")
    if not api_key:
        print("\n❌ Error: SGAI_API_KEY environment variable not set")
        print("💡 Get your API key at: https://scrapegraphai.com")
        print("   Then run: export SGAI_API_KEY='your-key'")
        return
    
    client = Client(api_key=api_key)
    
    # Check credits
    try:
        balance = client.get_credits()
        print(f"\n💳 Available credits: {balance.credits}")
    except Exception as e:
        print(f"\n⚠️  Could not check credits: {e}")
    
    print("\n" + "=" * 80)
    print("Example 1: Extract Product Information")
    print("=" * 80)
    
    # Example website (you can change this)
    url = "https://www.scrapethissite.com/pages/simple/"
    
    print(f"\n🔍 Scraping: {url}")
    print("📋 Prompt: Extract country names, capitals, and population")
    
    try:
        response = client.smartscraper(
            website_url=url,
            user_prompt="Extract the first 5 countries with their names, capitals, and population"
        )
        
        print("\n✅ Results:")
        print(json.dumps(response.result, indent=2))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def schema_validation_example():
    """Scraping with Pydantic schema validation."""
    
    print("\n" + "=" * 80)
    print("Example 2: Schema Validation with Pydantic")
    print("=" * 80)
    
    # Define data structure
    class Country(BaseModel):
        name: str
        capital: str
        population: int
        area: Optional[float] = None
    
    class Countries(BaseModel):
        countries: List[Country]
    
    api_key = os.getenv("SGAI_API_KEY")
    if not api_key:
        return
    
    client = Client(api_key=api_key)
    
    url = "https://www.scrapethissite.com/pages/simple/"
    
    print(f"\n🔍 Scraping: {url}")
    print("📋 Using Pydantic schema for validation")
    
    try:
        response = client.smartscraper(
            website_url=url,
            user_prompt="Extract the first 3 countries with name, capital, and population",
            output_schema=Countries.model_json_schema()
        )
        
        # Validate with Pydantic
        countries = Countries(**response.result)
        
        print("\n✅ Validated Results:")
        for country in countries.countries:
            print(f"\n  🌍 {country.name}")
            print(f"     Capital: {country.capital}")
            print(f"     Population: {country.population:,}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def html_scraping_example():
    """Scrape from HTML string instead of URL."""
    
    print("\n" + "=" * 80)
    print("Example 3: Scraping from HTML String")
    print("=" * 80)
    
    api_key = os.getenv("SGAI_API_KEY")
    if not api_key:
        return
    
    client = Client(api_key=api_key)
    
    # Sample HTML
    html_content = """
    <html>
    <body>
        <div class="products">
            <div class="product">
                <h2>Laptop Pro</h2>
                <p class="price">$1,299</p>
                <p class="stock">In Stock</p>
            </div>
            <div class="product">
                <h2>Magic Mouse</h2>
                <p class="price">$79</p>
                <p class="stock">Out of Stock</p>
            </div>
            <div class="product">
                <h2>Wireless Keyboard</h2>
                <p class="price">$89</p>
                <p class="stock">In Stock</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    print("\n📄 Scraping from HTML content")
    
    try:
        response = client.smartscraper(
            website_html=html_content,
            user_prompt="Extract all products with their names, prices, and stock status"
        )
        
        print("\n✅ Results:")
        print(json.dumps(response.result, indent=2))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def custom_schema_example():
    """Use custom JSON schema for precise output structure."""
    
    print("\n" + "=" * 80)
    print("Example 4: Custom JSON Schema")
    print("=" * 80)
    
    api_key = os.getenv("SGAI_API_KEY")
    if not api_key:
        return
    
    client = Client(api_key=api_key)
    
    # Define custom schema
    schema = {
        "type": "object",
        "properties": {
            "countries": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "country_name": {"type": "string"},
                        "capital_city": {"type": "string"},
                        "population_count": {"type": "number"}
                    },
                    "required": ["country_name", "capital_city", "population_count"]
                }
            }
        },
        "required": ["countries"]
    }
    
    url = "https://www.scrapethissite.com/pages/simple/"
    
    print(f"\n🔍 Scraping: {url}")
    print("📋 Using custom JSON schema")
    
    try:
        response = client.smartscraper(
            website_url=url,
            user_prompt="Extract first 3 countries",
            output_schema=schema
        )
        
        print("\n✅ Results:")
        print(json.dumps(response.result, indent=2))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def spa_rendering_example():
    """Scrape Single Page Applications with JavaScript rendering."""
    
    print("\n" + "=" * 80)
    print("Example 5: JavaScript Rendering for SPAs")
    print("=" * 80)
    
    api_key = os.getenv("SGAI_API_KEY")
    if not api_key:
        return
    
    client = Client(api_key=api_key)
    
    # Example SPA site
    url = "https://www.scrapethissite.com/pages/ajax-javascript/"
    
    print(f"\n🔍 Scraping SPA: {url}")
    print("⚙️  JavaScript rendering: ENABLED")
    
    try:
        response = client.smartscraper(
            website_url=url,
            user_prompt="Extract the years and number of Oscar wins",
            render_heavy_js=True  # Enable JS rendering
        )
        
        print("\n✅ Results:")
        print(json.dumps(response.result, indent=2))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def main():
    """Run all examples."""
    
    # Basic scraping
    basic_scraping_example()
    
    # Schema validation
    schema_validation_example()
    
    # HTML scraping
    html_scraping_example()
    
    # Custom schema
    custom_schema_example()
    
    # SPA rendering
    spa_rendering_example()
    
    print("\n" + "=" * 80)
    print("🎉 Demo completed!")
    print("\n💡 Next steps:")
    print("   - Try with your own URLs")
    print("   - Customize the prompts")
    print("   - Define your own schemas")
    print("   - Run the Streamlit app: streamlit run scrapegraph_app.py")
    print("\n🔗 Resources:")
    print("   - GitHub: https://github.com/ScrapeGraphAI/scrapegraph-sdk")
    print("   - Docs: https://docs.scrapegraphai.com")
    print("=" * 80)


if __name__ == "__main__":
    main()

