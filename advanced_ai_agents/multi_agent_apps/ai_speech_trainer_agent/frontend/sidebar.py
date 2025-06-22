# Sidebar with About section
import streamlit as st

def render_sidebar():
    st.sidebar.header("About")
    st.sidebar.info(
        """
        **AI Speech Trainer** helps users improve their public speaking skills through:\
        
        
        📽️ Video Analysis\
        
        🗣️ Voice Analysis\
                
        📊 Content Analysis & Feedback\
        

        - Upload your video to receive a detailed feedback.

        - Improve your public speaking skills with AI-powered analysis.
        
        - Get personalized suggestions to enhance your performance.
        """
    ) 