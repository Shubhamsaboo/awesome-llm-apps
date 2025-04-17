## 📰 Multi-agent AI news assistant
This Streamlit application implements a sophisticated news processing pipeline using multiple specialized AI agents to search, synthesize, and summarize news articles. It leverages the Llama 3.2 model via Ollama and DuckDuckGo search to provide comprehensive news analysis.


### Features
- Multi-agent architecture with specialized roles:
    - News Searcher: Finds recent news articles
    - News Synthesizer: Analyzes and combines information
    - News Summarizer: Creates concise, professional summaries

- Real-time news search using DuckDuckGo
- AP/Reuters-style summary generation
- User-friendly Streamlit interface


### How to get Started?

1. Clone the GitHub repository
```bash
git clone https://github.com/your-username/ai-news-processor.git
cd awesome-llm-apps/ai_agent_tutorials/local_news_agent_openai_swarm
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Pull and Run Llama 3.2 using Ollama:

```bash
# Pull the model
ollama pull llama3.2

# Verify installation
ollama list

# Run the model (optional test)
ollama run llama3.2
```

4. Create a .env file with your configurations:
```bash
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=fake-key 
```
5. Run the Streamlit app
```bash
streamlit run news_agent.py
```