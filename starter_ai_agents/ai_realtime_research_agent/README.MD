## 🔎 AI Real-Time Research Agent

This Streamlit app is an AI research agent that answers any question using **real-time data from Google, Reddit, and YouTube** — not stale training data. It combines web facts, genuine community opinion, and video sources into a single cited briefing, powered by OpenAI GPT-5.5 and the [Scavio](https://scavio.dev) search API.

Most "research" agents only see Google. This one also reads what real people say on Reddit and what reviewers show on YouTube — so the answer reflects the live internet, with citations.

### Features

- **Three real sources in one answer** — Google (web), Reddit (community opinion), and YouTube (video), searched live
- **Cited briefings** — a direct answer, key findings, real community sentiment, and a linked source list
- **Pick your sources** — toggle Google / Reddit / YouTube per question
- **One API key for everything** — no separate SERP, Reddit, and YouTube integrations to wire up or maintain

### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/starter_ai_agents/ai_realtime_research_agent
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Get your OpenAI API Key

- Sign up for an [OpenAI account](https://platform.openai.com/) (or the LLM provider of your choice) and obtain your API key.

4. Get your Scavio API Key

- Sign up for a free [Scavio account](https://dashboard.scavio.dev) (50 credits, no credit card) and obtain your API key. One key covers Google, Reddit, YouTube, Amazon, Walmart, TikTok, and Instagram.

5. Run the Streamlit App

```bash
streamlit run ai_realtime_research_agent.py
```

### How it works

1. You ask a question and choose which sources to use.
2. An [Agno](https://github.com/agno-agi/agno) agent calls Scavio's Google, Reddit, and YouTube tools to gather live results.
3. GPT-5.5 synthesizes the results into a structured, cited briefing — web facts, what the community actually says, and video sources, with links.
