import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory of 'news_summarizer_analyzer' to sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    from src.news_summarizer_analyzer.agents.summary_writer import SummaryWriterTool
    print("Import successful")
except ImportError as e:
    print(f"Import failed: {e}")

def test_summary_writer():
    api_key: str = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    summary_writer = SummaryWriterTool(api_key=api_key)

    # Example article to test
    article = {
        "title": "AI Breakthrough in Climate Modeling",
        "snippet": "Researchers use advanced AI to improve climate change predictions..."
    }

    try:
        # Run the fact checker
        result = summary_writer._run(article)
        print("Summary Writer Result:")
        print(result)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_summary_writer()