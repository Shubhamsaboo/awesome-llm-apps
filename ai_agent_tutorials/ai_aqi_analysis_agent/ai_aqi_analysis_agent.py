"""
AQI Analysis Assistant
---------------------
A Streamlit application that provides health recommendations based on air quality conditions.
Uses Firecrawl for AQI data and OpenAI for health recommendations.
"""

from typing import Dict, Optional, TypedDict
from dataclasses import dataclass
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from firecrawl import FirecrawlApp
import streamlit as st
import asyncio

# Data Models
class AQIExtractSchema(BaseModel):
    """Schema for AQI data extraction"""
    aqi: int = Field(description="Current AQI value")
    temperature: float = Field(description="Temperature in Celsius")
    humidity: float = Field(description="Humidity percentage")
    wind_speed: float = Field(description="Wind speed in km/h")
    pm25: float = Field(description="PM2.5 level in µg/m³")
    pm10: float = Field(description="PM10 level in µg/m³")
    co: float = Field(description="CO level in ppb")

@dataclass
class UserInput:
    """Structure for user input data"""
    city: str
    state: str
    country: str
    medical_conditions: Optional[str]
    planned_activity: str

# Agent Classes
class AQIDataAgent:
    """Agent responsible for fetching AQI and weather data"""
    
    def __init__(self, firecrawl_key: str, openai_key: str) -> None:
        """Initialize with API keys"""
        self.firecrawl = FirecrawlApp(api_key=firecrawl_key)
        self.agent = Agent(
            model=OpenAIChat(
                id="gpt-4o",
                api_key=openai_key
            ),
            description="Expert in analyzing air quality data and weather conditions"
        )
    
    def _format_url(self, country: str, state: str, city: str) -> str:
        """Format location URL with proper formatting for multi-word locations"""
        return f"https://www.aqi.in/dashboard/{country.lower().replace(' ', '-')}/{state.lower().replace(' ', '-')}/{city.lower().replace(' ', '-')}"
    
    async def fetch_data(self, city: str, state: str, country: str) -> AQIExtractSchema:
        """Fetch weather and AQI data for given location"""
        try:
            base_url = self._format_url(country, state, city)
            urls = [base_url, f"{base_url}/pm", f"{base_url}/co", f"{base_url}/pm10"]
            
            extract_prompt = """
            Extract the following air quality and weather metrics from the page:
            - Current AQI value as an integer
            - Temperature in Celsius as a float
            - Humidity percentage as a float
            - Wind speed in km/h as a float
            - PM2.5 level in µg/m³ as a float
            - PM10 level in µg/m³ as a float
            - CO level in ppb as a float
            
            Return these exact metrics with their specified types.
            """
            
            response = self.firecrawl.extract(
                urls=urls,
                params={
                    'prompt': extract_prompt,
                    'schema': AQIExtractSchema.model_json_schema()
                }
            )
            
            if isinstance(response, dict) and 'error' in response:
                raise ValueError(f"Firecrawl error: {response['error']}")
                
            return AQIExtractSchema(**response)
            
        except Exception as e:
            st.error(f"Error fetching AQI data: {str(e)}")
            # Return default values if fetch fails
            return AQIExtractSchema(
                aqi=0,
                temperature=0.0,
                humidity=0.0,
                wind_speed=0.0,
                pm25=0.0,
                pm10=0.0,
                co=0.0
            )

class HealthRecommendationAgent:
    """Agent responsible for providing health recommendations"""
    
    def __init__(self, openai_key: str) -> None:
        """Initialize with OpenAI API key"""
        self.agent = Agent(
            model=OpenAIChat(
                id="gpt-4o",
                api_key=openai_key
            ),
            description="Health recommendation expert for air quality conditions"
        )
    
    async def get_recommendations(
        self, 
        aqi_data: AQIExtractSchema,
        user_input: UserInput
    ) -> str:
        """Generate health recommendations based on conditions"""
        prompt = self._create_prompt(aqi_data, user_input)
        response = await self.agent.run(prompt)
        return response.content
    
    def _create_prompt(
        self,
        aqi_data: AQIExtractSchema,
        user_input: UserInput
    ) -> str:
        """Create detailed prompt for health recommendations"""
        return f"""
        Based on the following air quality conditions in {user_input.city}, {user_input.state}, {user_input.country}:
        - Overall AQI: {aqi_data.aqi}
        - PM2.5 Level: {aqi_data.pm25} µg/m³
        - PM10 Level: {aqi_data.pm10} µg/m³
        - CO Level: {aqi_data.co} ppb
        
        Weather conditions:
        - Temperature: {aqi_data.temperature}°C
        - Humidity: {aqi_data.humidity}%
        - Wind Speed: {aqi_data.wind_speed} km/h
        
        User's Context:
        - Medical Conditions: {user_input.medical_conditions or 'None'}
        - Planned Activity: {user_input.planned_activity}
        
        Provide detailed health recommendations considering:
        1. Current air quality impacts on health
        2. Safety precautions needed
        3. Whether the planned activity is advisable
        4. Alternative activity suggestions if needed
        5. Best time to conduct the activity if applicable
        """

# Main Analysis Function
async def analyze_conditions(
    user_input: UserInput,
    api_keys: Dict[str, str]
) -> str:
    """Main function to analyze conditions and provide recommendations"""
    # Initialize agents
    aqi_agent = AQIDataAgent(
        firecrawl_key=api_keys['firecrawl'],
        openai_key=api_keys['openai']
    )
    health_agent = HealthRecommendationAgent(
        openai_key=api_keys['openai']
    )
    
    # Get data and recommendations
    aqi_data = await aqi_agent.fetch_data(
        city=user_input.city,
        state=user_input.state,
        country=user_input.country
    )
    
    return await health_agent.get_recommendations(aqi_data, user_input)

# Streamlit UI Components
def initialize_session_state():
    """Initialize Streamlit session state"""
    if 'api_keys' not in st.session_state:
        st.session_state.api_keys = {
            'firecrawl': '',
            'openai': ''
        }

def setup_page():
    """Configure page settings and styles"""
    st.set_page_config(
        page_title="AQI Analysis Assistant",
        page_icon="🌍",
        layout="wide"
    )
    
    st.markdown("""
        <style>
        .main { padding: 2rem; }
        .stButton > button { width: 100%; }
        .success-message { 
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #dcfce7;
            color: #166534;
        }
        .error-message {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #fee2e2;
            color: #991b1b;
        }
        </style>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render sidebar with API configuration"""
    with st.sidebar:
        st.header("🔑 API Configuration")
        
        new_firecrawl_key = st.text_input(
            "Firecrawl API Key",
            type="password",
            value=st.session_state.api_keys['firecrawl'],
            help="Enter your Firecrawl API key"
        )
        new_openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=st.session_state.api_keys['openai'],
            help="Enter your OpenAI API key"
        )
        
        if (new_firecrawl_key != st.session_state.api_keys['firecrawl'] or 
            new_openai_key != st.session_state.api_keys['openai']):
            st.session_state.api_keys.update({
                'firecrawl': new_firecrawl_key,
                'openai': new_openai_key
            })
            st.success("✅ API keys updated!")

def render_main_content():
    """Render main content area"""
    st.title("🌍 AQI Analysis Assistant")
    st.markdown("Get personalized health recommendations based on air quality conditions.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📍 Location Details")
        city = st.text_input("City", placeholder="e.g., Mumbai")
        state = st.text_input("State", placeholder="e.g., Maharashtra")
        country = st.text_input("Country", value="India")
        
        st.header("👤 Personal Details")
        medical_conditions = st.text_area(
            "Medical Conditions (optional)",
            placeholder="e.g., asthma, allergies"
        )
        planned_activity = st.text_area(
            "Planned Activity",
            placeholder="e.g., morning jog for 2 hours"
        )
    
    return UserInput(
        city=city,
        state=state,
        country=country,
        medical_conditions=medical_conditions,
        planned_activity=planned_activity
    )

def main():
    """Main application entry point"""
    initialize_session_state()
    setup_page()
    render_sidebar()
    user_input = render_main_content()
    
    if st.button("🔍 Analyze & Get Recommendations"):
        if not all([user_input.city, user_input.state, user_input.planned_activity]):
            st.error("Please fill in all required fields (medical conditions are optional)")
        elif not all(st.session_state.api_keys.values()):
            st.error("Please provide both API keys in the sidebar")
        else:
            try:
                with st.spinner("🔄 Analyzing conditions..."):
                    result = asyncio.run(
                        analyze_conditions(
                            user_input=user_input,
                            api_keys=st.session_state.api_keys
                        )
                    )
                    
                    st.success("✅ Analysis completed!")
                    st.markdown("### 📊 Recommendations")
                    st.markdown(result)
                    
                    st.download_button(
                        "💾 Download Recommendations",
                        data=result,
                        file_name=f"aqi_recommendations_{user_input.city}_{user_input.state}.txt",
                        mime="text/plain"
                    )
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
