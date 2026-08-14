## 📄 AI Paper Research Agent
A Streamlit app that turns a research topic into a cited literature review. It searches academic
indexes (arXiv, OpenAlex, Semantic Scholar, Crossref) through CRW's research API, pulls the
abstracts, and has GPT-4o write a review where every claim carries the source it came from.

Unlike a general web-search research agent, this one only ever reads paper abstracts, so the output
stays traceable to real publications instead of blog posts and marketing pages.

## Features

- **Academic search**: Queries multiple paper indexes in one call and ranks the results by relevance.

- **Abstract backfill**: When a search hit arrives without an abstract, the agent fetches the paper
  record to get it, so the review is never written from titles alone.

- **Cited review**: GPT-4o writes the review from the abstracts only, with a bracketed citation on
  every claim and an explicit note when sources disagree.

- **Source list**: Every paper used is listed underneath with a link to arXiv where available.

## How to get Started?

1. **Clone the GitHub repository**

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/starter_ai_agents/ai_paper_research_agent
```

2. **Install the required dependencies**

```bash
pip install -r requirements.txt
```

3. **Get your API keys**

- **OpenAI**: sign up at [platform.openai.com](https://platform.openai.com/api-keys)
- **CRW**: sign up at [fastcrw.com](https://fastcrw.com) for a hosted key, or run the open-source
  engine yourself and point the SDK at it with `CRW_API_URL`

4. **Run the Streamlit app**

```bash
streamlit run paper_research_agent.py
```

5. **Use the app**

Paste both keys into the sidebar, pick how many papers to review, type a topic, and press Research.
