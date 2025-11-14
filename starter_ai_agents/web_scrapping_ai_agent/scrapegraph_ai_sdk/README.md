# 🕷️ ScrapeGraph AI SDK - Intelligent Web Scraping

Powerful AI-powered web scraping using the official [ScrapeGraph AI SDK](https://github.com/ScrapeGraphAI/scrapegraph-sdk). Extract structured data, convert to markdown, crawl multiple pages, and perform AI-powered web searches.

## 📋 Overview

ScrapeGraph AI SDK provides cloud-based AI scraping capabilities with natural language prompts. No complex selectors or XPath needed - just describe what you want to extract!

### 🌟 Key Features

- 🤖 **SmartScraper**: Extract structured data with natural language
- 🔍 **SearchScraper**: AI-powered web search with structured results
- 📝 **Markdownify**: Convert webpages to clean markdown
- 🕷️ **SmartCrawler**: Intelligent multi-page crawling
- 🤖 **AgenticScraper**: Automated browser actions
- ⏰ **Scheduled Jobs**: Cron-based scraping workflows
- 💳 **Credits Management**: Monitor API usage

## 🚀 Features

- **Natural Language Extraction**: No CSS selectors needed
- **Schema Validation**: Structured output with Pydantic
- **Multiple Formats**: JSON, Markdown, custom schemas
- **High Performance**: Concurrent processing
- **Enterprise Ready**: Production-grade reliability

## 📦 Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## 🔑 Setup

1. Get your API key from [ScrapeGraph AI](https://scrapegraphai.com)

2. Set your API key as environment variable:

```bash
export SGAI_API_KEY='your-api-key-here'
```

## 💻 Usage

### Basic Smart Scraping

Run the basic scraper demo:

```bash
python smart_scraper_demo.py
```

### Interactive Web App

Run the Streamlit app for interactive scraping:

```bash
streamlit run scrapegraph_app.py
```

### Search Scraping

Run the search scraper:

```bash
python search_scraper_demo.py
```

### Smart Crawler

Run the multi-page crawler:

```bash
python smart_crawler_demo.py
```

## 📚 Examples

### 1. SmartScraper - Extract Product Data

```python
from scrapegraph_py import Client

client = Client(api_key="your-api-key")

# Extract product information
response = client.smartscraper(
    website_url="https://example.com/product",
    user_prompt="Extract product name, price, description, and availability"
)

print(response.result)
```

### 2. SearchScraper - AI Web Search

```python
# Search and extract structured data
response = client.smartscraper(
    user_prompt="Find the top 5 AI news websites with their names, URLs, and descriptions",
    num_results=5
)

for result in response.result:
    print(f"{result['name']}: {result['url']}")
```

### 3. Markdownify - Convert to Markdown

```python
# Convert webpage to markdown
response = client.markdownify(
    website_url="https://example.com/article"
)

print(response.result)  # Clean markdown output
```

### 4. SmartCrawler - Multi-page Extraction

```python
# Crawl and extract from multiple pages
request_id = client.smartcrawler(
    website_url="https://docs.example.com",
    user_prompt="Extract all API endpoints with their methods and descriptions",
    max_pages=10,
    depth=2
)

# Fetch results
results = client.smartcrawler_get(request_id)
```

### 5. Schema Validation with Pydantic

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str
    price: float
    in_stock: bool
    rating: float = Field(ge=0, le=5)

# Extract with schema validation
response = client.smartscraper(
    website_url="https://example.com/product",
    user_prompt="Extract product details",
    output_schema=Product.model_json_schema()
)

product = Product(**response.result)
```

## 🎯 Use Cases

### E-commerce Data Extraction

```python
# Extract product catalog
products = client.smartscraper(
    website_url="https://shop.example.com",
    user_prompt="Extract all products with name, price, image, and availability"
)
```

### News & Content Aggregation

```python
# Convert articles to markdown for processing
article_md = client.markdownify(
    website_url="https://news.example.com/article"
)
```

### Competitive Intelligence

```python
# Search and analyze competitor data
competitors = client.smartscraper(
    user_prompt="Find top 10 SaaS companies in AI space with pricing info",
    num_results=10
)
```

### Documentation Scraping

```python
# Crawl entire documentation site
request_id = client.smartcrawler(
    website_url="https://docs.example.com",
    user_prompt="Extract all function signatures, parameters, and examples",
    max_pages=50
)
```

## 🔧 Advanced Features

### Custom Output Schemas

Define exactly what data you want:

```python
schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "author": {"type": "string"},
        "date": {"type": "string", "format": "date"},
        "content": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}}
    }
}

response = client.smartscraper(
    website_url="https://blog.example.com/post",
    user_prompt="Extract blog post information",
    output_schema=schema
)
```

### JavaScript Rendering

For dynamic Single Page Applications:

```python
response = client.smartscraper(
    website_url="https://spa.example.com",
    user_prompt="Extract data",
    render_heavy_js=True  # Enable JS rendering
)
```

### Stealth Mode

Avoid bot detection:

```python
response = client.smartscraper(
    website_url="https://protected-site.com",
    user_prompt="Extract data",
    stealth=True  # Enable stealth mode
)
```

### Scheduled Jobs

Create recurring scraping tasks:

```python
# Create scheduled job (daily at 9 AM)
job = client.create_scheduled_job(
    name="Daily Product Scrape",
    schedule="0 9 * * *",  # Cron expression
    scraper_type="smartscraper",
    config={
        "website_url": "https://shop.example.com",
        "user_prompt": "Extract all products"
    }
)

# List all scheduled jobs
jobs = client.list_scheduled_jobs()

# Get job execution history
history = client.get_job_history(job.id)
```

## 📊 Comparison with Local Library

| Feature | SDK (Cloud API) | Local Library |
|---------|----------------|---------------|
| Setup | API key only | Full installation |
| Processing | Cloud-based | Local compute |
| Scalability | Unlimited | Hardware limited |
| Maintenance | Managed | Self-managed |
| Credits | Pay-per-use | Free (local) |
| Speed | Very fast | Depends on hardware |
| Features | All features | Core features |

**Use SDK when:**
- ✅ You want managed infrastructure
- ✅ You need high scalability
- ✅ You prefer pay-per-use pricing
- ✅ You want latest features

**Use Local Library when:**
- ✅ You have sensitive data
- ✅ You prefer self-hosted
- ✅ You have available compute
- ✅ You want full control

## 💰 Credits & Pricing

Different operations use different credit amounts:

- **SmartScraper**: 10 credits per page
- **Markdownify**: 2 credits per page
- **SearchScraper**: 10 credits per result
- **SmartCrawler**: Variable (based on pages)
- **Scrape**: 1 credit per page

Check your credits:

```python
balance = client.get_credits()
print(f"Available credits: {balance.credits}")
```

## 🔗 Integrations

ScrapeGraph AI SDK integrates with:

- **LLM Frameworks**: Langchain, LlamaIndex, Crew.ai, CamelAI
- **Low-code**: Pipedream, Bubble, Zapier, n8n, LangFlow
- **MCP Server**: Model Context Protocol support

See the [integration docs](https://docs.scrapegraphai.com/integrations) for details.

## 📖 API Reference

### Client

```python
from scrapegraph_py import Client

client = Client(api_key="your-api-key")
```

### SmartScraper

```python
response = client.smartscraper(
    website_url: str | None = None,
    website_html: str | None = None,
    user_prompt: str,
    output_schema: dict | None = None,
    render_heavy_js: bool = False,
    stealth: bool = False
)
```

### SearchScraper

```python
response = client.smartscraper(
    user_prompt: str,
    num_results: int = 3,
    output_schema: dict | None = None
)
```

### Markdownify

```python
response = client.markdownify(
    website_url: str,
    render_heavy_js: bool = False
)
```

### SmartCrawler

```python
request_id = client.smartcrawler(
    url: str,
    user_prompt: str,
    max_pages: int | None = None,
    depth: int | None = None,
    same_domain_only: bool = True
)

results = client.smartcrawler_get(request_id)
```

## 🐛 Troubleshooting

### Common Issues

**Issue**: `Authentication failed`
```bash
# Solution: Check your API key
export SGAI_API_KEY='your-actual-key'
```

**Issue**: `Insufficient credits`
```python
# Solution: Check balance and recharge
balance = client.get_credits()
print(f"Credits: {balance.credits}")
```

**Issue**: `Rate limit exceeded`
```python
# Solution: Add delays between requests
import time
time.sleep(1)  # Wait 1 second between calls
```

## 🤝 Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## 📄 License

This example code is provided as-is for educational purposes.
ScrapeGraph AI SDK is licensed under MIT License.

## 🔗 Resources

- **GitHub**: https://github.com/ScrapeGraphAI/scrapegraph-sdk
- **Documentation**: https://docs.scrapegraphai.com
- **API Docs**: https://docs.scrapegraphai.com/api
- **Python SDK**: https://docs.scrapegraphai.com/sdk/python
- **JavaScript SDK**: https://docs.scrapegraphai.com/sdk/javascript
- **Get API Key**: https://scrapegraphai.com

## 💬 Support

- 📧 Email: support@scrapegraphai.com
- 💻 GitHub Issues: [Create an issue](https://github.com/ScrapeGraphAI/scrapegraph-sdk/issues)
- 🌟 Feature Requests: [Request a feature](https://github.com/ScrapeGraphAI/scrapegraph-sdk/issues/new)

---

Made with ❤️ by [ScrapeGraph AI](https://scrapegraphai.com)

