import os
import streamlit as st
import json
import time
import requests
from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field
from typing import List, Optional

# Load environment variables
load_dotenv()

# API keys - must be set in environment variables
DEFAULT_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEFAULT_FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
DEFAULT_PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")

# Pydantic schemas
class PropertyDetails(BaseModel):
    address: str = Field(description="Full property address")
    price: Optional[str] = Field(description="Property price")
    bedrooms: Optional[str] = Field(description="Number of bedrooms")
    bathrooms: Optional[str] = Field(description="Number of bathrooms")
    square_feet: Optional[str] = Field(description="Square footage")
    property_type: Optional[str] = Field(description="Type of property")
    description: Optional[str] = Field(description="Property description")
    features: Optional[List[str]] = Field(description="Property features")
    images: Optional[List[str]] = Field(description="Property image URLs")
    agent_contact: Optional[str] = Field(description="Agent contact information")
    listing_url: Optional[str] = Field(description="Original listing URL")

class PropertyListing(BaseModel):
    properties: List[PropertyDetails] = Field(description="List of properties found")
    total_count: int = Field(description="Total number of properties found")
    source_website: str = Field(description="Website where properties were found")

def get_firecrawl_app():
    """Get FirecrawlApp instance"""
    api_key = os.getenv("FIRECRAWL_API_KEY", DEFAULT_FIRECRAWL_API_KEY)
    return FirecrawlApp(api_key=api_key)

def extract_property_listings(url, user_criteria=None):
    """Extract property listings from search pages"""
    try:
        app = get_firecrawl_app()
        
        base_prompt = "Extract property listings from this real estate search page."
        
        if user_criteria:
            criteria_prompt = f"""
            Focus on properties matching:
            - Budget: {user_criteria.get('budget_range', 'Any')}
            - Type: {user_criteria.get('property_type', 'Any')}
            - Bedrooms: {user_criteria.get('bedrooms', 'Any')}
            - Bathrooms: {user_criteria.get('bathrooms', 'Any')}
            - Min Sqft: {user_criteria.get('min_sqft', 'Any')}
            - Features: {user_criteria.get('special_features', 'Any')}
            
            Extract: address, price, bedrooms, bathrooms, sqft, type, listing URLs.
            """
            full_prompt = base_prompt + criteria_prompt
        else:
            full_prompt = base_prompt + " Extract property information including address, price, bedrooms, bathrooms, square footage, property type, and listing URLs."
        
        data = app.extract([url], prompt=full_prompt, schema=PropertyListing.model_json_schema())
        
        if hasattr(data, 'data'):
            return data.data
        elif hasattr(data, 'model_dump'):
            return data.model_dump()
        else:
            return {"error": "Unexpected response format"}
            
    except Exception as e:
        return {"error": f"Failed to extract listings: {str(e)}"}

def search_perplexity_properties(city, state, user_criteria):
    """Search for properties using Perplexity API"""
    try:
        api_key = os.getenv("PERPLEXITY_API_KEY", DEFAULT_PERPLEXITY_API_KEY)
        
        search_query = f"""
        Find real estate properties for sale in {city}, {state} matching:
        - Budget: {user_criteria.get('budget_range', 'Any')}
        - Type: {user_criteria.get('property_type', 'Any')}
        - Bedrooms: {user_criteria.get('bedrooms', 'Any')}
        - Bathrooms: {user_criteria.get('bathrooms', 'Any')}
        - Min Sqft: {user_criteria.get('min_sqft', 'Any')}
        - Features: {user_criteria.get('special_features', 'Any')}
        
        Search: Zillow, Realtor.com, Trulia, Homes.com, Redfin
        Provide: detailed property info, market insights, neighborhood analysis
        Include: specific addresses, prices, features, listing URLs, market trends
        """
        
        response = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={'model': 'sonar-pro', 'messages': [{'role': 'user', 'content': search_query}]}
        )
        
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            return {"success": True, "content": content, "source": "Perplexity Search"}
        else:
            return {"error": f"Perplexity API error: {response.status_code}"}
            
    except Exception as e:
        return {"error": f"Perplexity search failed: {str(e)}"}

def search_real_estate_websites(city, state, user_criteria, selected_websites, update_callback):
    """Search real estate websites"""
    results = {}
    
    def create_search_urls(city, state):
        city_formatted = city.replace(' ', '-').lower()
        state_upper = state.upper() if state else ''
        
        return {
            "Zillow": f"https://www.zillow.com/homes/for_sale/{city_formatted}-{state_upper}/",
            "Realtor.com": f"https://www.realtor.com/realestateandhomes-search/{city_formatted}_{state_upper}/pg-1",
            "Trulia": f"https://www.trulia.com/for_sale/{city_formatted}-{state_upper}/",
            "Homes.com": f"https://www.homes.com/homes-for-sale/{city_formatted}-{state_upper}/"
        }
    
    search_urls = {site: url for site, url in create_search_urls(city, state).items() if site in selected_websites}
    
    for i, (site_name, search_url) in enumerate(search_urls.items()):
        try:
            progress = 0.2 + (i * 0.6 / len(search_urls))
            update_callback(progress, f"Searching {site_name}...", f"Analyzing {site_name}")
            
            if i > 0:
                time.sleep(2)
            
            result = extract_property_listings(search_url, user_criteria)
            
            if "error" not in result and len(result.get('properties', [])) > 0:
                results[site_name] = result
                property_count = len(result.get('properties', []))
                update_callback(progress + 0.3, f"Found {property_count} properties on {site_name}", f"Successfully analyzed {site_name}")
            else:
                results[site_name] = {"error": f"No data from {site_name}"}
                update_callback(progress + 0.3, f"Analyzing {site_name}", f"Gathering insights from {site_name}")
                
        except Exception as e:
            results[site_name] = {"error": f"Error: {str(e)}"}
            update_callback(progress + 0.3, f"Analyzing {site_name}", f"Processing {site_name}")
    
    return results

def create_firecrawl_tools(user_criteria):
    """Create tools for agents"""
    
    def extract_listings_tool(url: str) -> str:
        result = extract_property_listings(url, user_criteria)
        return json.dumps(result, indent=2) if "error" not in result else f"Error: {result['error']}"
    
    def perplexity_search_tool(city: str, state: str) -> str:
        result = search_perplexity_properties(city, state, user_criteria)
        return json.dumps(result, indent=2) if "error" not in result else f"Error: {result['error']}"
    
    return [extract_listings_tool, perplexity_search_tool]

def create_real_estate_agents(llm, firecrawl_tools, user_criteria):
    """Create specialized agents"""
    
    property_search_agent = Agent(
        name="Property Search Agent",
        model=llm,
        tools=firecrawl_tools,
        instructions="""
        You are a property search expert. Your role:
        
        1. SEARCH FOR PROPERTIES:
           - Use Firecrawl extract tools to search real estate websites
           - Focus on properties matching user criteria
           - Use Perplexity search tool if no properties found
        
        2. GATHER PROPERTY DATA:
           - Extract detailed property information
           - Collect listing URLs and agent contacts
           - Organize results clearly
        
        3. PROVIDE STRUCTURED OUTPUT:
           - List properties with full details
           - Include clickable listing URLs
           - Rank by match quality
        
        IMPORTANT: Always use perplexity_search_tool if extract methods don't find properties.
        Focus on finding properties that match user's exact criteria.
        """,
    )
    
    market_analysis_agent = Agent(
        name="Market Analysis Agent",
        model=llm,
        instructions="""
        You are a market analysis expert. Provide ELABORATE market insights:
        
        1. MARKET TRENDS:
           - Current market condition (buyer's/seller's market)
           - Price trends over 6-12 months
           - Market direction and key factors
           - Inventory levels and supply/demand
        
        2. NEIGHBORHOOD ANALYSIS:
           - Top neighborhood features and amenities
           - School district ratings and performance
           - Safety ratings and crime statistics
           - Local amenities (parks, shopping, restaurants)
           - Transportation and commute options
           - Employment opportunities
        
        3. INVESTMENT INSIGHTS:
           - Investment potential assessment
           - Price per square foot trends
           - Rental market data
           - Future development plans
           - Economic factors affecting the area
        
        4. COMPARATIVE ANALYSIS:
           - Compare with similar markets
           - Highlight unique advantages
           - Identify potential risks or opportunities
        
        PROVIDE DETAILED, ACTIONABLE INSIGHTS with specific data points.
        Include relevant links and sources when possible.
        """,
    )
    
    property_valuation_agent = Agent(
        name="Property Valuation Agent",
        model=llm,
        instructions="""
        You are a property valuation expert. Provide ELABORATE property assessments:
        
        1. PROPERTY VALUATION:
           - Fair market value estimates with reasoning
           - Price per square foot analysis
           - Comparable property analysis
           - Value appreciation potential
        
        2. PRICING ASSESSMENT:
           - Overpriced/Underpriced/Fair price analysis
           - Key pricing factors and market positioning
           - Negotiation potential and strategies
           - Price history and trends
        
        3. INVESTMENT ANALYSIS:
           - Investment potential (high/medium/low) with detailed reasoning
           - ROI projections and cash flow analysis
           - Key investment factors and considerations
           - Risk assessment and mitigation strategies
        
        4. PROPERTY FEATURES EVALUATION:
           - Detailed analysis of property features
           - Unique selling points and advantages
           - Potential improvements and their value impact
           - Maintenance considerations and costs
        
        5. MARKET POSITIONING:
           - How the property compares to market
           - Competitive advantages and disadvantages
           - Target buyer/renter profile
           - Marketing recommendations
        
        PROVIDE COMPREHENSIVE, DETAILED ANALYSIS with specific recommendations.
        Include relevant market data and comparative analysis.
        """,
    )
    
    return property_search_agent, market_analysis_agent, property_valuation_agent

def create_real_estate_team(llm, firecrawl_tools, user_criteria):
    """Create the real estate team"""
    
    property_search_agent, market_analysis_agent, property_valuation_agent = create_real_estate_agents(llm, firecrawl_tools, user_criteria)
    
    return Team(
        name="Real Estate Analysis Team",
        mode="coordinate",
        model=llm,
        members=[property_search_agent, market_analysis_agent, property_valuation_agent],
        instructions=[
            "You are a professional real estate analysis team.",
            "1. Property Search Agent: Find properties using extract + Perplexity fallback",
            "2. Market Analysis Agent: Provide ELABORATE market trends and neighborhood insights",
            "3. Property Valuation Agent: Give ELABORATE property valuations and investment analysis",
            "IMPORTANT: Provide detailed, actionable insights with specific data points.",
            "Include relevant links and sources when possible.",
            "Work together to provide comprehensive recommendations."
        ],
        show_members_responses=True,
        markdown=True,
    )

def display_property_results(result):
    """Display property results with clickable links"""
    st.markdown("## Property Analysis Report")
    st.markdown("### AI-Powered Real Estate Recommendations")
    
    if hasattr(result, 'content'):
        result_text = result.content
    else:
        result_text = str(result)
    
    # Display the full text result with markdown support for links
    st.markdown("### Analysis Report")
    st.markdown(result_text)
    
    # Extract and display clickable links
    import re
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', result_text)
    
    if urls:
        st.markdown("### 🔗 Property Links")
        for i, url in enumerate(set(urls), 1):
            st.markdown(f"{i}. [{url}]({url})")

def main():
    st.set_page_config(page_title="AI Multi-Agent Real Estate Team", page_icon="🏠", layout="wide")
    
    st.title("AI Multi-Agent Real Estate Team")
    st.markdown("### Find Your Dream Home with Specialized AI Agents")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        
        # API Key inputs with validation
        openai_key = st.text_input("OpenAI API Key", value=DEFAULT_OPENAI_API_KEY, type="password", 
                                  help="Get your API key from https://platform.openai.com/api-keys")
        firecrawl_key = st.text_input("Firecrawl API Key", value=DEFAULT_FIRECRAWL_API_KEY, type="password",
                                     help="Get your API key from https://firecrawl.dev")
        perplexity_key = st.text_input("Perplexity API Key", value=DEFAULT_PERPLEXITY_API_KEY, type="password",
                                      help="Get your API key from https://www.perplexity.ai/settings/api")
        
        # Show API key status
        if openai_key:
            st.success("✅ OpenAI API Key provided")
        else:
            st.error("❌ OpenAI API Key required")
            
        if firecrawl_key:
            st.success("✅ Firecrawl API Key provided")
        else:
            st.error("❌ Firecrawl API Key required")
            
        if perplexity_key:
            st.success("✅ Perplexity API Key provided")
        else:
            st.error("❌ Perplexity API Key required")
        
        # Update environment variables
        if openai_key: os.environ["OPENAI_API_KEY"] = openai_key
        if firecrawl_key: os.environ["FIRECRAWL_API_KEY"] = firecrawl_key
        if perplexity_key: os.environ["PERPLEXITY_API_KEY"] = perplexity_key
        
        st.markdown("---")
        
        # Website selection
        st.subheader("Select Websites to Search")
        available_websites = ["Zillow", "Realtor.com", "Trulia", "Homes.com"]
        selected_websites = [site for site in available_websites if st.checkbox(site, value=site in ["Zillow", "Realtor.com"])]
        
        if selected_websites:
            st.success(f"Selected: {', '.join(selected_websites)}")
        else:
            st.warning("Please select at least one website")
        
        st.markdown("---")
        st.markdown("### How it works")
        st.markdown("""
        1. **Property Search Agent** - Uses extract + Perplexity fallback
        2. **Market Analysis Agent** - Analyzes trends and neighborhood insights  
        3. **Property Valuation Agent** - Evaluates values and investment potential
        """)
    
    # Main form
    st.header("Your Property Requirements")
    
    with st.form("property_preferences"):
        col1, col2 = st.columns(2)
        
        with col1:
            city = st.text_input("City", placeholder="e.g., San Francisco")
            state = st.text_input("State/Province (optional)", placeholder="e.g., CA")
            min_price = st.number_input("Minimum Price ($)", min_value=0, value=500000, step=50000)
            max_price = st.number_input("Maximum Price ($)", min_value=0, value=1500000, step=50000)
        
        with col2:
            property_type = st.selectbox("Property Type", ["Any", "House", "Condo", "Townhouse", "Apartment"])
            bedrooms = st.selectbox("Bedrooms", ["Any", "1", "2", "3", "4", "5+"])
            bathrooms = st.selectbox("Bathrooms", ["Any", "1", "1.5", "2", "2.5", "3", "3.5", "4+"])
            min_sqft = st.number_input("Minimum Square Feet", min_value=0, value=1000, step=100)
        
        special_features = st.text_area("Special Features", placeholder="e.g., Parking, Yard, View, Near public transport, etc.")
        timeline = st.selectbox("Timeline", ["Flexible", "1-3 months", "3-6 months", "6+ months"])
        urgency = st.selectbox("Urgency", ["Not urgent", "Somewhat urgent", "Very urgent"])
        
        submitted = st.form_submit_button("Start Property Analysis", type="primary")
    
    # Process form submission
    if submitted:
        # Validate all required inputs
        missing_items = []
        if not openai_key:
            missing_items.append("OpenAI API Key")
        if not firecrawl_key:
            missing_items.append("Firecrawl API Key")
        if not perplexity_key:
            missing_items.append("Perplexity API Key")
        if not city:
            missing_items.append("City")
        if not selected_websites:
            missing_items.append("At least one website selection")
        
        if missing_items:
            st.error(f"Please provide: {', '.join(missing_items)}")
            return
        
        try:
            # Initialize components
            llm = OpenAIChat(id="gpt-4o", api_key=openai_key)
            
            user_criteria = {
                'budget_range': f"${min_price:,} - ${max_price:,}",
                'property_type': property_type,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'min_sqft': min_sqft,
                'special_features': special_features if special_features else 'None specified'
            }
            
            firecrawl_tools = create_firecrawl_tools(user_criteria)
            real_estate_team = create_real_estate_team(llm, firecrawl_tools, user_criteria)
            
        except Exception as e:
            st.error(f"Error initializing: {str(e)}")
            return
        
        # Display progress
        st.markdown("---")
        st.header("Property Analysis in Progress")
        
        status_container = st.container()
        with status_container:
            st.subheader("Current Activity")
            current_activity = st.empty()
        
        def update_progress(progress, status, activity=None):
            if activity:
                current_activity.text(activity)
        
        try:
            start_time = time.time()
            update_progress(0.1, "Initializing...", "Starting comprehensive property search")
            
            # Search websites
            search_start = time.time()
            search_results = search_real_estate_websites(city, state, user_criteria, selected_websites, update_progress)
            search_duration = time.time() - search_start
            
            # Process results
            successful_searches = sum(1 for result in search_results.values() if "error" not in result)
            total_properties = sum(len(result.get('properties', [])) for result in search_results.values() if "error" not in result)
            use_perplexity_fallback = total_properties == 0
            
            if use_perplexity_fallback:
                update_progress(0.85, "Running analysis...", "🔍 Searching rigorously across real estate platforms...")
            else:
                update_progress(0.85, "Running analysis...", "Property Search Agent: Analyzing search results")
            
            # Run agents
            agent_start = time.time()
            prompt = f"""
            Analyze real estate properties using our specialized agent team:
            
            USER REQUIREMENTS:
            LOCATION: {city}, {state if state else 'Any state'}
            BUDGET: {user_criteria['budget_range']}
            TYPE: {property_type}
            BEDROOMS: {bedrooms}
            BATHROOMS: {bathrooms}
            MIN SQFT: {min_sqft:,}
            FEATURES: {user_criteria['special_features']}
            TIMELINE: {timeline}
            URGENCY: {urgency}
            
            SEARCH RESULTS:
            - Websites: {', '.join(selected_websites)}
            - Successful: {successful_searches}/{len(selected_websites)}
            - Properties found: {total_properties}
            
            AGENT WORKFLOW:
            1. Property Search Agent: Find and analyze properties
            2. Market Analysis Agent: Provide ELABORATE market insights
            3. Property Valuation Agent: Give ELABORATE valuations
            
            IMPORTANT: Provide detailed, actionable insights with specific data points.
            Include relevant links and sources when possible.
            """
            
            # Show agent progression
            agent_messages = [
                "Property Search Agent: Processing property data",
                "Market Analysis Agent: Analyzing market trends", 
                "Property Valuation Agent: Evaluating property values"
            ]
            
            for i, message in enumerate(agent_messages):
                progress = 0.87 + (i * 0.03)
                update_progress(progress, "Analysis in progress...", message)
                time.sleep(1)
            
            # Execute agents
            if use_perplexity_fallback:
                with st.spinner("🔍 Searching rigorously across real estate platforms..."):
                    result = real_estate_team.run(prompt)
            else:
                result = real_estate_team.run(prompt)
            
            agent_duration = time.time() - agent_start
            total_time = time.time() - start_time
            
            # Display results
            st.markdown("---")
            display_property_results(result)
            
            # Download button
            if hasattr(result, 'content'):
                download_content = result.content
            else:
                download_content = str(result)
            
            st.download_button(
                label="Download Report",
                data=download_content,
                file_name="property_analysis_report.md",
                mime="text/markdown"
            )
            
            # Timing info
            st.info(f"⏱️ Total time: {total_time:.2f}s | Search: {search_duration:.2f}s | Agents: {agent_duration:.2f}s")
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()