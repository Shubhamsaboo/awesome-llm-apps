## 🔍 AI Research Agent with MiniMax

A Streamlit-based AI research agent powered by [MiniMax](https://www.minimaxi.com) M2.5 model. It searches the web using DuckDuckGo and synthesizes findings into comprehensive research reports, leveraging MiniMax's 204K context window for in-depth analysis.

### Features

- Powered by MiniMax M2.5 with 204K context window
- Web search via DuckDuckGo (no additional API key needed)
- Structured research reports with sources and evidence
- Interactive Streamlit interface

### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/starter_ai_agents/minimax_research_agent
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Get your MiniMax API Key

- Sign up at [MiniMax Platform](https://www.minimaxi.com) and obtain your API key.

4. Run the Streamlit App

```bash
streamlit run minimax_research_agent.py
```

### How it Works?

The agent uses MiniMax M2.5 via its OpenAI-compatible API to:
1. Take a research topic from the user
2. Generate and execute multiple web search queries using DuckDuckGo
3. Analyze and cross-reference the search results
4. Produce a well-structured research report with key findings and sources

MiniMax M2.5 is accessed through the OpenAI-compatible endpoint at `https://api.minimax.io/v1`, making it easy to integrate with existing OpenAI-based tools and frameworks.
