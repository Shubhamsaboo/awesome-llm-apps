import os
import streamlit as st
import json
import time
import requests
from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat
from agno.tools.googlesearch import GoogleSearchTools
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field
from typing import List, Optional

# Load environment variables
load_dotenv()

# API keys - must be set in environment variables
DEFAULT_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEFAULT_FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")

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

def search_google_properties(city, state, user_criteria):
    """Search for properties using Google Search"""
    try:
        # Create Google Search query
        search_query = f"""
        Find real estate properties for sale {city} {state}
        budget {user_criteria.get('budget_range', '')}
        {user_criteria.get('property_type', '')} 
        {user_criteria.get('bedrooms', '')} bedrooms
        {user_criteria.get('bathrooms', '')} bathrooms
        {user_criteria.get('min_sqft', '')} sqft
        {user_criteria.get('special_features', '')}
        site:zillow.com OR site:realtor.com OR site:trulia.com OR site:homes.com OR site:redfin.com
        """
        
        # Use GoogleSearchTools to perform the search
        google_search = GoogleSearchTools()
        search_results = google_search.google_search(
            query=search_query,
            max_results=10,
            language="en"
        )
        
        return {"success": True, "content": search_results, "source": "Google Search"}
            
    except Exception as e:
        return {"error": f"Google search failed: {str(e)}"}

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
            update_callback(progress, f"Searching {site_name}...", f"🔍 Analyzing {site_name}...")
            
            if i > 0:
                time.sleep(1.5)  # Reduced delay for better UX
            
            result = extract_property_listings(search_url, user_criteria)
            
            if "error" not in result and len(result.get('properties', [])) > 0:
                results[site_name] = result
                property_count = len(result.get('properties', []))
                update_callback(progress + 0.3, f"Found {property_count} properties on {site_name}", f"✅ Successfully analyzed {site_name} ({property_count} properties)")
            else:
                results[site_name] = {"error": f"No data from {site_name}"}
                update_callback(progress + 0.3, f"Analyzing {site_name}", f"⚠️ No properties found on {site_name}")
                
        except Exception as e:
            results[site_name] = {"error": f"Error: {str(e)}"}
            update_callback(progress + 0.3, f"Analyzing {site_name}", f"❌ Error processing {site_name}")
    
    return results

def create_firecrawl_tools(user_criteria):
    """Create tools for agents"""
    
    def extract_listings_tool(url: str) -> str:
        result = extract_property_listings(url, user_criteria)
        return json.dumps(result, indent=2) if "error" not in result else f"Error: {result['error']}"
    
    def google_search_tool(city: str, state: str) -> str:
        result = search_google_properties(city, state, user_criteria)
        return json.dumps(result, indent=2) if "error" not in result else f"Error: {result['error']}"
    
    # Include both Firecrawl extract and Google Search tools
    tools = [extract_listings_tool, google_search_tool]
    
    return tools

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
           - Use Google Search tool if extract methods don't find properties
        
        2. GATHER PROPERTY DATA:
           - Extract detailed property information
           - Collect listing URLs and agent contacts
           - Organize results clearly
        
        3. PROVIDE STRUCTURED OUTPUT:
           - List properties with full details
           - Include clickable listing URLs
           - Rank by match quality
        
        IMPORTANT: Use google_search_tool if extract methods don't find properties.
        Google Search will find relevant real estate listings from Zillow, Realtor.com, Trulia, Homes.com, and Redfin.
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
        name="🏠 AI Real Estate Agent Team",
        mode="coordinate",
        model=llm,
        members=[property_search_agent, market_analysis_agent, property_valuation_agent],
        instructions=[
            "You are a professional AI Real Estate Agent Team.",
            "1. Property Search Agent: Find properties using extract + Google Search fallback",
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
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem;">
        <h3 style="color: white; text-align: center; margin: 0;">🤖 AI-Powered Real Estate Recommendations</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if hasattr(result, 'content'):
        result_text = result.content
    else:
        result_text = str(result)
    
    # Display the full text result with markdown support for links
    st.markdown("### 📋 Analysis Report")
    st.markdown(result_text)
    
    # Extract and display clickable links
    import re
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', result_text)
    
    if urls:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin: 2rem 0;">
            <h3 style="color: #667eea; margin-bottom: 1rem;">🔗 Property Links</h3>
        """, unsafe_allow_html=True)
        
        for i, url in enumerate(set(urls), 1):
            st.markdown(f"""
            <div style="margin: 0.5rem 0; padding: 0.5rem; background: #f8f9fa; border-radius: 5px;">
                <a href="{url}" target="_blank" style="color: #667eea; text-decoration: none; font-weight: 600;">
                    {i}. {url}
                </a>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

def main():
    st.set_page_config(
        page_title="AI Real Estate Agent Team", 
        page_icon="🏠", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        color: white;
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .main-header p {
        color: rgba(255,255,255,0.9);
        text-align: center;
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
    }
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    .status-info {
        background: linear-gradient(90deg, #2196F3, #1976D2);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        margin: 0.5rem 0;
        text-align: center;
    }
    .status-success {
        background: linear-gradient(90deg, #4CAF50, #45a049);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        margin: 0.5rem 0;
        text-align: center;
    }
    .status-error {
        background: linear-gradient(90deg, #f44336, #da190b);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        margin: 0.5rem 0;
        text-align: center;
    }
    .form-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        margin: 2rem 0;
    }
    .progress-container {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        color: white;
    }
    .result-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        margin: 2rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Beautiful header
    st.markdown("""
    <div class="main-header">
        <h1>🏠 AI Real Estate Agent Team</h1>
        <p>Find Your Dream Home with Specialized AI Agents</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
            <h3 style="color: white; margin: 0; text-align: center;">⚙️ Configuration</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # API Key inputs with validation
        with st.expander("🔑 API Keys", expanded=True):
            openai_key = st.text_input(
                "OpenAI API Key", 
                value=DEFAULT_OPENAI_API_KEY, 
                type="password",
                help="Get your API key from https://platform.openai.com/api-keys",
                placeholder="sk-..."
            )
            firecrawl_key = st.text_input(
                "Firecrawl API Key", 
                value=DEFAULT_FIRECRAWL_API_KEY, 
                type="password",
                help="Get your API key from https://firecrawl.dev",
                placeholder="fc_..."
            )
            
            # Update environment variables
            if openai_key: os.environ["OPENAI_API_KEY"] = openai_key
            if firecrawl_key: os.environ["FIRECRAWL_API_KEY"] = firecrawl_key
        
        # Website selection
        with st.expander("🌐 Search Sources", expanded=True):
            st.markdown("**Select real estate websites to search:**")
            available_websites = ["Zillow", "Realtor.com", "Trulia", "Homes.com"]
            selected_websites = [site for site in available_websites if st.checkbox(site, value=site in ["Zillow", "Realtor.com"])]
            
            if selected_websites:
                st.markdown(f'<div class="status-success">✅ {len(selected_websites)} sources selected</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-error">⚠️ Please select at least one website</div>', unsafe_allow_html=True)
        
        # How it works
        with st.expander("🤖 How It Works", expanded=False):
            st.markdown("""
            <div class="feature-card">
                <h4>🔍 Property Search Agent</h4>
                <p>Uses extract + Google Search fallback</p>
            </div>
            <div class="feature-card">
                <h4>📊 Market Analysis Agent</h4>
                <p>Analyzes trends and neighborhood insights</p>
            </div>
            <div class="feature-card">
                <h4>💰 Property Valuation Agent</h4>
                <p>Evaluates values and investment potential</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Main form
    st.markdown("""
    <div class="form-container">
        <h2 style="color: #667eea; margin-bottom: 1.5rem; text-align: center;">🏠 Your Property Requirements</h2>
    """, unsafe_allow_html=True)
    
    with st.form("property_preferences"):
        # Location and Budget Section
        st.markdown("### 📍 Location & Budget")
        col1, col2 = st.columns(2)
        
        with col1:
            city = st.text_input(
                "🏙️ City", 
                placeholder="e.g., San Francisco",
                help="Enter the city where you want to buy property"
            )
            state = st.text_input(
                "🗺️ State/Province (optional)", 
                placeholder="e.g., CA",
                help="Enter the state or province (optional)"
            )
        
        with col2:
            min_price = st.number_input(
                "💰 Minimum Price ($)", 
                min_value=0, 
                value=500000, 
                step=50000,
                help="Your minimum budget for the property"
            )
            max_price = st.number_input(
                "💰 Maximum Price ($)", 
                min_value=0, 
                value=1500000, 
                step=50000,
                help="Your maximum budget for the property"
            )
        
        # Property Details Section
        st.markdown("### 🏡 Property Details")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            property_type = st.selectbox(
                "🏠 Property Type",
                ["Any", "House", "Condo", "Townhouse", "Apartment"],
                help="Type of property you're looking for"
            )
            bedrooms = st.selectbox(
                "🛏️ Bedrooms",
                ["Any", "1", "2", "3", "4", "5+"],
                help="Number of bedrooms required"
            )
        
        with col2:
            bathrooms = st.selectbox(
                "🚿 Bathrooms",
                ["Any", "1", "1.5", "2", "2.5", "3", "3.5", "4+"],
                help="Number of bathrooms required"
            )
            min_sqft = st.number_input(
                "📏 Minimum Square Feet",
                min_value=0,
                value=1000,
                step=100,
                help="Minimum square footage required"
            )
        
        with col3:
            timeline = st.selectbox(
                "⏰ Timeline",
                ["Flexible", "1-3 months", "3-6 months", "6+ months"],
                help="When do you plan to buy?"
            )
            urgency = st.selectbox(
                "🚨 Urgency",
                ["Not urgent", "Somewhat urgent", "Very urgent"],
                help="How urgent is your purchase?"
            )
        
        # Special Features
        st.markdown("### ✨ Special Features")
        special_features = st.text_area(
            "🎯 Special Features & Requirements",
            placeholder="e.g., Parking, Yard, View, Near public transport, Good schools, Walkable neighborhood, etc.",
            help="Any specific features or requirements you're looking for"
        )
        
        # Submit button with custom styling
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "🚀 Start Property Analysis",
                type="primary",
                use_container_width=True
            )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Process form submission
    if submitted:
        # Validate all required inputs
        missing_items = []
        if not openai_key:
            missing_items.append("OpenAI API Key")
        if not firecrawl_key:
            missing_items.append("Firecrawl API Key")
        if not city:
            missing_items.append("City")
        if not selected_websites:
            missing_items.append("At least one website selection")
        
        if missing_items:
            st.markdown(f"""
            <div class="status-error" style="text-align: center; margin: 2rem 0;">
                ⚠️ Please provide: {', '.join(missing_items)}
            </div>
            """, unsafe_allow_html=True)
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
            st.markdown(f"""
            <div class="status-error" style="text-align: center; margin: 2rem 0;">
                ❌ Error initializing: {str(e)}
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Display progress
        st.markdown("""
        <div class="progress-container">
            <h2 style="color: white; text-align: center; margin-bottom: 1rem;">🚀 Property Analysis in Progress</h2>
            <div style="text-align: center; margin-bottom: 1rem;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔍</div>
                <div style="font-size: 1.1rem; opacity: 0.9;">AI Agents are working together to find your perfect home</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        status_container = st.container()
        with status_container:
            st.markdown("### 📊 Current Activity")
            progress_bar = st.progress(0)
            current_activity = st.empty()
        
        def update_progress(progress, status, activity=None):
            if activity:
                progress_bar.progress(progress)
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
            use_google_fallback = total_properties == 0
            
            if use_google_fallback:
                update_progress(0.85, "Running analysis...", "🔍 Searching Google for real estate listings...")
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
            
            # Show agent progression with better messaging
            agent_messages = [
                "🔍 Property Search Agent: Processing property data and listings",
                "📊 Market Analysis Agent: Analyzing market trends and neighborhood insights", 
                "💰 Property Valuation Agent: Evaluating property values and investment potential"
            ]
            
            for i, message in enumerate(agent_messages):
                progress = 0.87 + (i * 0.03)
                update_progress(progress, "Analysis in progress...", message)
                time.sleep(1.5)  # Slightly longer for better UX
            
            # Execute agents with better UX
            if use_google_fallback:
                with st.spinner("🔍 Searching Google for real estate listings..."):
                    result = real_estate_team.run(prompt)
            else:
                with st.spinner("🤖 AI Agents are analyzing your property requirements..."):
                    result = real_estate_team.run(prompt)
            
            agent_duration = time.time() - agent_start
            total_time = time.time() - start_time
            
            # Display results
            st.markdown("""
            <div class="result-container">
                <h2 style="color: #667eea; text-align: center; margin-bottom: 2rem;">🎉 Analysis Complete!</h2>
            """, unsafe_allow_html=True)
            display_property_results(result)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Download button with better styling
            if hasattr(result, 'content'):
                download_content = result.content
            else:
                download_content = str(result)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="📄 Download Full Report",
                    data=download_content,
                    file_name="property_analysis_report.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            # Timing info with better styling
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 1rem; border-radius: 10px; text-align: center; margin: 2rem 0;">
                <h4 style="color: #667eea; margin-bottom: 0.5rem;">⏱️ Performance Metrics</h4>
                <p style="margin: 0; color: #6c757d;">
                    Total: <strong>{total_time:.2f}s</strong> | 
                    Search: <strong>{search_duration:.2f}s</strong> | 
                    AI Analysis: <strong>{agent_duration:.2f}s</strong>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.markdown(f"""
            <div class="status-error" style="text-align: center; margin: 2rem 0;">
                ❌ An error occurred: {str(e)}
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()