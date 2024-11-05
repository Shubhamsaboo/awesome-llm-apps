from agents.trend_analyzer import TrendAnalyzerTool
from dotenv import load_dotenv
import json
import os

# Load environment variables
load_dotenv()

def test_specific_input():
    # The exact input you provided
    test_input = """{\"input_data\": {\"title\": \"Summaries of Verified News Articles\", \"summary\": \"1. Trump's crypto website experienced a crash following the sale of its token. 2. Scotland's Treasury demands compensation for a tax increase. 3. The launch of Trumpcoin faced a lackluster response. 4. UK borrowing in September reached the third-highest level on record. 5. The banking industry creator emphasizes that bankers are neither seen as villains nor rock stars.\", \"key_points\": [\"Trump's crypto website crash post-token sale\", \"Scotland's Treasury seeks compensation for tax hike\", \"Trumpcoin launch met with low interest\", \"UK records third-highest borrowing in September\", \"Bankers perceived as neither villains nor rock stars\"], \"sources\": [\"Trump\\u2019s crypto website crashed after its token went on sale\", \"Treasury must compensate Scotland for tax hike - Robison\", \"Trumpcoin Launches With a Whimper\", \"UK borrowing for September third highest on record\", \"Bankers 'neither villains nor rock stars', says Industry creator\"]}}"""

    print("\n=== Testing Specific Input ===")
    print("\nInput data (formatted):")
    parsed = json.loads(test_input)
    print(json.dumps(parsed, indent=2))

    analyzer = TrendAnalyzerTool()
    
    print("\nProcessing...")
    result = analyzer._run(test_input)
    
    print("\nResult:")
    print(json.dumps(result, indent=2))
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_specific_input()