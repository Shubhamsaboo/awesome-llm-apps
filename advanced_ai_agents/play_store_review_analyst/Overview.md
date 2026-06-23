# AI Agent Analyst - POC

Intelligent AI-powered trend analysis system for Google Play Store reviews using multi-agent architecture with CrewAI.

## 🎯 Overview

This POC analyzes Google Play Store reviews to identify trends, topics, and issues using a sophisticated multi-agent architecture. The system:

1. **Scrapes** reviews from Google Play Store (June 2024 - present)
2. **Analyzes** data structure and validates completeness
3. **Extracts** topics using LLM with high recall
4. **Validates** and merges similar categories
5. **Classifies** reviews with category IDs
6. **Generates** trend analysis reports

## 🏗️ Architecture

### Components

```
backend/
├── llm/                     # LLM provider abstraction
│   ├── llm_provider.py     # Base abstract class
│   ├── gemini_provider.py  # Google Gemini API
│   ├── openai_provider.py  # OpenAI API
│   └── local_provider.py   # Ollama/Local LLM
├── scraper/                # Data collection
│   ├── play_store_scraper.py
│   └── data_validator.py
├── agents/                 # Multi-agent pipeline
│   ├── structure_analyzer.py
│   ├── topic_extractor.py
│   ├── category_validator.py
│   ├── category_mapper.py
│   ├── review_classifier.py
│   ├── trend_analyzer.py
│   └── orchestrator.py
├── output/                 # Report generation
│   └── report_generator.py
└── main.py                 # FastAPI server

frontend/
├── index.html              # UI
├── style.css               # Styling
└── app.js                  # Client logic

config/
├── config.yaml             # Main configuration
└── llm_config.yaml         # LLM prompts & settings

data/                       # Scraped reviews (JSONL)
categories/                 # Category mappings (JSON)
output/                     # Generated reports
```

### Agent Pipeline

1. **Structure Analyzer** - Analyzes data schema
2. **Topic Extractor** - Extracts topics from reviews (high recall)
3. **Category Validator** - Merges duplicate categories
4. **Category Mapper** - Assigns IDs and creates mappings
5. **Review Classifier** - Assigns category IDs to reviews
6. **Trend Analyzer** - Generates frequency tables and insights

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- GEMINI_API_KEY or OPENAI_API_KEY (free tier supported)

### Installation

```bash
# Clone and setup
git clone <repo>
cd AI\ Agent\ Analyst
pip install -r requirements.txt

# Configure
export GEMINI_API_KEY="your-api-key"
# OR
export OPENAI_API_KEY="your-api-key"

# Run server
python -m uvicorn backend.main:app --reload
```

### Usage

1. Open `http://localhost:8000` in browser
2. Enter app package ID (e.g., `com.swiggy.android`)
3. (Optional) Select target date
4. Click "Start Analysis"
5. Download generated reports (Markdown & HTML)

## 📋 Configuration

### config.yaml

```yaml
data:
  start_date: "2024-06-01"      # Start of data range
  required_fields: [...]        # Required fields for validation

scraper:
  reviews_per_batch: 500        # Batch size for scraping
  delay_seconds: 2              # Delay between batches

taxonomy:
  mode: "agent_based"           # agent_based or semantic
  batch_size: 200               # Topics per batch

output:
  trend_window_days: 30         # Days to analyze
```

### llm_config.yaml

```yaml
llm:
  provider: "gemini"            # gemini, openai, local
  model: "gemini-1.5-flash"
  temperature: 0.3

prompts:
  structure_analyzer: "..."     # Custom prompts
  topic_extractor: "..."
  taxonomy_matcher: "..."
  # ... more prompts
```

## 📊 Output Report

Generated reports include:

**Frequency Table**
- Rows: Categories/Topics
- Columns: Dates (T to T-30)
- Cells: Frequency counts

**Key Insights**
- Top categories
- Trending up
- Trending down
- Emerging categories

## 🧠 Key Features

### High Recall Design
- Extracts ALL relevant topics from reviews
- Multiple batching strategies
- Semantic similarity matching
- Ontology-based category merging

### Modular Architecture
- Independent components
- Easy to test and debug
- Configurable via YAML
- Support multiple LLM providers

### Production Ready
- Error handling and logging
- Data validation
- Configurable parameters
- Report generation in multiple formats

## 🔧 Advanced Usage

### Using Different LLM Providers

**Gemini (Default)**
```bash
export GEMINI_API_KEY="your-key"
# config/llm_config.yaml: provider: "gemini"
```

**OpenAI**
```bash
export OPENAI_API_KEY="your-key"
# config/llm_config.yaml: provider: "openai"
```

**Local LLM (Ollama)**
```bash
# Start Ollama: ollama run llama2
# config/llm_config.yaml: provider: "local"
```

### Taxonomy Builder Modes

**Agent-Based (Recommended)**
- Iterative batching (200 topics/batch)
- First batch: Create categories
- Subsequent batches: Match or create
- Highest accuracy, slower

**Semantic-Based**
- Embedding-based clustering
- Faster processing
- Good for large datasets
- May need validation

## 📝 Example Report Structure

```
# Trend Analysis Report

**App:** Swiggy
**Analysis Date:** 2024-10-15
**Window:** 30 days

## Key Insights

### Top Categories
1. Delivery Issue
2. Food Stale
3. Delivery Partner Rude

### Trending Up
- Maps Not Working

### Trending Down
- Payment Issue

## Frequency Table

| Category | 2024-09-15 | 2024-09-16 | ... | 2024-10-15 |
|:---------|:----------:|:----------:|:---:|:----------:|
| Delivery Issue | 12 | 8 | ... | 23 |
| Food Stale | 5 | 7 | ... | 11 |
```

## 🐛 Troubleshooting 
**Issue**: "App not found"
- Verify package ID format
- Try with full Play Store URL

**Issue**: "API quota exceeded"
- Check rate limiting in scraper config
- Increase `delay_seconds`
- Use semantic mode for large datasets

**Issue**: "Category merging too aggressive"
- Lower merge threshold in validator
- Use agent-based mode for better control
- Review LLM prompts in config

## 📦 Dependencies

- **FastAPI**: Web framework
- **google-play-scraper**: Play Store data
- **CrewAI**: Multi-agent orchestration (planned)
- **google-generativeai**: Gemini API
- **openai**: OpenAI API
- **sentence-transformers**: Embeddings
- **PyYAML**: Configuration

## 📄 API Endpoints

```
GET  /                 Health check
POST /analyze          Start analysis
GET  /report/{file}    Download report
```

## 🎓 How It Works
1. User submits app link + date
2. Scraper fetches reviews with batching
3. Data validator filters incomplete reviews
4. Multi-agent pipeline processes reviews:
   - Analyzes structure
   - Extracts topics
   - Validates categories
   - Classifies reviews
   - Generates trends
5. Reports generated (Markdown + HTML)
6. User downloads reports
 
## 📞 Support

For issues or questions:
1. Check troubleshooting section
2. Review logs in `app.log`
3. Verify configuration files
4. Check API key validity
  