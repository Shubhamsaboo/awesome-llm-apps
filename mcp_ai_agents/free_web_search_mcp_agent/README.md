# 🔍 Free Web Search MCP Agent

A Streamlit application that demonstrates how to build a **Search-First LLM Agent** using the Model Context Protocol (MCP). It uses DuckDuckGo for free, real-time web searches and beautifulsoup4 for webpage content extraction, requiring **zero API keys** for the search functionality.

**✨ Powered by [free-web-search-ultimate](https://github.com/wd041216-bit/free-web-search-ultimate) MCP Server** [![free-web-search-ultimate MCP server](https://glama.ai/mcp/servers/wd041216-bit/free-web-search-ultimate/badges/score.svg)](https://glama.ai/mcp/servers/wd041216-bit/free-web-search-ultimate)

## Features

- **Zero-Cost Search**: Uses DuckDuckGo for unlimited free web searches
- **Search-First Paradigm**: The LLM is instructed to *always* search the web before answering, completely eliminating knowledge cut-off limitations
- **Real-Time Data Extraction**: Automatically visits search results and extracts clean markdown content
- **Interactive UI**: Clean Streamlit interface for natural language queries
- **MCP Integration**: Uses the standard Model Context Protocol for tool integration

## Setup

### Requirements
- Python 3.9+
- OpenAI API Key (only for the LLM reasoning, search is free)

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/mcp_ai_agents/free_web_search_mcp_agent
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Install the free-web-search MCP server:
   ```bash
   pip install free-web-search-ultimate
   ```

4. Get your OpenAI API Key:
   - Get from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

### Running the App

1. Start the Streamlit app:
   ```bash
   streamlit run search_agent.py
   ```

2. In the app interface:
   - Enter your OpenAI API key
   - Type any question that requires up-to-date knowledge
   - Click "Search & Answer"

## Example Queries

- "What are the latest developments in AI this week?"
- "Who won the most recent Super Bowl and what was the score?"
- "What is the current stock price of Apple and what are analysts saying?"
- "Summarize the latest news about SpaceX Starship launches"
