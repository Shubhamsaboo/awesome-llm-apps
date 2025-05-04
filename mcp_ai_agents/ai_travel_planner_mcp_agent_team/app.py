import asyncio
import os

from agno.agent import Agent
from agno.team.team import Team
from agno.tools.mcp import MultiMCPTools
from agno.models.openai import OpenAIChat
import streamlit as st
from datetime import date

# Remove dotenv import and loading since we'll use sidebar
# from dotenv import load_dotenv
# load_dotenv()

async def run_agent(message: str):
    """Run the Airbnb, Google Maps, Weather and Calendar agent with the given message."""

    # Get API keys from session state
    google_maps_key = st.session_state.get('google_maps_key')
    accuweather_key = st.session_state.get('accuweather_key')
    openai_key = st.session_state.get('openai_key')
    google_client_id = st.session_state.get('google_client_id')
    google_client_secret = st.session_state.get('google_client_secret')
    google_refresh_token = st.session_state.get('google_refresh_token')

    if not google_maps_key:
        raise ValueError("🚨 Missing Google Maps API Key. Please enter it in the sidebar.")
    elif not accuweather_key:
        raise ValueError("🚨 Missing AccuWeather API Key. Please enter it in the sidebar.")
    elif not openai_key:
        raise ValueError("🚨 Missing OpenAI API Key. Please enter it in the sidebar.")
    elif not google_client_id:
        raise ValueError("🚨 Missing Google Client ID. Please enter it in the sidebar.")
    elif not google_client_secret:
        raise ValueError("🚨 Missing Google Client Secret. Please enter it in the sidebar.")
    elif not google_refresh_token:
        raise ValueError("🚨 Missing Google Refresh Token. Please enter it in the sidebar.")

    # 👉 Set OPENAI_API_KEY globally
    os.environ["OPENAI_API_KEY"] = openai_key

    env = {
        **os.environ,
        "GOOGLE_MAPS_API_KEY": google_maps_key,
        "ACCUWEATHER_API_KEY": accuweather_key,
        "OPENAI_API_KEY": openai_key,
        "GOOGLE_CLIENT_ID": google_client_id,
        "GOOGLE_CLIENT_SECRET": google_client_secret,
        "GOOGLE_REFRESH_TOKEN": google_refresh_token
    }

    async with MultiMCPTools(
        [
            "npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt", # ✅ Airbnb mcp added
            "npx -y @modelcontextprotocol/server-google-maps", # ✅ Google Maps mcp added
            "uvx --from git+https://github.com/adhikasp/mcp-weather.git mcp-weather", # ✅ Weather mcp added
            "./calendar_mcp.py"
        ],
        env=env,
    ) as mcp_tools:
        
        #Define specialized agents with enhanced instructions
        maps_agent = Agent(
            tools=[mcp_tools],
            model=OpenAIChat(id="gpt-4o-mini", api_key=openai_key),
            name="Maps Agent",
            goal="""As a Maps Agent, your responsibilities include:
            1. Finding optimal routes between locations
            2. Identifying points of interest near destinations
            3. Calculating travel times and distances
            4. Suggesting transportation options
            5. Finding nearby amenities and services
            6. Providing location-based recommendations
            
            Always consider:
            - Traffic conditions and peak hours
            - Alternative routes and transportation modes
            - Accessibility and convenience
            - Safety and well-lit areas
            - Proximity to other planned activities"""
        )

        weather_agent = Agent(
            tools=[mcp_tools],
            name="Weather Agent",
            model=OpenAIChat(id="gpt-4o-mini", api_key=openai_key),
            goal="""As a Weather Agent, your responsibilities include:
            1. Providing detailed weather forecasts for destinations
            2. Alerting about severe weather conditions
            3. Suggesting weather-appropriate activities
            4. Recommending the best travel times based on the weather conditions.
            5. Providing seasonal travel recommendations
            
            Always consider:
            - Temperature ranges and comfort levels
            - Precipitation probability
            - Wind conditions
            - UV index and sun protection
            - Seasonal variations
            - Weather alerts and warnings"""
        )

        booking_agent = Agent(
            tools=[mcp_tools],
            name="Booking Agent",
            model=OpenAIChat(id="gpt-4o-mini", api_key=openai_key),
            goal="""As a Booking Agent, your responsibilities include:
            1. Finding accommodations within budget on airbnb
            2. Comparing prices across platforms
            3. Checking availability for specific dates
            4. Verifying amenities and policies
            5. Finding last-minute deals when applicable
            
            Always consider:
            - Location convenience
            - Price competitiveness
            - Cancellation policies
            - Guest reviews and ratings
            - Amenities matching preferences
            - Special requirements or accessibility needs"""
        )

        calendar_agent = Agent(
            tools=[mcp_tools],
            name="Calendar Agent",
            model=OpenAIChat(id="gpt-4o-mini", api_key=openai_key),
            goal="""As a Calendar Agent, your responsibilities include:
            1. Creating detailed travel itineraries
            2. Setting reminders for bookings and check-ins
            3. Scheduling activities and reservations
            4. Adding reminders for booking deadlines, check-ins, and other important events.
            5. Coordinating with other team members' schedules
            
            Always consider:
            - Time zone differences
            - Travel duration between activities
            - Buffer time for unexpected delays
            - Important deadlines and check-in times
            - Synchronization with other team members"""
        )

        team = Team(
            members=[maps_agent, weather_agent, booking_agent, calendar_agent],
            name="Travel Planning Team",
            markdown=True,
            show_tool_calls=True,
            instructions="""As a Travel Planning Team, coordinate to create comprehensive travel plans:
            1. Share information between agents to ensure consistency
            2. Consider dependencies between different aspects of the trip
            3. Prioritize user preferences and constraints
            4. Provide backup options when primary choices are unavailable
            5. Maintain a balance between planned activities and free time
            6. Consider local events and seasonal factors
            7. Ensure all recommendations align with the user's budget
            8. Provide a detailed breakdown of the trip, including bookings, routes, weather, and planned activities.
            9. Add the journey start date in the user calendar"""
        )

        result = await team.arun(message)
        output = result.messages[-1].content
        return output  
    
# -------------------- Streamlit App --------------------
    
# Configure the page
st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide"
)

# Add sidebar for API keys
with st.sidebar:
    st.header("🔑 API Keys Configuration")
    st.markdown("Please enter your API keys to use the travel planner.")
    
    # Initialize session state for API keys if not exists
    if 'google_maps_key' not in st.session_state:
        st.session_state.google_maps_key = ""
    if 'accuweather_key' not in st.session_state:
        st.session_state.accuweather_key = ""
    if 'openai_key' not in st.session_state:
        st.session_state.openai_key = ""
    if 'google_client_id' not in st.session_state:
        st.session_state.google_client_id = ""
    if 'google_client_secret' not in st.session_state:
        st.session_state.google_client_secret = ""
    if 'google_refresh_token' not in st.session_state:
        st.session_state.google_refresh_token = ""

    # API key input fields
    st.session_state.google_maps_key = st.text_input(
        "Google Maps API Key",
        value=st.session_state.google_maps_key,
        type="password"
    )
    st.session_state.accuweather_key = st.text_input(
        "AccuWeather API Key",
        value=st.session_state.accuweather_key,
        type="password"
    )
    st.session_state.openai_key = st.text_input(
        "OpenAI API Key",
        value=st.session_state.openai_key,
        type="password"
    )
    st.session_state.google_client_id = st.text_input(
        "Google Client ID",
        value=st.session_state.google_client_id,
        type="password"
    )
    st.session_state.google_client_secret = st.text_input(
        "Google Client Secret",
        value=st.session_state.google_client_secret,
        type="password"
    )
    st.session_state.google_refresh_token = st.text_input(
        "Google Refresh Token",
        value=st.session_state.google_refresh_token,
        type="password"
    )

    # Check if all API keys are filled
    all_keys_filled = all([
        st.session_state.google_maps_key,
        st.session_state.accuweather_key,
        st.session_state.openai_key,
        st.session_state.google_client_id,
        st.session_state.google_client_secret,
        st.session_state.google_refresh_token
    ])

    if not all_keys_filled:
        st.warning("⚠️ Please fill in all API keys to use the travel planner.")
    else:
        st.success("✅ All API keys are configured!")

# Title and description
st.title("✈️ AI Travel Planner")
st.markdown("""
This AI-powered travel planner helps you create personalized travel itineraries using:
- 🗺️ Maps and navigation
- 🌤️ Weather forecasts
- 🏨 Accommodation booking
- 📅 Calendar management
""")

# Create two columns for input
col1, col2 = st.columns(2)

with col1:
    # Source and Destination
    source = st.text_input("Source", placeholder="Enter your departure city")
    destination = st.text_input("Destination", placeholder= "Enter your destination city")
    
    # Travel Dates
    travel_dates = st.date_input(
        "Travel Dates",
        [date.today(), date.today()],
        min_value=date.today(),
        help="Select your travel dates"
    )

with col2:
    # Budget
    budget = st.number_input(
        "Budget (in USD)",
        min_value=0,
        max_value=10000,
        step=100,
        help="Enter your total budget for the trip"
    )
    
    # Travel Preferences
    travel_preferences = st.multiselect(
        "Travel Preferences",
        ["Adventure", "Relaxation", "Sightseeing", "Cultural Experiences", 
         "Beach", "Mountain", "Luxury", "Budget-Friendly", "Food & Dining",
         "Shopping", "Nightlife", "Family-Friendly"],
        help="Select your travel preferences"
    )

# Additional preferences
st.subheader("Additional Preferences")
col3, col4 = st.columns(2)

with col3:
    accommodation_type = st.selectbox(
        "Preferred Accommodation",
        ["Any", "Hotel", "Hostel", "Apartment", "Resort"],
        help="Select your preferred type of accommodation"
    )
    
    transportation_mode = st.multiselect(
        "Preferred Transportation",
        ["Train", "Bus", "Flight", "Rental Car"],
        help="Select your preferred modes of transportation"
    )

with col4:
    dietary_restrictions = st.multiselect(
        "Dietary Restrictions",
        ["None", "Vegetarian", "Vegan", "Gluten-Free", "Halal", "Kosher"],
        help="Select any dietary restrictions"
    )

# Submit Button
if st.button("Plan My Trip", type="primary", disabled=not all_keys_filled):
    if not source or not destination:
        st.error("Please enter both source and destination cities.")
    elif not travel_preferences:
        st.warning("Consider selecting some travel preferences for better recommendations.")
    else:
        # Create a loading spinner
        with st.spinner("🤖 AI Agents are planning your perfect trip..."):
            try:
                # Construct the message for the agents
                message = f"""
                Plan a trip with the following details:
                - From: {source}
                - To: {destination}
                - Dates: {travel_dates[0]} to {travel_dates[1]}
                - Budget in USD: ${budget}
                - Preferences: {', '.join(travel_preferences)}
                - Accommodation: {accommodation_type}
                - Transportation: {', '.join(transportation_mode)}
                - Dietary Restrictions: {', '.join(dietary_restrictions)}
                
                Please provide a comprehensive travel plan including:
                1. Recommended accommodations
                2. Daily itinerary with activities
                3. Transportation options
                4. The Expected Day Weather
                5. Estimated cost of the Trip
                6. Add the Departure Date to the calendar
                """
                
                # Run the agents
                response = asyncio.run(run_agent(message))
                
                # Display the response
                st.success("✅ Your travel plan is ready!")
                st.markdown(response)
                
            except Exception as e:
                st.error(f"An error occurred while planning your trip: {str(e)}")
                st.info("Please try again or contact support if the issue persists.")

# Add a footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Powered by AI Travel Planning Agents</p>
    <p>Your personal travel assistant for creating memorable experiences</p>
</div>
""", unsafe_allow_html=True)