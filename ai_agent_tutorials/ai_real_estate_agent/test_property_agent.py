from ai_real_estate_agent import PropertyFindingAgent

def test_property_agent():
    # Initialize the agent with your Firecrawl and OpenAI API keys
    agent = PropertyFindingAgent(
        firecrawl_api_key="",  # Replace with your Firecrawl key
        openai_api_key=""
    )
    
    try:
        # Test property search
        results = agent.find_properties(
            city="Visakhapatnam",
            max_price=4.0,
            property_category="Residential",
            property_type="Individual House"
        )
        
        print("\n=== Property Search Results ===")
        print(results.content)
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    test_property_agent() 