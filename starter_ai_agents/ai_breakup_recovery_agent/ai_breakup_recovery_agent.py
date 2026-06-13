from agno.agent import Agent
from agno.team import Team
from agno.models.anthropic import Claude
from agno.media import Image as AgnoImage
from agno.tools.duckduckgo import DuckDuckGoTools
import streamlit as st
from typing import List, Optional
import logging
from pathlib import Path
import tempfile
import os
import subprocess
from datetime import datetime

# Configure logging for errors only
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def get_zuora_jwt_token() -> str:
    """Get fresh JWT token from Zuora infrastructure."""
    token_file = os.path.expanduser("~/.claude/tokens/id_token.txt")

    try:
        if os.path.exists(token_file):
            mtime = os.path.getmtime(token_file)
            age = datetime.now().timestamp() - mtime
            if age < 86000:  # < 24 hours
                with open(token_file, "r") as f:
                    return f.read().strip()

        # Token missing or stale — refresh
        result = subprocess.run(
            [os.path.expanduser("~/.claude/scripts/get-current-token.sh")],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Token refresh failed: {result.stderr}")
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"Failed to get Zuora JWT token: {str(e)}")
        raise

def initialize_agents() -> tuple[Team, Agent, Agent, Agent, Agent]:
    try:
        jwt_token = get_zuora_jwt_token()

        model = Claude(
            id="aws-bedrock-claude-haiku-4-5",
            api_key=jwt_token,
            client_params={
                "base_url": "http://claude-proxy.tools.stg.uw2.aws.zuora",
                "default_headers": {
                    "Authorization": f"Bearer {jwt_token}",
                },
            },
        )

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



# Sidebar for Zuora Auth status
with st.sidebar:
    st.header("🔑 Zuora AI Infrastructure")

    try:
        jwt_token = get_zuora_jwt_token()
        token_age = datetime.now().timestamp() - os.path.getmtime(
            os.path.expanduser("~/.claude/tokens/id_token.txt")
        )
        hours_left = round((86400 - token_age) / 3600)
        st.success(f"✅ Authenticated (expires in {hours_left}h)")
    except Exception as e:
        st.error(f"❌ Auth failed: {str(e)}")
        st.markdown("""
        **Fix:**
        1. Ensure you're on Zuora VPN (Zscaler)
        2. Run: `~/.claude/scripts/get-current-token.sh`
        3. Verify token: `cat ~/.claude/tokens/id_token.txt`
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

# Process button
if st.button("Get Recovery Plan 💝", type="primary"):
    try:
        team_leader, therapist_agent, closure_agent, routine_planner_agent, brutal_honesty_agent = initialize_agents()

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
                    st.error(f"Analysis failed: {str(e)}")
            else:
                st.warning("Please share your feelings or upload screenshots to get help.")
        else:
            st.error("Failed to initialize agents. Check sidebar for auth status.")
    except Exception as e:
        logger.error(f"Initialization error: {str(e)}")
        st.error(f"Failed to initialize: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        <p>Made with ❤️ by the Breakup Recovery Squad</p>
        <p>Share your recovery journey with #BreakupRecoverySquad</p>
    </div>
""", unsafe_allow_html=True)