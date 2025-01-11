from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field
from typing import Optional

# Define a simple schema for testing
class SimpleSchema(BaseModel):
    title: Optional[str] = Field(description="Title of the webpage.")
    description: Optional[str] = Field(description="Meta description of the webpage.")

# Initialize the FirecrawlApp with your API key
app = FirecrawlApp(api_key='fc-')  # Replace with your API key

def extract_competitor_info(competitor_url: str):

    try:
        # Use Firecrawl to scrape and extract data
        data = app.scrape_url(competitor_url, {
            'formats': ['extract'],
            'extract': {
                'schema': SimpleSchema.model_json_schema(),
            }
        })
        return data.get("extract", {})
    except Exception as e:
        return {"error": str(e)}

# Example usage
if __name__ == "__main__":
    # Competitor URL to analyze
    competitor_url = "https://www.equal.in"  # Replace with your competitor URL
    
    # Extract competitor information
    competitor_info = extract_competitor_info(competitor_url)
    
    # Print the structured information
    print(f"Competitor: {competitor_url}")
    print(competitor_info)