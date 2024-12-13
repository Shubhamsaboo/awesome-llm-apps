import streamlit as st
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.duckduckgo import DuckDuckGo
from google.generativeai import upload_file, get_file
import time
from pathlib import Path
import tempfile

st.set_page_config(
    page_title="Multimodal AI Agent",
    page_icon="🧬",
    layout="wide"
)

st.title("Multimodal AI Agent 🧬")

# Initialize single agent with both capabilities
@st.cache_resource
def initialize_agent():
    return Agent(
        name="Multimodal Analyst",
        model=Gemini(id="gemini-2.0-flash-exp"),
        tools=[DuckDuckGo()],
        markdown=True,
    )

agent = initialize_agent()

# File uploader
uploaded_file = st.file_uploader("Upload a video file", type=['mp4', 'mov', 'avi'])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
        tmp_file.write(uploaded_file.read())
        video_path = tmp_file.name
    
    st.video(video_path)
    
    user_prompt = st.text_area(
        "What would you like to know?",
        placeholder="Ask any question related to the video - the AI Agent will analyze it and search the web if needed",
        help="You can ask questions about the video content and get relevant information from the web"
    )
    
    if st.button("Analyze & Research"):
        if not user_prompt:
            st.warning("Please enter your question.")
        else:
            try:
                with st.spinner("Processing video and researching..."):
                    video_file = upload_file(video_path)
                    while video_file.state.name == "PROCESSING":
                        time.sleep(2)
                        video_file = get_file(video_file.name)

                    prompt = f"""
                    First analyze this video and then answer the following question using both 
                    the video analysis and web research: {user_prompt}
                    
                    Provide a comprehensive response focusing on practical, actionable information.
                    """
                    
                    result = agent.run(prompt, videos=[video_file])
                    
                st.subheader("Result")
                st.markdown(result.content)

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
            finally:
                Path(video_path).unlink(missing_ok=True)
else:
    st.info("Please upload a video to begin analysis.")

st.markdown("""
    <style>
    .stTextArea textarea {
        height: 100px;
    }
    </style>
    """, unsafe_allow_html=True)