# AI Content Factory for AgroDrone Europe

A multi-agent content generation system that creates SEO-optimized content for [agrodroneeurope.com](https://agrodroneeurope.com) — a professional agricultural drone services company in Germany.

## Features

- **Multi-agent pipeline**: Researcher → SEO Writer → Editor working together
- **6 content types**: Blog posts, landing pages, service descriptions, social media packs, case studies, FAQ sections
- **SEO optimization**: Meta tags, heading structure, keyword integration, internal linking suggestions
- **Bilingual**: German and English content generation
- **Service-focused**: Tailored for crop protection, seeding, NDVI monitoring, and roof cleaning services

## How It Works

The app uses three AI agents coordinated by Agno:

1. **Researcher** — searches the web for industry data, trends, and competitor insights using SerpAPI
2. **SEO Content Writer** — creates structured, keyword-optimized content using research findings
3. **Content Editor** — orchestrates the team, reviews quality, and ensures brand consistency

## Getting Started

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
streamlit run content_factory.py
```

3. Enter your API keys in the sidebar:
   - **OpenAI API Key** (for GPT-4o)
   - **SerpAPI Key** (for web research)

4. Select content type, service focus, language, and target keywords, then describe your topic.
