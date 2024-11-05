## AI Business Insider - A News Summarizer and Analyst - CrewAI 

- Problem Statement: This is quite Personal to me, since my 1st year of Uni, I always wanted to be an Entreprenuer. Back then, I was constantly looking for a gap in the market, a problem that I can solve by constantly by reading news articles extensively, which was a very hard task. I have build this AI Agent News Analyzer that gives me Business Ideas regarding a particular topic. I have realised now that there's no perfect idea -  atleast in the tech space. You have to build stuff and gain experience working with multiple people increasing your odds of finding a problem to work on rather than reading news.

This project is a News Engine that helps users research a news topic, fact-check information, summarize key findings, and analyze trends to help find their Potential Business Ideas for their own Company!. It leverages multiple AI agents to collect, verify, and analyze news, enabling users to extract insights and identify key opportunities across various news articles. The application uses [CrewAI](https://crewai.com/) to orchestrate these tasks and provide an interactive experience.

## Features

- **User Prompt**: Users can input a topic of interest for research.
- **News Collection**: The system gathers recent news articles based on the topic provided.
- **Fact Verification**: Key facts from collected news articles are verified using trusted tools.
- **Summary Generation**: Concise summaries of verified information are generated.
- **Trend Analysis**: The system identifies trends and patterns across the analyzed news stories, providing deeper insights for user's potential business ideas

## Architecture

This tool comprises four key agents:

### 1. News Collector
- **Task**: Collects recent news articles on the given topic.
- **Tools**: 
  - News APIs (like [NewsAPI](https://newsapi.org/))
  
### 2. Fact Checker
- **Task**: Verifies key facts from collected articles.
- **Tools**: 
  - Google Fact-Check Tools API
  
### 3. Summary Writer
- **Task**: Produces concise summaries of the verified information.
- **Tools**: 
  - Hugging Face's [BART](https://huggingface.co/facebook/bart-large-cnn) / GPT 4o (now)

### 4. Trend Analyzer
- **Task**: Analyzes trends and patterns across collected and summarized news stories.
- **Tools**: 
  - OpenAI's GPT 4o

## Project Flow

1. **Step 1**: User enters a topic in the input field on the frontend.
2. **Step 2**: The system fetches recent news articles related to the topic using the News Collector agent.
3. **Step 3**: The Fact Checker agent verifies the accuracy of key facts from the news articles.
4. **Step 4**: The Summary Writer agent generates a concise summary of the news.
5. **Step 5**: The Trend Analyzer agent examines the news for trends and patterns.
6. **Step 6**: Results are presented to the user, showing collected news, verified facts, a summary, and trend analysis.

## Technologies Used

- **Frontend**: Streamlit 
- **Backend**: 
  - Python (with FastAPI for the API backend)
- **AI/ML Tools**: 
  - CrewAI for orchestrating AI agents
  - Google Fact-Check Tools API
  - OpenAI for trend analysis
- **Web Scraping**: Custom web scrapers and external APIs (News API)

## How to Run

1. Clone the repository:
   ```bash
   git clone https://github.com/Madhuvod/AI-Business-Insider.git
   cd AI-Business-Insider
   ```

2. Create and activate a virtual environment:
   ```bash
   # For macOS/Linux
   python -m venv venv
   source venv/bin/activate

   # For Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
   (after doing this, sometimes a few packages might not be installed - so installed those 2-3 packages seprately, or reload the IDE if any import errors showing)

4. Create a new .env file and set up your environment variables:
   ```bash
   # Get API keys from:
   # - News API: https://newsapi.org/account
   # - Google Fact Check: https://developers.google.com/fact-check/tools/api
   # - OpenAI: https://platform.openai.com/api-keys

   NEWS_API_KEY=your_news_api_key 
   GOOGLE_FACT_CHECK_KEY=your_google_fact_check_key
   OPENAI_API_KEY=your_openai_api_key
   ```

5. Run the application (in two different terminals):
   ```bash
   # Terminal 1 - Start the backend
   python news_summarizer_analyzer/src/news_summarizer_analyzer/main.py

   # Terminal 2 - Start the Streamlit frontend
   streamlit run news_summarizer_analyzer/src/news_summarizer_analyzer/streamlit_app.py
   ```

## Development Setup

If you're contributing to the project:
```bash
# Install in development mode
pip install -e .

# Install additional development dependencies
pip install pytest python-dotenv
```

**TODO**: Thinking of using A voice agent for this tooo
![image](IMG_3530.heic)
