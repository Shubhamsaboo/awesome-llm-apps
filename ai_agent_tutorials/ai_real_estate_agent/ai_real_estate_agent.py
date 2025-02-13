from typing import Dict, List
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from firecrawl import FirecrawlApp

class PropertyData(BaseModel):
    """Schema for property data extraction"""
    building_name: str = Field(description="Name of the building/property", alias="Building_name")
    property_type: str = Field(description="Type of property (commercial, residential, etc)", alias="Property_type")
    location_address: str = Field(description="Complete address of the property")
    price: str = Field(description="Price of the property", alias="Price")
    description: str = Field(description="Detailed description of the property", alias="Description")

class PropertiesResponse(BaseModel):
    """Schema for multiple properties response"""
    properties: List[PropertyData] = Field(description="List of property details")

class LocationData(BaseModel):
    """Schema for location price trends"""
    location: str
    price_per_sqft: float
    percent_increase: float
    rental_yield: float

class LocationsResponse(BaseModel):
    """Schema for multiple locations response"""
    locations: List[LocationData] = Field(description="List of location data points")

class MarketNewsData(BaseModel):
    """Schema for market news extraction"""
    title: str = Field(description="Title of the article/news")
    content: str = Field(description="Main content of the article")
    date: str = Field(description="Publication date")
    source: str = Field(description="Source of the article")

class FirecrawlResponse(BaseModel):
    """Schema for Firecrawl API response"""
    success: bool
    data: Dict
    status: str
    expiresAt: str

class PropertyFindingAgent:
    """Agent responsible for finding properties and providing recommendations"""
    
    def __init__(self, firecrawl_api_key: str, openai_api_key: str):
        self.agent = Agent(
            model=OpenAIChat(id="o3-mini", api_key=openai_api_key),
            markdown=True,
            description="I am a real estate expert who helps find and analyze properties based on user preferences."
        )
        self.firecrawl = FirecrawlApp(api_key=firecrawl_api_key)

    def find_properties(
        self, 
        city: str,
        max_price: float,
        property_category: str = "Residential",
        property_type: str = "Flat"
    ) -> str:
        """Find and analyze properties based on user preferences"""
        formatted_location = city.lower()
        
        # First, extract properties using Firecrawl
        urls = [
            f"https://www.squareyards.com/sale/property-for-sale-in-{formatted_location}/*",
            f"https://www.99acres.com/property-in-{formatted_location}-ffid/*",
            f"https://housing.com/in/buy/{formatted_location}/{formatted_location}",
            f"https://www.nobroker.in/property/sale/{city}/{formatted_location}",
            f"https://www.magicbricks.com/*"
        ]
        
        property_type_prompt = "Flats" if property_type == "Flat" else "Individual Houses"
        
        raw_response = self.firecrawl.extract(
            urls=urls,
            params={
                'prompt': f"""Extract at least 3-6 different {property_category} {property_type_prompt} from {city} that cost less than {max_price} crores.
                
                Requirements:
                - Property Category: {property_category} properties only
                - Property Type: {property_type_prompt} only
                - Location: {city}
                - Maximum Price: {max_price} crores
                - Include complete property details with exact location
                - IMPORTANT: Return data for at least 3 different properties
                - Format as a list of properties with their respective details
                """,
                'schema': PropertiesResponse.model_json_schema()
            }
        )
        
        print("Raw Property Response:", raw_response)
        
        # Process the properties data
        if isinstance(raw_response, dict) and raw_response.get('success'):
            properties = raw_response['data'].get('properties', [])
        else:
            properties = []
            
        print("Processed Properties:", properties)

        # Now use the agent to analyze and provide recommendations
        properties_context = "\n".join([
            f"Property: {p['Building_name']}\nPrice: {p['Price']}\nLocation: {p['location_address']}\nType: {p['Property_type']}\nDescription: {p['Description']}"
            for p in properties
        ])
        
        # Get location price trends
        price_trends = self.get_location_trends(city)
        
        analysis = self.agent.run(
            f"""As a real estate expert, analyze these properties and market trends:

            Properties Found:
            {properties_context}

            Location Price Trends:
            {price_trends}

            Please provide:
            1. A summary of available properties
            2. Best value properties based on current market rates
            3. Location-specific advantages and price trends
            4. Specific recommendations based on the {property_category} {property_type} requirement
            5. Investment potential based on price trends
            6. Any red flags or concerns to consider
            7. Negotiation tips for the best properties

            Format your response in a clear, structured way that helps the user make an informed decision.
            """
        )
        
        return analysis

    def get_location_trends(self, city: str) -> str:
        """Get price trends for different localities in the city"""
        raw_response = self.firecrawl.extract([
            f"https://www.99acres.com/property-rates-and-price-trends-in-{city.lower()}-prffid/*"
        ], {
            'prompt': """Extract price trends data for ALL major localities in the city. 
            IMPORTANT: 
            - Return data for at least 5-10 different localities
            - Include both premium and affordable areas
            - Do not skip any locality mentioned in the source
            - Format as a list of locations with their respective data
            """,
            'schema': LocationsResponse.model_json_schema(),
        })
        
        if isinstance(raw_response, dict) and raw_response.get('success'):
            locations = raw_response['data'].get('locations', [])
            
    
            # Use agent to analyze the trends
            analysis = self.agent.run(
                f"""As a real estate expert, analyze these location price trends for {city}:

                {locations}

                Please provide:
                1. A bullet-point summary of the price trends for each location
                2. Identify the top 3 locations with:
                   - Highest price appreciation
                   - Best rental yields
                   - Best value for money
                3. Investment recommendations:
                   - Best locations for long-term investment
                   - Best locations for rental income
                   - Areas showing emerging potential
                4. Specific advice for investors based on these trends

                Format the response as follows:
                
                📊 LOCATION TRENDS SUMMARY
                • [Bullet points for each location]

                🏆 TOP PERFORMING AREAS
                • [Bullet points for best areas]

                💡 INVESTMENT INSIGHTS
                • [Bullet points with investment advice]

                🎯 RECOMMENDATIONS
                • [Bullet points with specific recommendations]
                """
            )
            
            return analysis.content
            
        return "No price trends data available"

class MarketAnalysisAgent:
    """Agent responsible for analyzing market trends and conditions"""
    
    def __init__(self, firecrawl_api_key: str, openai_api_key: str):
        self.agent = Agent(
            model=OpenAIChat(id="o3-mini", api_key=openai_api_key),
            markdown=True,
            description="I am a real estate market analyst who provides insights on market trends and conditions."
        )
        self.firecrawl = FirecrawlApp(api_key=firecrawl_api_key)

    def analyze_market(self, city: str) -> str:
        """Analyze market conditions using news and market reports"""
        # Extract market information from news and analysis sites
        urls = [
            "https://www.moneycontrol.com/real-estate-property/*",
            f"https://www.99acres.com/property-rates-and-price-trends-in-{city.lower()}/*",
            "https://housing.com/news/*",
            f"https://www.99acres.com/articles/real-estate-market-{city.lower()}*"
        ]
        
        raw_response = self.firecrawl.extract(
            urls=urls,
            params={
                'prompt': f"""Extract recent real estate market information and trends for {city}.
                Focus on:
                - Market trends
                - Price movements
                - Development projects
                - Infrastructure updates
                - Investment potential
                Only extract articles from the last 6 months.
                """,
                'schema': MarketNewsData.model_json_schema()
            }
        )
        
        # Process the market data
        market_data = []
        if isinstance(raw_response, dict):
            response = FirecrawlResponse(**raw_response)
            market_data = [response.data]
        elif isinstance(raw_response, list):
            responses = [FirecrawlResponse(**item) for item in raw_response]
            market_data = [resp.data for resp in responses]

        # Analyze the market data
        market_context = "\n".join([
            f"Title: {article['title']}\nDate: {article['date']}\nContent: {article['content']}\nSource: {article['source']}"
            for article in market_data
        ])
        
        analysis = self.agent.run(
            f"""As a real estate market analyst, provide a comprehensive market analysis for {city}:

            Market Data:
            {market_context}

            Please provide:
            1. Current market overview
            2. Price trends and predictions
            3. Development and infrastructure updates
            4. Investment opportunities and risks
            5. Regulatory changes affecting the market
            6. Future outlook

            Format your response as a detailed market report with clear sections and actionable insights.
            """
        )
        
        return analysis

def main():
    """Main function to demonstrate the agents"""
    firecrawl_api_key = "YOUR_FIRECRAWL_API_KEY"
    openai_api_key = "OPENAI_API_KEY"
    
    try:
        # Initialize agents
        property_agent = PropertyFindingAgent(firecrawl_api_key, openai_api_key)
        market_agent = MarketAnalysisAgent(firecrawl_api_key)
        
        # Get property recommendations
        print("=== Property Analysis ===")
        property_analysis = property_agent.find_properties(
            city="Hyderabad",
            max_price=5.0,
            property_category="Residential",
            property_type="Flat"
        )
        print(property_analysis)
        
        # Get market analysis
        print("\n=== Market Analysis ===")
        market_analysis = market_agent.analyze_market("Hyderabad")
        print(market_analysis)
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
