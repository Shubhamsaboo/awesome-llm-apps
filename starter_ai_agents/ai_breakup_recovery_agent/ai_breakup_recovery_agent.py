from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat
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

def initialize_agents(api_key: str) -> tuple[Team, Agent, Agent, Agent, Agent]:
    try:
        model = OpenAIChat(id="gpt-4o", api_key=api_key)

        therapist_agent = Agent(
            model=model,
            name="Therapist Agent",
            instructions=[
                "You are an empathetic therapist that:",
                "1. Listens with empathy and validates feelings",
                "2. Uses gentle humor to lighten the mood",
                "3. Shares relatable breakup experiences",
                "4. Offers comforting words and encouragement",
                "5. Analyzes both text and image inputs for emotional context",
                "Be supportive and understanding in your responses"
            ],
            markdown=True
        )

        closure_agent = Agent(
            model=model,
            name="Closure Agent",
            instructions=[
                "You are a closure specialist that:",
                "1. Creates emotional messages for unsent feelings",
                "2. Helps express raw, honest emotions",
                "3. Formats messages clearly with headers",
                "4. Ensures tone is heartfelt and authentic",
                "Focus on emotional release and closure"
            ],
            markdown=True
        )

        routine_planner_agent = Agent(
            model=model,
            name="Routine Planner Agent",
            instructions=[
                "You are a recovery routine planner that:",
                "1. Designs 7-day recovery challenges",
                "2. Includes fun activities and self-care tasks",
                "3. Suggests social media detox strategies",
                "4. Creates empowering playlists",
                "Focus on practical recovery steps"
            ],
            markdown=True
        )

        brutal_honesty_agent = Agent(
            model=model,
            name="Brutal Honesty Agent",
            tools=[DuckDuckGoTools()],
            instructions=[
                "You are a direct feedback specialist that:",
                "1. Gives raw, objective feedback about breakups",
                "2. Explains relationship failures clearly",
                "3. Uses blunt, factual language",
                "4. Provides reasons to move forward",
                "Focus on honest insights without sugar-coating"
            ],
            markdown=True
        )

        team_leader = Team(
            model=model,
            name="Relationship Recovery Coordinator",
            members=[therapist_agent, closure_agent, routine_planner_agent, brutal_honesty_agent],
            instructions=[
                "You are the Relationship Recovery Coordinator (Team Leader). Your job is to:",
                "1. Coordinate with your team of specialists: Therapist Agent, Closure Agent, Routine Planner Agent, and Brutal Honesty Agent.",
                "2. Delegate sub-tasks to these agents using the tools available to you to gather their individual analysis and contributions.",
                "3. Compile and synthesize their feedback into a single, cohesive, highly-structured recovery roadmap.",
                "4. Ensure the final response flows logically, starting with the therapist's emotional assessment, followed by the reality check, then the recovery routine, and ending with closure exercises.",
                "5. Maintain a supportive yet direct tone throughout the report."
            ],
            markdown=True
        )

        return team_leader, therapist_agent, closure_agent, routine_planner_agent, brutal_honesty_agent
    except Exception as e:
        st.error(f"Error initializing agents: {str(e)}")
        return None, None, None, None, None

# Set page config and UI elements
st.set_page_config(
    page_title="💔 Breakup Recovery Squad",
    page_icon="💔",
    layout="wide"
)



# Sidebar for API key input
with st.sidebar:
    st.header("🔑 API Configuration")

    if "api_key_input" not in st.session_state:
        st.session_state.api_key_input = os.environ.get("OPENAI_API_KEY", "")
        
    api_key = st.text_input(
        "Enter your OpenAI API Key",
        value=st.session_state.api_key_input,
        type="password",
        help="Get your API key from OpenAI Platform",
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
        1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
        2. Create a new secret API key
        """)

# Main content
st.title("💔 Breakup Recovery Squad")
st.markdown("""
    ### Your AI-powered breakup recovery team is here to help!
    Share your feelings and chat screenshots, and we'll help you navigate through this tough time.
""")

# Input section
col1, col2 = st.columns(2)

with col1:
    st.subheader("Share Your Feelings")
    user_input = st.text_area(
        "How are you feeling? What happened?",
        height=150,
        placeholder="Tell us your story..."
    )
    
with col2:
    st.subheader("Upload Chat Screenshots")
    uploaded_files = st.file_uploader(
        "Upload screenshots of your chats (optional)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key="screenshots"
    )
    
    if uploaded_files:
        for file in uploaded_files:
            st.image(file, caption=file.name, use_container_width=True)

# Process button and API key check
if st.button("Get Recovery Plan 💝", type="primary"):
    if not st.session_state.api_key_input:
        st.warning("Please enter your API key in the sidebar first!")
    else:
        team_leader, therapist_agent, closure_agent, routine_planner_agent, brutal_honesty_agent = initialize_agents(st.session_state.api_key_input)

        if all([team_leader, therapist_agent, closure_agent, routine_planner_agent, brutal_honesty_agent]):
            if user_input or uploaded_files:
                try:
                    st.header("Your Personalized Recovery Plan")
                    
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
                    
                    all_images = process_images(uploaded_files) if uploaded_files else []
                    
                    # Coordinated Team Leader Execution
                    with st.spinner("🤝 Coordinating with the Breakup Recovery Squad..."):
                        team_leader_prompt = f"""
                        Coordinate with your team of specialists to create a comprehensive, synthesized breakup recovery roadmap based on:
                        User situation: {user_input}

                        Please delegate to each specialist:
                        1. Ask the Therapist Agent to analyze the emotional state and provide empathetic support.
                        2. Ask the Brutal Honesty Agent to provide an objective, direct reality check on the situation.
                        3. Ask the Routine Planner Agent to design a tailored 7-day recovery calendar and self-care routine.
                        4. Ask the Closure Agent to write a template for unsent messages and release rituals.

                        Synthesize all their contributions into a single, cohesive, beautifully-structured report.
                        """

                        response = team_leader.run(
                            team_leader_prompt,
                            images=all_images
                        )

                        st.markdown(response.content)
                            
                except Exception as e:
                    logger.error(f"Error during analysis: {str(e)}")
                    st.error("An error occurred during analysis. Please check the logs for details.")
            else:
                st.warning("Please share your feelings or upload screenshots to get help.")
        else:
            st.error("Failed to initialize agents. Please check your API key.")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        <p>Made with ❤️ by the Breakup Recovery Squad</p>
        <p>Share your recovery journey with #BreakupRecoverySquad</p>
    </div>
""", unsafe_allow_html=True)