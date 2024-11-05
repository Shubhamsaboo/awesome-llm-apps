import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory of 'news_summarizer_analyzer' to sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    from src.news_summarizer_analyzer.tools.custom_tool import NewsAPITool
    print("Import successful")
except ImportError as e:
    print(f"Import failed: {e}")

def test_news_api_tool():
    api_key: str = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise ValueError("NEWS_API_KEY environment variable is not set")
    
    tool: NewsAPITool = NewsAPITool(api_key=api_key)

    # Define a query to test
    query: str = 'Financial Markets'

    try:
        # Fetch articles
        articles: list = tool._run(query)
        for article in articles:
            print(f"Title: {article['title']}, Source: {article['source']}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_news_api_tool()
