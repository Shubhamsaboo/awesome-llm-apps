# 🕷️ Web Scraping AI Agent

### 🎓 FREE Step-by-Step Tutorial 
**👉 [Click here to follow our complete step-by-step tutorial](https://www.theunwindai.com/p/build-a-web-scraping-ai-agent-with-llama-3-2-running-locally) and learn how to build this from scratch with detailed code walkthroughs, explanations, and best practices.**

AI-powered web scraping using **ScrapeGraphAI** - extract structured data from websites using natural language prompts. This agent runs locally with the open-source `scrapegraphai` library.

---

## 📁 What's Inside

**Files**: `ai_scrapper.py`, `local_ai_scrapper.py`

Use the open-source ScrapeGraphAI library that runs on your local machine.

**✅ Pros:**
- Free to use (no API costs)
- Full control over execution
- Privacy-friendly (all data stays local)

**❌ Cons:**
- Requires local installation and dependencies
- Limited by your hardware
- Need to manage updates

---

## 🚀 Getting Started

1. **Clone the repository**
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/starter_ai_agents/web_scraping_ai_agent
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Install the Playwright browser** (used by ScrapeGraphAI to load pages)
```bash
playwright install chromium
```

4. **Choose a model backend**

**Option A – OpenAI** (`ai_scrapper.py`)
- Sign up for an [OpenAI account](https://platform.openai.com/)
- Obtain your API key

**Option B – Local models with Ollama** (`local_ai_scrapper.py`)

`local_ai_scrapper.py` uses two Ollama models: `llama3.2:latest` as the LLM and `nomic-embed-text` for embeddings.

- Install Ollama from [ollama.com/download](https://ollama.com/download) (Windows, macOS, Linux)
- Pull both models:
```bash
ollama pull llama3.2:latest
ollama pull nomic-embed-text
```
- Make sure the Ollama server is running on `http://localhost:11434`. On Windows and macOS the desktop app starts it automatically; otherwise run:
```bash
ollama serve
```
- Verify both models are available:
```bash
ollama list
```

Ollama loads each model on demand when the app calls it, so you don't need to `ollama run` either one yourself.

5. **Run the Streamlit App**
```bash
streamlit run ai_scrapper.py
# Or for local models:
streamlit run local_ai_scrapper.py
```

---

## 🧪 Quick Test Pages

Local models on CPU can take several minutes on large pages, because the page is split into many chunks and each one is sent to the LLM. Start with a small page to confirm everything works:

| URL | Prompt to try |
|---|---|
| `https://example.com` | Get the page title and the link text |
| `https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html` | Extract the book title, price, and availability |
| `https://quotes.toscrape.com/tag/love/` | List the quotes and their authors |
| `https://httpbin.org/html` | What is the title and who is the author of the story? |

`books.toscrape.com` and `quotes.toscrape.com` are sandbox sites built for scraping practice. While a scrape runs, `local_ai_scrapper.py` shows each step (loading the page, splitting it into chunks, asking the LLM) with how long it took.

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

1. You provide your OpenAI API key
2. Select the model (GPT-4o, GPT-5, or local models)
3. Enter the URL and extraction prompt
4. The app uses ScrapeGraphAI to scrape and extract data locally
5. Results are displayed in the app

---

## 📖 Documentation

- **ScrapeGraphAI Library**: [ScrapeGraphAI GitHub](https://github.com/VinciGit00/Scrapegraph-ai)

---
