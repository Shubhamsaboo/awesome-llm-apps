import re
import asyncio
from textwrap import dedent
from agno.agent import Agent
from agno.tools.mcp import MultiMCPTools
from agno.tools.googlesearch import GoogleSearchTools
from agno.models.openai import OpenAIChat
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import streamlit as st
from datetime import date
import os

def generate_ics_content(plan_text: str, start_date: datetime = None) -> bytes:
    """
    Generate an ICS calendar file from a travel itinerary text.

    Args:
        plan_text: The travel itinerary text
        start_date: Optional start date for the itinerary (defaults to today)

    Returns:
        bytes: The ICS file content as bytes
    """
    cal = Calendar()
    cal.add('prodid','-//AI Travel Planner//github.com//')
    cal.add('version', '2.0')

    if start_date is None:
        start_date = datetime.today()

    # Split the plan into days
    day_pattern = re.compile(r'Day (\d+)[:\s]+(.*?)(?=Day \d+|$)', re.DOTALL)
    days = day_pattern.findall(plan_text)

    if not days:  # If no day pattern found, create a single all-day event with the entire content
        event = Event()
        event.add('summary', "Travel Itinerary")
        event.add('description', plan_text)
        event.add('dtstart', start_date.date())
        event.add('dtend', start_date.date())
        event.add("dtstamp", datetime.now())
        cal.add_component(event)
    else:
        # Process each day
        for day_num, day_content in days:
            day_num = int(day_num)
            current_date = start_date + timedelta(days=day_num - 1)

            # Create a single event for the entire day
            event = Event()
            event.add('summary', f"Day {day_num} Itinerary")
            event.add('description', day_content.strip())

            # Make it an all-day event
            event.add('dtstart', current_date.date())
            event.add('dtend', current_date.date())
            event.add("dtstamp", datetime.now())
            cal.add_component(event)

    return cal.to_ical()

async def run_mcp_travel_planner(destination: str, num_days: int, preferences: str, budget: int, openai_key: str, google_maps_key: str):
    """Run the MCP-based travel planner agent with real-time data access."""

    try:
        # Set Google Maps API key environment variable
        os.environ["GOOGLE_MAPS_API_KEY"] = google_maps_key

        # Initialize MCPTools with Airbnb MCP
        mcp_tools = MultiMCPTools(
            [
            "npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt",
            "npx @gongrzhe/server-travelplanner-mcp",
            ],      
            env={
                "GOOGLE_MAPS_API_KEY": google_maps_key,
            },
            timeout_seconds=60,
        )   

        # Connect to Airbnb MCP server
        await mcp_tools.connect()


        travel_planner = Agent(
            name="Travel Planner",
            role="Creates travel itineraries using Airbnb, Google Maps, and Google Search",
            model=OpenAIChat(id="gpt-4o", api_key=openai_key),
            description=dedent(
                """\
                You are a professional travel consultant AI that creates highly detailed travel itineraries directly without asking questions.

                You have access to:
                🏨 Airbnb listings with real availability and current pricing
                🗺️ Google Maps MCP for location services, directions, distance calculations, and local navigation
                🔍 Web search capabilities for current information, reviews, and travel updates

                ALWAYS create a complete, detailed itinerary immediately without asking for clarification or additional information.
                Use Google Maps MCP extensively to calculate distances between all locations and provide precise travel times.
                If information is missing, use your best judgment and available tools to fill in the gaps.
                """
            ),
            instructions=[
                "IMPORTANT: Never ask questions or request clarification - always generate a complete itinerary",
                "Research the destination thoroughly using all available tools to gather comprehensive current information",
                "Find suitable accommodation options within the budget using Airbnb MCP with real prices and availability",
                "Create an extremely detailed day-by-day itinerary with specific activities, locations, exact timing, and distances",
                "Use Google Maps MCP extensively to calculate distances between ALL locations and provide travel times",
                "Include detailed transportation options and turn-by-turn navigation tips using Google Maps MCP",
                "Research dining options with specific restaurant names, addresses, price ranges, and distance from accommodation",
                "Check current weather conditions, seasonal factors, and provide detailed packing recommendations",
                "Calculate precise estimated costs for EVERY aspect of the trip and ensure recommendations fit within budget",
                "Include detailed information about each attraction: opening hours, ticket prices, best visiting times, and distance from accommodation",
                "Add practical information including local transportation costs, currency exchange, safety tips, and cultural norms",
                "Structure the itinerary with clear sections, detailed timing for each activity, and include buffer time between activities",
                "Use all available tools proactively without asking for permission",
                "Generate the complete, detailed itinerary in one response without follow-up questions"
            ],
            tools=[mcp_tools, GoogleSearchTools()],
            add_datetime_to_instructions=True,
            markdown=True,
            show_tool_calls=False,
        )

        # Create the planning prompt
        prompt = f"""
        IMMEDIATELY create an extremely detailed and comprehensive travel itinerary for:

        **Destination:** {destination}
        **Duration:** {num_days} days
        **Budget:** ${budget} USD total
        **Preferences:** {preferences}

        DO NOT ask any questions. Generate a complete, highly detailed itinerary now using all available tools.

        **CRITICAL REQUIREMENTS:**
        - Use Google Maps MCP to calculate distances and travel times between ALL locations
        - Include specific addresses for every location, restaurant, and attraction
        - Provide detailed timing for each activity with buffer time between locations
        - Calculate precise costs for transportation between each location
        - Include opening hours, ticket prices, and best visiting times for all attractions
        - Provide detailed weather information and specific packing recommendations

        **REQUIRED OUTPUT FORMAT:**
        1. **Trip Overview** - Summary, total estimated cost breakdown, detailed weather forecast
        2. **Accommodation** - 3 specific Airbnb options with real prices, addresses, amenities, and distance from city center
        3. **Transportation Overview** - Detailed transportation options, costs, and recommendations
        4. **Day-by-Day Itinerary** - Extremely detailed schedule with:
           - Specific start/end times for each activity
           - Exact distances and travel times between locations (use Google Maps MCP)
           - Detailed descriptions of each location with addresses
           - Opening hours, ticket prices, and best visiting times
           - Estimated costs for each activity and transportation
           - Buffer time between activities for unexpected delays
        5. **Dining Plan** - Specific restaurants with addresses, price ranges, cuisine types, and distance from accommodation
        6. **Detailed Practical Information**:
           - Weather forecast with clothing recommendations
           - Currency exchange rates and costs
           - Local transportation options and costs
           - Safety information and emergency contacts
           - Cultural norms and etiquette tips
           - Communication options (SIM cards, WiFi, etc.)
           - Health and medical considerations
           - Shopping and souvenir recommendations

        Use Airbnb MCP for real accommodation data, Google Maps MCP for ALL distance calculations and location services, and web search for current information.
        Make reasonable assumptions and fill in any gaps with your knowledge.
        Generate the complete, highly detailed itinerary in one response without asking for clarification.
        """

        response = await travel_planner.arun(prompt)
        return response.content

    finally:
        await mcp_tools.close()

def run_travel_planner(destination: str, num_days: int, preferences: str, budget: int, openai_key: str, google_maps_key: str):
    """Synchronous wrapper for the async MCP travel planner."""
    return asyncio.run(run_mcp_travel_planner(destination, num_days, preferences, budget, openai_key, google_maps_key))
    
# -------------------- Streamlit App --------------------
    
# Configure the page
st.set_page_config(
    page_title="MCP AI Travel Planner",
    page_icon="✈️",
    layout="wide"
)

# Initialize session state
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = None

# Title and description
st.title("✈️ MCP AI Travel Planner")
st.caption("Plan your next adventure with AI Travel Planner using MCP servers for real-time data access")

# Sidebar for API keys
with st.sidebar:
    st.header("🔑 API Keys Configuration")
    st.warning("⚠️ These services require API keys:")

    openai_api_key = st.text_input("OpenAI API Key", type="password", help="Required for AI planning")
    google_maps_key = st.text_input("Google Maps API Key", type="password", help="Required for location services")

    # Check if API keys are provided (both OpenAI and Google Maps are required)
    api_keys_provided = openai_api_key and google_maps_key

    if api_keys_provided:
        st.success("✅ All API keys configured!")
    else:
        st.warning("⚠️ Please enter both API keys to use the travel planner.")
        st.info("""
        **Required API Keys:**
        - **OpenAI API Key**: https://platform.openai.com/api-keys
        - **Google Maps API Key**: https://console.cloud.google.com/apis/credentials (for location services)
        """)

# Main content (only shown if API keys are provided)
if api_keys_provided:
    # Main input section
    st.header("🌍 Trip Details")

    col1, col2 = st.columns(2)

    with col1:
        destination = st.text_input("Destination", placeholder="e.g., Paris, Tokyo, New York")
        num_days = st.number_input("Number of Days", min_value=1, max_value=30, value=7)

    with col2:
        budget = st.number_input("Budget (USD)", min_value=100, max_value=10000, step=100, value=2000)
        start_date = st.date_input("Start Date", min_value=date.today(), value=date.today())

    # Preferences section
    st.subheader("🎯 Travel Preferences")
    preferences_input = st.text_area(
        "Describe your travel preferences",
        placeholder="e.g., adventure activities, cultural sites, food, relaxation, nightlife...",
        height=100
    )

    # Quick preference buttons
    quick_prefs = st.multiselect(
        "Quick Preferences (optional)",
        ["Adventure", "Relaxation", "Sightseeing", "Cultural Experiences",
         "Beach", "Mountain", "Luxury", "Budget-Friendly", "Food & Dining",
         "Shopping", "Nightlife", "Family-Friendly"],
        help="Select multiple preferences or describe in detail above"
    )

    # Combine preferences
    all_preferences = []
    if preferences_input:
        all_preferences.append(preferences_input)
    if quick_prefs:
        all_preferences.extend(quick_prefs)

    preferences = ", ".join(all_preferences) if all_preferences else "General sightseeing"

    # Generate button
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("🎯 Generate Itinerary", type="primary"):
            if not destination:
                st.error("Please enter a destination.")
            elif not preferences:
                st.warning("Please describe your preferences or select quick preferences.")
            else:
                tools_message = "🏨 Connecting to Airbnb MCP"
                if google_maps_key:
                    tools_message += " and Google Maps MCP"
                tools_message += ", creating itinerary..."

                with st.spinner(tools_message):
                    try:
                        # Calculate number of days from start date
                        response = run_travel_planner(
                            destination=destination,
                            num_days=num_days,
                            preferences=preferences,
                            budget=budget,
                            openai_key=openai_api_key,
                            google_maps_key=google_maps_key or ""
                        )

                        # Store the response in session state
                        st.session_state.itinerary = response

                        # Show MCP connection status
                        if "Airbnb" in response and ("listing" in response.lower() or "accommodation" in response.lower()):
                            st.success("✅ Your travel itinerary is ready with Airbnb data!")
                            st.info("🏨 Used real Airbnb listings for accommodation recommendations")
                        else:
                            st.success("✅ Your travel itinerary is ready!")
                            st.info("📝 Used general knowledge for accommodation suggestions (Airbnb MCP may have failed to connect)")

                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        st.info("Please try again or check your internet connection.")

    with col2:
        if st.session_state.itinerary:
            # Generate the ICS file
            ics_content = generate_ics_content(st.session_state.itinerary, datetime.combine(start_date, datetime.min.time()))

            # Provide the file for download
            st.download_button(
                label="📅 Download as Calendar",
                data=ics_content,
                file_name="travel_itinerary.ics",
                mime="text/calendar"
            )

    # Display itinerary
    if st.session_state.itinerary:
        st.header("📋 Your Travel Itinerary")
        st.markdown(st.session_state.itinerary)