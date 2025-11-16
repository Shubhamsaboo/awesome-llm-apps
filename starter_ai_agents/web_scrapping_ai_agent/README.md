# 🕷️ Web Scraping AI Agent

AI-powered web scraping using **ScrapeGraph AI** - extract structured data from websites using natural language prompts. This folder contains two implementations:

1. **🏠 Local Library** - Using `scrapegraphai` library (runs locally)
2. **☁️ Cloud SDK** - Using ScrapeGraph AI API (managed service)

---

## 📁 What's Inside

### 🏠 Local Library Version
**Files**: `ai_scrapper.py`, `local_ai_scrapper.py`

Use the open-source ScrapeGraph AI library that runs on your local machine.

**✅ Pros:**
- Free to use (no API costs)
- Full control over execution
- Privacy-friendly (all data stays local)

**❌ Cons:**
- Requires local installation and dependencies
- Limited by your hardware
- Need to manage updates

**Quick Start:**
```bash
pip install -r requirements.txt
streamlit run ai_scrapper.py
```

---

### ☁️ Cloud SDK Version
**Folder**: `scrapegraph_ai_sdk/`

Use the managed ScrapeGraph AI API with advanced features and no setup required.

**✅ Pros:**
- No setup required (just API key)
- Scalable and fast
- Advanced features (SmartCrawler, SearchScraper, Markdownify)
- Always up-to-date

**❌ Cons:**
- Pay-per-use (credit-based)
- Requires internet connection

**Quick Start:**
```bash
cd scrapegraph_ai_sdk/
pip install -r requirements.txt
export SGAI_API_KEY='your-api-key'
python quickstart.py
```

**📖 Full Documentation**: [See scrapegraph_ai_sdk/README.md](scrapegraph_ai_sdk/README.md)

---

## 🚀 Getting Started

### Local Library Version

1. **Clone the repository**
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/starter_ai_agents/web_scrapping_ai_agent
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Get your OpenAI API Key**
- Sign up for an [OpenAI account](https://platform.openai.com/)
- Obtain your API key

4. **Run the Streamlit App**
```bash
streamlit run ai_scrapper.py
# Or for local models:
streamlit run local_ai_scrapper.py
```

### Cloud SDK Version

1. **Navigate to SDK folder**
```bash
cd scrapegraph_ai_sdk/
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Get your ScrapeGraph AI API Key**
- Sign up at [scrapegraphai.com](https://scrapegraphai.com)
- Get your API key

4. **Set API key**
```bash
export SGAI_API_KEY='your-api-key-here'
```

5. **Run demos**
```bash
# Quick test
python quickstart.py

# SmartScraper demo
python smart_scraper_demo.py

# Interactive app
streamlit run scrapegraph_app.py
```

---

## 📊 Feature Comparison

| Feature | Local Library | Cloud SDK |
|---------|--------------|-----------|
| **Setup** | Install dependencies | API key only |
| **Cost** | Free (+ LLM costs) | Pay-per-use |
| **Processing** | Your hardware | Cloud-based |
| **Speed** | Depends on hardware | Fast & optimized |
| **SmartScraper** | ✅ | ✅ |
| **SearchScraper** | ❌ | ✅ |
| **SmartCrawler** | ❌ | ✅ |
| **Markdownify** | ❌ | ✅ |
| **Scheduled Jobs** | ❌ | ✅ |
| **Scalability** | Limited | Unlimited |
| **Maintenance** | Self-managed | Fully managed |

---

## 💡 Use Cases

### E-commerce Scraping
```python
# Extract product information
prompt = "Extract product names, prices, and availability"
```

### Content Aggregation
```python
# Convert articles to structured data
prompt = "Extract article title, author, date, and main content"
```

### Competitive Intelligence
```python
# Monitor competitor websites
prompt = "Extract pricing, features, and updates"
```

### Lead Generation
```python
# Extract contact information
prompt = "Find company names, emails, and phone numbers"
```

---

## 🔧 How It Works

### Local Library
1. You provide your OpenAI API key
2. Select the model (GPT-4o, GPT-5, or local models)
3. Enter the URL and extraction prompt
4. The app uses ScrapeGraphAI to scrape and extract data locally
5. Results are displayed in the app

### Cloud SDK
1. You provide your ScrapeGraph AI API key
2. Choose the scraping method (SmartScraper, SearchScraper, etc.)
3. Define extraction prompt and optional output schema
4. API processes the request in the cloud
5. Structured results are returned

---

## 🌟 Cloud SDK Features

### 🤖 SmartScraper
Extract structured data using natural language:
```python
response = client.smartscraper(
    website_url="https://example.com",
    user_prompt="Extract all products with prices"
)
```

### 🔍 SearchScraper
AI-powered web search with structured results:
```python
response = client.smartscraper(
    user_prompt="Find top 5 AI news websites",
    num_results=5
)
```

### 📝 Markdownify
Convert webpages to clean markdown:
```python
response = client.markdownify(
    website_url="https://example.com/article"
)
```

### 🕷️ SmartCrawler
Crawl multiple pages intelligently:
```python
request_id = client.smartcrawler(
    url="https://docs.example.com",
    user_prompt="Extract all API endpoints",
    max_pages=50
)
```

---

## 📖 Documentation

- **Local Library**: [ScrapeGraphAI GitHub](https://github.com/VinciGit00/Scrapegraph-ai)
- **Cloud SDK**: [See scrapegraph_ai_sdk/README.md](scrapegraph_ai_sdk/README.md)
- **API Docs**: https://docs.scrapegraphai.com

---

## 🤝 Which Version Should I Use?

**Use Local Library if:**
- ✅ You want free, open-source solution
- ✅ You have good hardware
- ✅ You need full control
- ✅ Privacy is critical

**Use Cloud SDK if:**
- ✅ You want quick setup
- ✅ You need advanced features
- ✅ You want scalability
- ✅ You prefer managed service

**💡 Pro Tip**: Start with the local version to learn, then switch to SDK for production!
