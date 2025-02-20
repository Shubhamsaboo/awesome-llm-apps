from typing import Dict, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from firecrawl import FirecrawlApp
import streamlit as st
import asyncio

class AQIResponse(BaseModel):
    success: bool
    data: Dict[str, float]
    status: str
    expiresAt: str

class ExtractSchema(BaseModel):
    aqi: float = Field(description="Air Quality Index")
    temperature: float = Field(description="Temperature in degrees Celsius")
    humidity: float = Field(description="Humidity percentage")
    wind_speed: float = Field(description="Wind speed in kilometers per hour")
    pm25: float = Field(description="Particulate Matter 2.5 micrometers")
    pm10: float = Field(description="Particulate Matter 10 micrometers")
    co: float = Field(description="Carbon Monoxide level")

@dataclass
class UserInput:
    city: str
    state: str
    country: str
    medical_conditions: Optional[str]
    planned_activity: str

class AQIAnalyzer:
    
    def __init__(self, firecrawl_key: str) -> None:
        self.firecrawl = FirecrawlApp(api_key=firecrawl_key)
    
    def _format_url(self, country: str, state: str, city: str) -> str:
        return f"https://www.aqi.in/dashboard/{country.lower().replace(' ', '-')}/{state.lower().replace(' ', '-')}/{city.lower().replace(' ', '-')}"
    
    def fetch_aqi_data(self, city: str, state: str, country: str) -> Dict[str, float]:
        try:
            url = self._format_url(country, state, city)
            
            response = self.firecrawl.extract(
                urls=[f"{url}/*"],
                params={
                    'prompt': 'Extract the AQI, temperature, humidity, wind speed, PM2.5, PM10, and CO levels from the page.',
                    'schema': ExtractSchema.model_json_schema()
                }
            )
            
            aqi_response = AQIResponse(**response)
            if not aqi_response.success:
                raise ValueError(f"Failed to fetch AQI data: {aqi_response.status}")
                
            return aqi_response.data
            
        except Exception as e:
            st.error(f"Error fetching AQI data: {str(e)}")
            return {
                'aqi': 0,
                'temperature': 0,
                'humidity': 0,
                'wind_speed': 0,
                'pm25': 0,
                'pm10': 0,
                'co': 0
            }

class HealthRecommendationAgent:
    
    def __init__(self, openai_key: str) -> None:
        self.agent = Agent(
            model=OpenAIChat(
                id="gpt-4o",
                name="Health Recommendation Agent",
                api_key=openai_key
            )
        )
    
    def get_recommendations(
        self,
        aqi_data: Dict[str, float],
        user_input: UserInput
    ) -> str:
        prompt = self._create_prompt(aqi_data, user_input)
        response = self.agent.run(prompt)
        return response.content
    
    def _create_prompt(self, aqi_data: Dict[str, float], user_input: UserInput) -> str:
        return f"""
        Based on the following air quality conditions in {user_input.city}, {user_input.state}, {user_input.country}:
        - Overall AQI: {aqi_data['aqi']}
        - PM2.5 Level: {aqi_data['pm25']} µg/m³
        - PM10 Level: {aqi_data['pm10']} µg/m³
        - CO Level: {aqi_data['co']} ppb
        
        Weather conditions:
        - Temperature: {aqi_data['temperature']}°C
        - Humidity: {aqi_data['humidity']}%
        - Wind Speed: {aqi_data['wind_speed']} km/h
        
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

def analyze_conditions(
    user_input: UserInput,
    api_keys: Dict[str, str]
) -> str:
    aqi_analyzer = AQIAnalyzer(firecrawl_key=api_keys['firecrawl'])
    health_agent = HealthRecommendationAgent(openai_key=api_keys['openai'])
    
    aqi_data = aqi_analyzer.fetch_aqi_data(
        city=user_input.city,
        state=user_input.state,
        country=user_input.country
    )
    
    return health_agent.get_recommendations(aqi_data, user_input)

def initialize_session_state():
    if 'api_keys' not in st.session_state:
        st.session_state.api_keys = {
            'firecrawl': '',
            'openai': ''
        }

def setup_page():
    st.set_page_config(
        page_title="AQI Analysis Assistant",
        page_icon="🌍",
        layout="wide"
    )
    
    st.title("🌍 AQI Analysis Assistant")
    st.info("Get personalized health recommendations based on air quality conditions.")

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
        
        # Update session state only if both keys are provided
        if (new_firecrawl_key and new_openai_key and
            (new_firecrawl_key != st.session_state.api_keys['firecrawl'] or 
             new_openai_key != st.session_state.api_keys['openai'])):
            st.session_state.api_keys.update({
                'firecrawl': new_firecrawl_key,
                'openai': new_openai_key
            })
            st.success("✅ API keys updated!")

def render_main_content():
    st.header("📍 Location Details")
    col1, col2 = st.columns(2)
    
    with col1:
        city = st.text_input("City", placeholder="e.g., Mumbai")
        state = st.text_input("State", placeholder="e.g., Maharashtra")
        country = st.text_input("Country", value="India")
    
    with col2:
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
                    result = analyze_conditions(
                        user_input=user_input,
                        api_keys=st.session_state.api_keys
                    )
                    
                    st.success("✅ Analysis completed!")
                    st.markdown("### 📊 Recommendations")
                    st.info(result)
                    
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
