import streamlit as st
import requests
import tempfile
import os
import json
import numpy as np
from page_congif import render_page_config

render_page_config()

# Initialize session state variables
if "begin" not in st.session_state:
    st.session_state.begin = False

if "video_path" not in st.session_state:
    st.session_state.video_path = None

if "upload_file" not in st.session_state:
    st.session_state.upload_file = False

if "response" not in st.session_state:
    st.session_state.response = None

if "facial_expression_response" not in st.session_state:
    st.session_state.facial_expression_response = None

if "voice_analysis_response" not in st.session_state:
    st.session_state.voice_analysis_response = None

if "content_analysis_response" not in st.session_state:
    st.session_state.content_analysis_response = None

if "feedback_response" not in st.session_state:
    st.session_state.feedback_response = None


def clear_session_response():
    st.session_state.response = None
    st.session_state.facial_expression_response = None
    st.session_state.voice_analysis_response = None
    st.session_state.content_analysis_response = None
    st.session_state.feedback_response = None    


# Create two columns with a 70:30 width ratio
col1, col2 = st.columns([0.7, 0.3])

# Left column: Video area and buttons
with col1:
    spacer1, btn_col = st.columns([0.8, 0.2])

    if st.session_state.begin:
        with spacer1:
            st.markdown("<h4>📽️ Video</h4>", unsafe_allow_html=True)
        
        with btn_col:
            if st.button("📤 Upload Video"):
                if st.session_state.video_path:
                    os.remove(st.session_state.video_path)
                st.session_state.video_path = None
                clear_session_response()
                st.session_state.upload_file = True
                st.rerun()  # Force rerun to fully reset uploader

    
    if st.session_state.get("upload_file"):
        uploaded_file = st.file_uploader("📤 Upload Video", type=["mp4"])
        
        if uploaded_file is not None:
            temp_dir = tempfile.gettempdir()
            # Use a random name to avoid reuse
            unique_name = f"{int(np.random.rand()*1e8)}_{uploaded_file.name}"
            file_path = os.path.join(temp_dir, unique_name)
            
            if not os.path.exists(file_path):
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.read())

            st.session_state.video_path = file_path
            st.session_state.upload_file = False
            st.rerun()
    # elif not st.session_state.get("video_path"):
    if not st.session_state.begin:
        st.success("""
            **Welcome to AI Speech Trainer!**  
            Your ultimate companion to help improve your public speaking skills.
            """)        
        st.info("""
                🚀 To get started:
                \n\t1. Record a video of yourself practicing a speech or presentation - use any video recording app.
                \n\t2. Upload the recorded video.
                \n\t3. Analyze the video to get personalized feedback.
                """)
        if st.button("👉 Let's begin!"):
            st.session_state.begin = True
            st.rerun()

    if st.session_state.video_path:
        st.video(st.session_state.video_path, autoplay=False)
        
        if not st.session_state.response:
            if st.button("▶️ Analyze Video"):
                with st.spinner("Analyzing video..."):
                    st.warning("⚠️ This process may take some time, so please be patient and wait for the analysis to complete.")
                    API_URL = "http://localhost:8000/analyze"
                    response = requests.post(API_URL, json={"video_url": st.session_state.video_path})
                    
                    if response.status_code == 200:
                        st.success("Video analysis completed successfully.")
                        response = response.json()
                        st.session_state.response = response
                        st.session_state.facial_expression_response = response.get("facial_expression_response")
                        st.session_state.voice_analysis_response = response.get("voice_analysis_response")
                        st.session_state.content_analysis_response = response.get("content_analysis_response")
                        st.session_state.feedback_response = response.get("feedback_response")
                        st.rerun()
                    else:   
                        st.error("🚨 Error during video analysis. Please try again.")

# Right column: Transcript and feedback
with col2:
    st.markdown("<h4>📝 Transcript</h4>", unsafe_allow_html=True)
    transcript_text = "Your transcript will be displayed here."
    if st.session_state.response:
        voice_analysis_response = st.session_state.voice_analysis_response
        transcript = json.loads(voice_analysis_response).get("transcription")
    else:
        transcript = None

    st.markdown(
        f"""
        <div style="background-color:#f0f2f6; padding: 1.5rem; border-radius: 10px;
                    border: 1px solid #ccc; font-family: 'Segoe UI', sans-serif;
                    line-height: 1.6; color: #333; height: 400px; max-height: 400px; overflow-y: auto;">
            {transcript if transcript else transcript_text}
        </div>
        <br>
        """,
        unsafe_allow_html=True
    )

    if st.button("📝 Get Feedback"):
        st.switch_page("pages/1 - Feedback.py")