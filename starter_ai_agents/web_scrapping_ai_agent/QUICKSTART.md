# 🚀 Quick Start Guide - Web Scraping AI Agent

Choose your version and get started in minutes!

---

## 📋 Two Versions Available

### 1️⃣ **Local Library** (Free, Open Source)
✅ Best for: Learning, privacy, full control  
📁 Files: `ai_scrapper.py`, `local_ai_scrapper.py`

### 2️⃣ **Cloud SDK** (Managed Service)
✅ Best for: Production, scalability, advanced features  
📁 Folder: `scrapegraph_ai_sdk/`

---

## 🏃‍♂️ Quick Start - Local Version

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Get OpenAI API Key
👉 Sign up at [platform.openai.com](https://platform.openai.com/)

### Step 3: Run the App
```bash
streamlit run ai_scrapper.py
```

### Step 4: Use the App
1. Enter your OpenAI API key
2. Select model (GPT-4o recommended)
3. Enter website URL
4. Describe what to extract
5. Click "Scrape"!

**⏱️ Setup Time: ~2 minutes**

---

## ☁️ Quick Start - Cloud SDK

### Step 1: Navigate to SDK Folder
```bash
cd scrapegraph_ai_sdk/
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Get ScrapeGraph AI API Key
👉 Sign up at [scrapegraphai.com](https://scrapegraphai.com)

### Step 4: Set API Key
```bash
export SGAI_API_KEY='your-api-key-here'
```

### Step 5: Quick Test
```bash
python quickstart.py
```

### Step 6: Try Different Features

**SmartScraper** (extract structured data):
```bash
python smart_scraper_demo.py
```

**SearchScraper** (AI web search):
```bash
python search_scraper_demo.py
```

**SmartCrawler** (multi-page scraping):
```bash
python smart_crawler_demo.py
```

**Interactive App**:
```bash
streamlit run scrapegraph_app.py
```

**⏱️ Setup Time: ~1 minute**

---

## 🎯 Which One Should I Choose?

### Choose **Local Library** if you want:
- 🆓 Free solution (pay only for OpenAI API)
- 🔒 Privacy (all processing on your machine)
- 🎓 Learning and experimentation
- 🛠️ Full control over the process

### Choose **Cloud SDK** if you want:
- ⚡ Quick setup (no dependencies)
- 🚀 Production-ready scalability
- ✨ Advanced features (SmartCrawler, SearchScraper, Markdownify)
- 🔄 Automatic updates

---

## 💡 Example Use Cases

### E-commerce Price Monitoring
```python
# Local Version
prompt = "Extract product name, price, and availability"

# Cloud SDK
response = client.smartscraper(
    website_url="https://shop.example.com/product",
    user_prompt="Extract product name, price, and availability"
)
```

### News Aggregation
```python
# Cloud SDK only
response = client.smartscraper(
    user_prompt="Find top 5 tech news articles with titles and summaries",
    num_results=5
)
```

### Documentation Scraping
```python
# Cloud SDK SmartCrawler
request_id = client.smartcrawler(
    url="https://docs.example.com",
    user_prompt="Extract all API endpoints and descriptions",
    max_pages=50
)
```

---

## 🆘 Troubleshooting

### Local Version Issues

**Problem**: `ModuleNotFoundError: No module named 'scrapegraphai'`
```bash
# Solution
pip install scrapegraphai
```

**Problem**: Scraping is slow
```
# Solution: Try a lighter model
Use GPT-3.5-turbo instead of GPT-4
```

### Cloud SDK Issues

**Problem**: `SGAI_API_KEY not found`
```bash
# Solution
export SGAI_API_KEY='your-actual-key'
# Or add to your .bashrc/.zshrc
```

**Problem**: `Insufficient credits`
```bash
# Check balance
python -c "from scrapegraph_py import Client; print(Client('your-key').get_credits())"
# Then recharge at scrapegraphai.com
```

---

## 📚 Next Steps

### After Getting Started:

1. **Read Full Documentation**
   - Local: Main README.md
   - Cloud SDK: `scrapegraph_ai_sdk/README.md`

2. **Try Advanced Features**
   - Custom output schemas
   - JavaScript rendering
   - Scheduled jobs (SDK only)

3. **Integrate into Your Project**
   - Use as a library in your Python code
   - Build custom workflows
   - Automate data collection

---

## 🔗 Useful Links

### Local Library
- [ScrapeGraph AI GitHub](https://github.com/VinciGit00/Scrapegraph-ai)
- [Documentation](https://scrapegraph-ai.readthedocs.io/)

### Cloud SDK
- [SDK GitHub](https://github.com/ScrapeGraphAI/scrapegraph-sdk)
- [API Documentation](https://docs.scrapegraphai.com)
- [Get API Key](https://scrapegraphai.com)

---

## 💬 Need Help?

- 📖 Check the README files
- 💡 Look at example code in demos
- 🐛 Report issues on GitHub
- 📧 Contact: support@scrapegraphai.com

---

**Happy Scraping! 🕷️✨**

