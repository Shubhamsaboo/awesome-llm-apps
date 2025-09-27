import tempfile
import streamlit as st
from embedchain import App
from youtube_transcript_api import YouTubeTranscriptApi
from typing import Tuple

def embedchain_bot(db_path: str, api_key: str) -> App:
    return App.from_config(
        config={
            "llm": {"provider": "openai", "config": {"model": "gpt-4", "temperature": 0.5, "api_key": api_key}},
            "vectordb": {"provider": "chroma", "config": {"dir": db_path}},
            "embedder": {"provider": "openai", "config": {"api_key": api_key}},
        }
    )

def extract_video_id(video_url: str) -> str:
    if "youtube.com/watch?v=" in video_url:
        return video_url.split("v=")[-1].split("&")[0]
    elif "youtube.com/shorts/" in video_url:
        return video_url.split("/shorts/")[-1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube URL")

def fetch_video_data(video_url: str) -> Tuple[str, str]:
    try:
        video_id = extract_video_id(video_url)
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([entry["text"] for entry in transcript])
        return "Unknown", transcript_text  # Title is set to "Unknown" since we're not fetching it
    except Exception as e:
        st.error(f"Error fetching transcript: {e}")
        return "Unknown", "No transcript available for this video."

# Create Streamlit app
st.title("Chat with YouTube Video 📺")
st.caption("This app allows you to chat with a YouTube video using OpenAI API")

# Get OpenAI API key from user
openai_access_token = st.text_input("OpenAI API Key", type="password")

# If OpenAI API key is provided, create an instance of App
if openai_access_token:
    # Create a temporary directory to store the database
    db_path = tempfile.mkdtemp()
    # Create an instance of Embedchain App
    app = embedchain_bot(db_path, openai_access_token)
    # Get the YouTube video URL from the user
    video_url = st.text_input("Enter YouTube Video URL", type="default")
    # Add the video to the knowledge base
    if video_url:
        try:
            title, transcript = fetch_video_data(video_url)
            if transcript != "No transcript available for this video.":
                app.add(transcript, data_type="text", metadata={"title": title, "url": video_url})
                st.success(f"Added video '{title}' to knowledge base!")
            else:
                st.warning(f"No transcript available for video '{title}'. Cannot add to knowledge base.")
        except Exception as e:
            st.error(f"Error adding video: {e}")
        # Ask a question about the video
        prompt = st.text_input("Ask any question about the YouTube Video")
        # Chat with the video
        if prompt:
            try:
                answer = app.chat(prompt)
                st.write(answer)
            except Exception as e:
                st.error(f"Error chatting with the video: {e}")