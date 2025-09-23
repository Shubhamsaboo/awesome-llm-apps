## Fix Firecrawl deep_research + Streamlit Cloud deploy

- Switch to firecrawl>=2.0.0, remove firecrawl-py.
- Use FirecrawlApp.deep_research(query, max_depth, time_limit, max_urls, on_activity=...).
- Preload OpenAI and Firecrawl keys from Streamlit Secrets if present.
- Pin Python 3.11 for Streamlit Cloud.
- Optional Streamlit config file.
- Display installed Firecrawl version for debugging.
