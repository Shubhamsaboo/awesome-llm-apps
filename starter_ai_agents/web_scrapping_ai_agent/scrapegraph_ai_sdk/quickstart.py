"""
ScrapeGraph AI Quick Start
Quick test to verify installation and basic functionality
"""

import os


def check_installation():
    """Verify ScrapeGraph AI SDK is installed."""
    try:
        from scrapegraph_py import Client
        print("✅ scrapegraph-py is installed")
        return True
    except ImportError:
        print("❌ scrapegraph-py not found")
        print("💡 Install with: pip install scrapegraph-py")
        return False


def check_api_key():
    """Check if API key is configured."""
    api_key = os.getenv("SGAI_API_KEY")
    if api_key:
        print(f"✅ API key found: {api_key[:10]}...")
        return api_key
    else:
        print("❌ SGAI_API_KEY not found")
        print("💡 Get your API key at: https://scrapegraphai.com")
        print("   Then set it: export SGAI_API_KEY='your-key'")
        return None


def test_connection(api_key):
    """Test API connection."""
    from scrapegraph_py import Client
    
    try:
        client = Client(api_key=api_key)
        balance = client.get_credits()
        print(f"✅ Connection successful!")
        print(f"💳 Available credits: {balance.credits}")
        return client
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None


def quick_scrape_test(client):
    """Run a quick scraping test."""
    print("\n" + "=" * 60)
    print("Running quick scrape test...")
    print("=" * 60)
    
    # Simple HTML to scrape
    html = """
    <html>
    <body>
        <h1>Welcome to ScrapeGraph AI</h1>
        <div class="features">
            <div class="feature">
                <h3>SmartScraper</h3>
                <p>Extract structured data with natural language</p>
            </div>
            <div class="feature">
                <h3>SearchScraper</h3>
                <p>AI-powered web search</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        response = client.smartscraper(
            website_html=html,
            user_prompt="Extract all feature names and descriptions"
        )
        
        print("\n✅ Scrape successful!")
        print("\n📊 Results:")
        import json
        print(json.dumps(response.result, indent=2))
        
        return True
        
    except Exception as e:
        print(f"\n❌ Scrape failed: {e}")
        return False


def main():
    """Run quick start checks."""
    print("=" * 60)
    print("🕷️  SCRAPEGRAPH AI - QUICK START")
    print("=" * 60)
    print()
    
    # 1. Check installation
    if not check_installation():
        return False
    
    print()
    
    # 2. Check API key
    api_key = check_api_key()
    if not api_key:
        return False
    
    print()
    
    # 3. Test connection
    client = test_connection(api_key)
    if not client:
        return False
    
    # 4. Quick scrape test
    success = quick_scrape_test(client)
    
    print("\n" + "=" * 60)
    if success:
        print("✨ Quick start completed successfully!")
        print("\n💡 Next steps:")
        print("   1. Run full demo: python smart_scraper_demo.py")
        print("   2. Try search: python search_scraper_demo.py")
        print("   3. Launch app: streamlit run scrapegraph_app.py")
    else:
        print("⚠️  Quick start completed with errors")
        print("💡 Check the error messages above")
    
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)

