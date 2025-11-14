"""
ScrapeGraph AI SmartCrawler Demo
Intelligently crawl and extract data from multiple pages
"""

import os
from scrapegraph_py import Client
import json
import time


def basic_crawler_example():
    """Basic multi-page crawling."""
    
    print("=" * 80)
    print("🕷️  SCRAPEGRAPH AI - SMART CRAWLER DEMO")
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
    print("Example 1: Basic Website Crawling")
    print("=" * 80)
    
    # Start crawling
    url = "https://www.scrapethissite.com/pages/"
    prompt = "Extract all page titles and descriptions"
    
    print(f"\n🔍 Starting crawler...")
    print(f"   URL: {url}")
    print(f"   Prompt: {prompt}")
    print(f"   Max pages: 5")
    print(f"   Depth: 1")
    
    try:
        # Initiate crawl
        request_id = client.smartcrawler(
            url=url,
            user_prompt=prompt,
            max_pages=5,
            depth=1,
            same_domain_only=True
        )
        
        print(f"\n✅ Crawler started!")
        print(f"   Request ID: {request_id}")
        print("\n⏳ Waiting for results...")
        
        # Poll for results
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                results = client.smartcrawler_get(request_id)
                
                if results:
                    print("\n✅ Crawl completed!")
                    print(f"\n📊 Results:")
                    print(json.dumps(results, indent=2))
                    break
                    
            except Exception as e:
                if "not ready" in str(e).lower() or "pending" in str(e).lower():
                    print(f"   Attempt {attempt + 1}/{max_attempts}...")
                    time.sleep(2)
                else:
                    raise
        else:
            print("\n⏰ Timeout waiting for results")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def documentation_crawler_example():
    """Crawl documentation sites."""
    
    print("\n" + "=" * 80)
    print("Example 2: Documentation Crawling")
    print("=" * 80)
    
    api_key = os.getenv("SGAI_API_KEY")
    if not api_key:
        return
    
    client = Client(api_key=api_key)
    
    # Example: Crawl a documentation site
    url = "https://docs.python.org/3/"
    prompt = "Extract all function names, descriptions, and code examples"
    
    print(f"\n🔍 Crawling documentation...")
    print(f"   URL: {url}")
    print(f"   Max pages: 10")
    print(f"   Depth: 2")
    
    try:
        request_id = client.smartcrawler(
            url=url,
            user_prompt=prompt,
            max_pages=10,
            depth=2,
            same_domain_only=True
        )
        
        print(f"\n✅ Crawler initiated: {request_id}")
        print("⏳ Crawling in progress...")
        print("💡 This may take a few minutes for multiple pages")
        
        # Note: In production, you'd poll for results
        # For this demo, we just show how to initiate
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def product_catalog_crawler():
    """Crawl e-commerce product catalogs."""
    
    print("\n" + "=" * 80)
    print("Example 3: Product Catalog Crawling")
    print("=" * 80)
    
    api_key = os.getenv("SGAI_API_KEY")
    if not api_key:
        return
    
    client = Client(api_key=api_key)
    
    url = "https://www.scrapethissite.com/pages/simple/"
    prompt = "Extract all country information including name, capital, population, and area"
    
    print(f"\n🔍 Crawling product catalog...")
    print(f"   URL: {url}")
    print(f"   Extraction mode: AI")
    
    try:
        request_id = client.smartcrawler(
            url=url,
            prompt=prompt,
            extraction_mode="ai",
            max_pages=10,
            depth=1
        )
        
        print(f"\n✅ Crawler started: {request_id}")
        print("⏳ Processing...")
        
        # Poll for results
        for i in range(20):
            try:
                results = client.smartcrawler_get(request_id)
                if results:
                    print("\n✅ Results ready!")
                    print(json.dumps(results, indent=2)[:500] + "...")
                    break
            except:
                time.sleep(3)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def markdown_crawler_example():
    """Crawl and convert pages to markdown."""
    
    print("\n" + "=" * 80)
    print("Example 4: Markdown Conversion Crawler")
    print("=" * 80)
    
    api_key = os.getenv("SGAI_API_KEY")
    if not api_key:
        return
    
    client = Client(api_key=api_key)
    
    url = "https://www.scrapethissite.com/pages/"
    
    print(f"\n🔍 Converting pages to markdown...")
    print(f"   URL: {url}")
    print(f"   Mode: Markdown")
    
    try:
        request_id = client.smartcrawler(
            url=url,
            extraction_mode="markdown",
            max_pages=5,
            depth=1
        )
        
        print(f"\n✅ Crawler initiated: {request_id}")
        print("⏳ Converting to markdown...")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def custom_depth_crawl():
    """Demonstrate different crawl depths."""
    
    print("\n" + "=" * 80)
    print("Example 5: Custom Depth Crawling")
    print("=" * 80)
    
    api_key = os.getenv("SGAI_API_KEY")
    if not api_key:
        return
    
    client = Client(api_key=api_key)
    
    url = "https://www.scrapethissite.com/"
    prompt = "Extract page titles and main content"
    
    print("\n🔍 Comparing different crawl depths:")
    
    # Depth 1: Only linked pages from start URL
    print("\n   Depth 1: Direct links only")
    
    try:
        request_id_1 = client.smartcrawler(
            url=url,
            user_prompt=prompt,
            depth=1,
            max_pages=5
        )
        print(f"   Request ID: {request_id_1}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    # Depth 2: Two levels deep
    print("\n   Depth 2: Two levels deep")
    
    try:
        request_id_2 = client.smartcrawler(
            url=url,
            user_prompt=prompt,
            depth=2,
            max_pages=10
        )
        print(f"   Request ID: {request_id_2}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n💡 Higher depth = more pages discovered")
    print("💡 Use max_pages to control costs")


def main():
    """Run all crawler examples."""
    
    print("\n⚠️  Note: SmartCrawler is asynchronous and may take time")
    print("💡 Results are fetched via polling or webhooks")
    
    # Basic crawler
    basic_crawler_example()
    
    # Documentation crawler
    documentation_crawler_example()
    
    # Product catalog
    product_catalog_crawler()
    
    # Markdown crawler
    markdown_crawler_example()
    
    # Custom depth
    custom_depth_crawl()
    
    print("\n" + "=" * 80)
    print("🎉 Crawler Demo completed!")
    print("\n💡 Best Practices:")
    print("   - Start with small max_pages to test")
    print("   - Use same_domain_only to avoid following external links")
    print("   - Set appropriate depth based on site structure")
    print("   - Monitor credit usage for large crawls")
    print("\n🔗 Resources:")
    print("   - GitHub: https://github.com/ScrapeGraphAI/scrapegraph-sdk")
    print("   - Docs: https://docs.scrapegraphai.com")
    print("=" * 80)


if __name__ == "__main__":
    main()

