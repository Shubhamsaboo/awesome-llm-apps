from agno.agent import Agent
from agno.models.google import Gemini
from agno.media import Image as AgnoImage
from agno.tools.duckduckgo import DuckDuckGoTools
import streamlit as st
from typing import List, Optional
import logging
from pathlib import Path
import tempfile
import os

# Configure logging for errors only
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def initialize_agents(api_key: str) -> tuple[Agent, Agent, Agent]:
    try:
        model = Gemini(id="gemini-2.0-flash-exp", api_key=api_key)
        
        vision_agent = Agent(
            model=model,
            instructions=[
                "You are a visual analysis expert that:",
                "1. Identifies design elements, patterns, and visual hierarchy",
                "2. Analyzes color schemes, typography, and layouts",
                "3. Detects UI components and their relationships",
                "4. Evaluates visual consistency and branding",
                "Be specific and technical in your analysis"
            ],
            markdown=True
        )

        ux_agent = Agent(
            model=model,
            instructions=[
                "You are a UX analysis expert that:",
                "1. Evaluates user flows and interaction patterns",
                "2. Identifies usability issues and opportunities",
                "3. Suggests UX improvements based on best practices",
                "4. Analyzes accessibility and inclusive design",
                "Focus on user-centric insights and practical improvements"
            ],
            markdown=True
        )

        market_agent = Agent(
            model=model,
            tools=[DuckDuckGoTools()],
            instructions=[
                "You are a market research expert that:",
                "1. Identifies market trends and competitor patterns",
                "2. Analyzes similar products and features",
                "3. Suggests market positioning and opportunities",
                "4. Provides industry-specific insights",
                "Focus on actionable market intelligence"
            ],
            markdown=True
        )
        
        return vision_agent, ux_agent, market_agent
    except Exception as e:
        st.error(f"Error initializing agents: {str(e)}")
        return None, None, None

# Set page config and UI elements
st.set_page_config(page_title="Multimodal AI Design Agent Team", layout="wide")

# Sidebar for API key input
with st.sidebar:
    st.header("🔑 API Configuration")

    if "api_key_input" not in st.session_state:
        st.session_state.api_key_input = ""
        
    api_key = st.text_input(
        "Enter your Gemini API Key",
        value=st.session_state.api_key_input,
        type="password",
        help="Get your API key from Google AI Studio",
        key="api_key_widget"  
    )

    if api_key != st.session_state.api_key_input:
        st.session_state.api_key_input = api_key
    
    if api_key:
        st.success("API Key provided! ✅")
    else:
        st.warning("Please enter your API key to proceed")
        st.markdown("""
        To get your API key:
        1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
        2. Enable the Generative Language API in your [Google Cloud Console](https://console.developers.google.com/apis/api/generativelanguage.googleapis.com)
        """)

st.title("Multimodal AI Design Agent Team")

if st.session_state.api_key_input:
    vision_agent, ux_agent, market_agent = initialize_agents(st.session_state.api_key_input)
    
    if all([vision_agent, ux_agent, market_agent]):
        # File Upload Section
        st.header("📤 Upload Content")
        col1, space, col2 = st.columns([1, 0.1, 1])
        
        with col1:
            design_files = st.file_uploader(
                "Upload UI/UX Designs",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key="designs"
            )
            
            if design_files:
                for file in design_files:
                    st.image(file, caption=file.name, use_container_width=True)

        with col2:
            competitor_files = st.file_uploader(
                "Upload Competitor Designs (Optional)",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key="competitors"
            )
            
            if competitor_files:
                for file in competitor_files:
                    st.image(file, caption=f"Competitor: {file.name}", use_container_width=True)

        # Analysis Configuration
        st.header("🎯 Analysis Configuration")

        analysis_types = st.multiselect(
            "Select Analysis Types",
            ["Visual Design", "User Experience", "Market Analysis"],
            default=["Visual Design"]
        )

        specific_elements = st.multiselect(
            "Focus Areas",
            ["Color Scheme", "Typography", "Layout", "Navigation", 
             "Interactions", "Accessibility", "Branding", "Market Fit"]
        )

        context = st.text_area(
            "Additional Context",
            placeholder="Describe your product, target audience, or specific concerns..."
        )

        # Analysis Process
        if st.button("🚀 Run Analysis", type="primary"):
            if design_files:
                try:
                    st.header("📊 Analysis Results")
                    
                    def process_images(files):
                        processed_images = []
                        for file in files:
                            try:
                                temp_dir = tempfile.gettempdir()
                                temp_path = os.path.join(temp_dir, f"temp_{file.name}")
                                
                                with open(temp_path, "wb") as f:
                                    f.write(file.getvalue())
                                
                                agno_image = AgnoImage(filepath=Path(temp_path))
                                processed_images.append(agno_image)
                                
                            except Exception as e:
                                logger.error(f"Error processing image {file.name}: {str(e)}")
                                continue
                        return processed_images
                    
                    design_images = process_images(design_files)
                    competitor_images = process_images(competitor_files) if competitor_files else []
                    all_images = design_images + competitor_images
                    
                    # Visual Design Analysis
                    if "Visual Design" in analysis_types and design_files:
                        with st.spinner("🎨 Analyzing visual design..."):
                            if all_images:
                                vision_prompt = f"""
                                Analyze these designs focusing on: {', '.join(specific_elements)}
                                Additional context: {context}
                                Provide specific insights about visual design elements.
                                
                                Please format your response with clear headers and bullet points.
                                Focus on concrete observations and actionable insights.
                                """
                                
                                response = vision_agent.run(
                                    message=vision_prompt,
                                    images=all_images
                                )
                                
                                st.subheader("🎨 Visual Design Analysis")
                                st.markdown(response.content)
                    
                    # UX Analysis
                    if "User Experience" in analysis_types:
                        with st.spinner("🔄 Analyzing user experience..."):
                            if all_images:
                                ux_prompt = f"""
                                Evaluate the user experience considering: {', '.join(specific_elements)}
                                Additional context: {context}
                                Focus on user flows, interactions, and accessibility.
                                
                                Please format your response with clear headers and bullet points.
                                Focus on concrete observations and actionable improvements.
                                """
                                
                                response = ux_agent.run(
                                    message=ux_prompt,
                                    images=all_images
                                )
                                
                                st.subheader("🔄 UX Analysis")
                                st.markdown(response.content)
                    
                    # Market Analysis
                    if "Market Analysis" in analysis_types:
                        with st.spinner("📊 Conducting market analysis..."):
                            market_prompt = f"""
                            Analyze market positioning and trends based on these designs.
                            Context: {context}
                            Compare with competitor designs if provided.
                            Suggest market opportunities and positioning.
                            
                            Please format your response with clear headers and bullet points.
                            Focus on concrete market insights and actionable recommendations.
                            """
                            
                            response = market_agent.run(
                                message=market_prompt,
                                images=all_images
                            )
                            
                            st.subheader("📊 Market Analysis")
                            st.markdown(response.content)
                            
                except Exception as e:
                    logger.error(f"Error during analysis: {str(e)}")
                    st.error("An error occurred during analysis. Please check the logs for details.")
            else:
                st.warning("Please upload at least one design to analyze.")
    else:
        st.info("👈 Please enter your API key in the sidebar to get started")
else:
    st.info("👈 Please enter your API key in the sidebar to get started")

# Footer with usage tips
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <h4>Tips for Best Results</h4>
    <p>
    • Upload clear, high-resolution images<br>
    • Include multiple views/screens for better context<br>
    • Add competitor designs for comparative analysis<br>
    • Provide specific context about your target audience
    </p>
</div>
""", unsafe_allow_html=True) 