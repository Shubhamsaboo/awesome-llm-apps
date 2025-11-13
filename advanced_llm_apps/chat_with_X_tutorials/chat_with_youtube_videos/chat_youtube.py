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
        
        # Create API instance (required for new version)
        api = YouTubeTranscriptApi()
        
        # First, check if transcripts are available
        try:
            transcript_list = api.list(video_id)
            available_languages = [t.language_code for t in transcript_list]
            st.info(f"Available transcripts: {available_languages}")
        except Exception as list_error:
            st.error(f"Cannot retrieve transcript list: {list_error}")
            return "Unknown", "No transcript available for this video."
        
        # Try to get transcript with multiple fallback languages
        languages_to_try = ['en', 'en-US', 'en-GB']  # Try English variants first
        transcript = None
        
        for lang in languages_to_try:
            if lang in available_languages:
                try:
                    fetched_transcript = api.fetch(video_id, languages=[lang])
                    transcript = list(fetched_transcript)  # Convert to list of snippets
                    st.success(f"Successfully fetched transcript in language: {lang}")
                    break
                except Exception:
                    continue
        
        # If no English transcript, try any available language
        if transcript is None and available_languages:
            try:
                fetched_transcript = api.fetch(video_id, languages=[available_languages[0]])
                transcript = list(fetched_transcript)
                st.success(f"Successfully fetched transcript in language: {available_languages[0]}")
            except Exception as final_error:
                st.error(f"Could not fetch transcript in any language: {final_error}")
                return "Unknown", "No transcript available for this video."
        
        if transcript:
            # Extract text from FetchedTranscriptSnippet objects
            transcript_text = " ".join([snippet.text for snippet in transcript])
            return "Unknown", transcript_text  # Title is set to "Unknown" since we're not fetching it
        else:
            return "Unknown", "No transcript available for this video."
        
    except ValueError as ve:
        st.error(f"Invalid YouTube URL: {ve}")
        return "Unknown", "Invalid YouTube URL provided."
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        if "VideoUnavailable" in error_type:
            st.error("❌ Video is unavailable, private, or has been removed.")
        elif "TranscriptsDisabled" in error_type:
            st.error("❌ Subtitles/transcripts are disabled for this video.")
            st.info("💡 Try a different video that has subtitles enabled.")
        elif "NoTranscriptFound" in error_type:
            st.error("❌ No transcript found in the requested language.")
            st.info("💡 Try a video with auto-generated subtitles or manual captions.")
        elif "ParseError" in error_type:
            st.error("❌ Unable to parse video data. This might be due to:")
            st.info("• Video is private or restricted")
            st.info("• Video has been removed")
            st.info("• YouTube changed their format")
            st.info("💡 Try a different video.")
        else:
            st.error(f"❌ Error fetching transcript ({error_type}): {error_msg}")
            
        return "Unknown", "No transcript available for this video."

# Create Streamlit app
st.title("Chat with YouTube Video 📺")
st.caption("This app allows you to chat with a YouTube video using OpenAI API")

# Add helpful instructions
with st.expander("ℹ️ How to use this app", expanded=False):
    st.markdown("""
    1. **Enter your OpenAI API key** (required for AI responses)
    2. **Paste a YouTube video URL** (must have subtitles/transcripts available)
    3. **Wait for the transcript to load** (you'll see confirmation messages)
    4. **Ask questions** about the video content
    
    **📝 Note:** This app only works with videos that have:
    - Auto-generated subtitles, OR
    - Manually uploaded captions/transcripts
    
    **❌ Common issues:**
    - "Transcripts disabled" = Video doesn't have subtitles
    - "Video unavailable" = Video might be private, restricted, or removed
    - Try popular educational videos (TED talks, tutorials, etc.) for best results
    """)

with st.expander("🎯 Try these working example videos", expanded=False):
    example_videos = [
        "https://www.youtube.com/watch?v=9bZkp7q19f0",  # Short working video
        "https://www.youtube.com/watch?v=UF8uR6Z6KLc",  # Simon Sinek TED Talk
        "https://www.youtube.com/watch?v=_uQrJ0TkZlc",  # Programming tutorial
    ]
    
    st.markdown("**Working test videos (copy and paste these URLs):**")
    for i, video in enumerate(example_videos, 1):
        st.code(video, language=None)
    
    st.info("💡 These videos are confirmed to have accessible transcripts.")

st.divider()

# Initialize session state variables
if 'app' not in st.session_state:
    st.session_state.app = None
if 'current_video_url' not in st.session_state:
    st.session_state.current_video_url = None
if 'transcript_loaded' not in st.session_state:
    st.session_state.transcript_loaded = False
if 'transcript_text' not in st.session_state:
    st.session_state.transcript_text = None
if 'word_count' not in st.session_state:
    st.session_state.word_count = 0
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Get OpenAI API key from user
openai_access_token = st.text_input("OpenAI API Key", type="password")

# If OpenAI API key is provided, create an instance of App
if openai_access_token:
    # Create/update the embedchain app only if needed
    if st.session_state.app is None:
        # Create a temporary directory to store the database
        db_path = tempfile.mkdtemp()
        # Create an instance of Embedchain App
        st.session_state.app = embedchain_bot(db_path, openai_access_token)
    
    # Get the YouTube video URL from the user
    video_url = st.text_input("Enter YouTube Video URL", type="default")
    
    # Check if we have a new video URL or no transcript loaded yet
    if video_url and (video_url != st.session_state.current_video_url or not st.session_state.transcript_loaded):
        with st.spinner("🔍 Checking video and fetching transcript..."):
            try:
                title, transcript = fetch_video_data(video_url)
                if transcript != "No transcript available for this video." and transcript != "Invalid YouTube URL provided.":
                    with st.spinner("🧠 Adding to knowledge base..."):
                        # Clear previous video data if it exists
                        if st.session_state.transcript_loaded:
                            # Create a new app instance for the new video
                            db_path = tempfile.mkdtemp()
                            st.session_state.app = embedchain_bot(db_path, openai_access_token)
                            # Clear chat history for new video
                            st.session_state.chat_history = []
                        
                        st.session_state.app.add(transcript, data_type="text", metadata={"title": title, "url": video_url})
                        
                        # Store in session state
                        st.session_state.current_video_url = video_url
                        st.session_state.transcript_loaded = True
                        st.session_state.transcript_text = transcript
                        st.session_state.word_count = len(transcript.split())
                        
                        st.success(f"✅ Added video to knowledge base! You can now ask questions about it.")
                        st.info(f"📊 Transcript contains {st.session_state.word_count} words")
                else:
                    st.warning(f"❌ Cannot add video to knowledge base: {transcript}")
                    st.session_state.transcript_loaded = False
                    st.session_state.current_video_url = None
            except Exception as e:
                st.error(f"❌ Error processing video: {e}")
                st.session_state.transcript_loaded = False
                st.session_state.current_video_url = None
    
    # Show current video status
    if st.session_state.transcript_loaded and st.session_state.current_video_url:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"📹 Current video: {st.session_state.current_video_url}")
            st.info(f"📊 Transcript: {st.session_state.word_count} words loaded in memory")
        with col2:
            if st.button("🗑️ Clear Video", help="Remove current video and load a new one"):
                st.session_state.transcript_loaded = False
                st.session_state.current_video_url = None
                st.session_state.transcript_text = None
                st.session_state.word_count = 0
                st.session_state.app = None
                st.session_state.chat_history = []
                st.rerun()
        
        # Display chat history
        if st.session_state.chat_history:
            with st.expander("💬 Chat History", expanded=True):
                for i, (question, answer) in enumerate(st.session_state.chat_history):
                    st.markdown(f"**Q{i+1}:** {question}")
                    st.markdown(f"**A{i+1}:** {answer}")
                    st.divider()
        
    # Ask a question about the video
    prompt = st.text_input("Ask any question about the YouTube Video")
    
    # Chat with the video
    if prompt:
        if st.session_state.transcript_loaded and st.session_state.app:
            try:
                with st.spinner("🤔 Thinking..."):
                    answer = st.session_state.app.chat(prompt)
                    
                    # Add to chat history
                    st.session_state.chat_history.append((prompt, answer))
                    
                    # Display the current answer
                    st.write("**Answer:**")
                    st.write(answer)
                    
                    # Clear the input by refreshing (optional)
                    # st.rerun()
            except Exception as e:
                st.error(f"❌ Error chatting with the video: {e}")
        else:
            st.warning("⚠️ Please add a valid video with transcripts first before asking questions.")