from agno.agent import Agent
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
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging for errors only
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Environment Configuration (required, no defaults)
MY_LLM_MODEL = os.getenv("MY_LLM_MODEL")
MY_LLM_ENDPOINT = os.getenv("MY_LLM_ENDPOINT")
MY_TOKEN_FILE = os.getenv("MY_TOKEN_FILE")
MY_TOKEN_REFRESH_SCRIPT = os.getenv("MY_TOKEN_REFRESH_SCRIPT")

# Validate required env vars
_missing_vars = [
    var for var, val in [
        ("MY_LLM_MODEL", MY_LLM_MODEL),
        ("MY_LLM_ENDPOINT", MY_LLM_ENDPOINT),
        ("MY_TOKEN_FILE", MY_TOKEN_FILE),
        ("MY_TOKEN_REFRESH_SCRIPT", MY_TOKEN_REFRESH_SCRIPT),
    ] if not val
]

if _missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(_missing_vars)}")

# Expand user paths
MY_TOKEN_FILE = os.path.expanduser(MY_TOKEN_FILE)
MY_TOKEN_REFRESH_SCRIPT = os.path.expanduser(MY_TOKEN_REFRESH_SCRIPT)

async def get_recovery_roadmap(
    coordinator_agent: Agent,
    therapist_agent: Agent,
    closure_agent: Agent,
    routine_planner_agent: Agent,
    brutal_honesty_agent: Agent,
    user_input: str,
    images: List = None,
) -> str:
    """Run 4 sub-agents in parallel, then synthesize with coordinator."""
    if images is None:
        images = []

    payload = user_input

    # 1. Run all 4 sub-agents CONCURRENTLY using asyncio
    try:
        tasks = [
            therapist_agent.arun(payload, images=images),
            closure_agent.arun(payload, images=images),
            routine_planner_agent.arun(payload, images=images),
            brutal_honesty_agent.arun(payload, images=images),
        ]
        results = await asyncio.gather(*tasks)
    except Exception as e:
        logger.error(f"Sub-agent execution failed: {str(e)}")
        raise

    # 2. Format sub-agent outputs as context for coordinator
    sub_agent_context = f"""
Based on the user situation: {user_input}

EMOTIONAL SUPPORT (Therapist):
{results[0].content}

CLOSURE EXERCISES (Closure Specialist):
{results[1].content}

RECOVERY ROUTINE (Routine Planner):
{results[2].content}

REALITY CHECK (Brutal Honesty):
{results[3].content}

---
Now synthesize the above into a single, cohesive recovery roadmap.
"""

    # 3. Run coordinator to synthesize (final ~2s)
    try:
        final_response = await coordinator_agent.arun(sub_agent_context, images=images)
        return final_response.content
    except Exception as e:
        logger.error(f"Coordinator synthesis failed: {str(e)}")
        raise

def get_jwt_token() -> str:
    """Get fresh JWT token from configured infrastructure."""
    try:
        if os.path.exists(MY_TOKEN_FILE):
            mtime = os.path.getmtime(MY_TOKEN_FILE)
            age = datetime.now().timestamp() - mtime
            if age < 86000:  # < 24 hours
                with open(MY_TOKEN_FILE, "r") as f:
                    return f.read().strip()

        # Token missing or stale — refresh
        result = subprocess.run(
            [MY_TOKEN_REFRESH_SCRIPT],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Token refresh failed: {result.stderr}")
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"Failed to get JWT token: {str(e)}")
        raise

def initialize_agents() -> tuple[Agent, Agent, Agent, Agent, Agent]:
    """Initialize 5 standalone agents for parallel execution."""
    try:
        jwt_token = get_jwt_token()

        model = Claude(
            id=MY_LLM_MODEL,
            api_key=jwt_token,
            client_params={
                "base_url": MY_LLM_ENDPOINT,
                "default_headers": {
                    "Authorization": f"Bearer {jwt_token}",
                },
            },
        )

        # 4 Sub-agents (run in parallel)
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

        # Coordinator (synthesizes sub-agent outputs)
        coordinator_agent = Agent(
            model=model,
            name="Relationship Recovery Coordinator",
            instructions=[
                "You are the final synthesis specialist. Your job is to:",
                "1. Read the 4 specialist responses provided to you below.",
                "2. Synthesize them into a single, cohesive, beautifully-structured recovery roadmap.",
                "3. Do NOT list out individual agent outputs; instead, speak with one unified voice.",
                "4. Flow logically: start with emotional assessment, reality check, recovery routine, then closure exercises.",
                "5. Maintain supportive yet direct tone throughout."
            ],
            markdown=True
        )

        return coordinator_agent, therapist_agent, closure_agent, routine_planner_agent, brutal_honesty_agent
    except Exception as e:
        st.error(f"Error initializing agents: {str(e)}")
        return None, None, None, None, None

# Set page config and UI elements
st.set_page_config(
    page_title="💔 Breakup Recovery Squad",
    page_icon="💔",
    layout="wide"
)



# Sidebar for Auth status
with st.sidebar:
    st.header("🔑 AI Infrastructure")

    try:
        jwt_token = get_jwt_token()
        token_age = datetime.now().timestamp() - os.path.getmtime(MY_TOKEN_FILE)
        hours_left = round((86400 - token_age) / 3600)
        st.success(f"✅ Authenticated (expires in {hours_left}h)")
    except Exception as e:
        st.error(f"❌ Auth failed: {str(e)}")
        st.markdown(f"""
        **Fix:**
        1. Verify environment variables:
           - MY_LLM_MODEL
           - MY_LLM_ENDPOINT
           - MY_TOKEN_FILE
           - MY_TOKEN_REFRESH_SCRIPT
        2. Run token refresh script: `{MY_TOKEN_REFRESH_SCRIPT}`
        3. Verify token exists: `cat {MY_TOKEN_FILE}`
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
        coordinator_agent, therapist_agent, closure_agent, routine_planner_agent, brutal_honesty_agent = initialize_agents()

        if all([coordinator_agent, therapist_agent, closure_agent, routine_planner_agent, brutal_honesty_agent]):
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

                    # Parallel Sub-Agent Execution
                    with st.spinner("🤝 Running Breakup Recovery Squad in parallel..."):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                        roadmap = loop.run_until_complete(
                            get_recovery_roadmap(
                                coordinator_agent=coordinator_agent,
                                therapist_agent=therapist_agent,
                                closure_agent=closure_agent,
                                routine_planner_agent=routine_planner_agent,
                                brutal_honesty_agent=brutal_honesty_agent,
                                user_input=user_input,
                                images=all_images,
                            )
                        )

                        st.markdown(roadmap)

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