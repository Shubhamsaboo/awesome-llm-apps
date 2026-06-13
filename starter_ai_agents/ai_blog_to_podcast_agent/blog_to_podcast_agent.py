import os
from uuid import uuid4

from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.models.openai import OpenAIChat
import streamlit as st

from podcast_utils import (
    extract_text_from_html,
    fetch_url_with_curl,
    get_openai_api_key,
    synthesize_aiff_with_say,
)

# Streamlit Setup
st.set_page_config(page_title="📰 ➡️ 🎙️ Blog to Podcast", page_icon="🎙️")
st.title("📰 ➡️ 🎙️ Blog to Podcast Agent")

# API Keys (Runtime Input)
st.sidebar.header("🔑 API Keys")
openai_key = get_openai_api_key()
if openai_key:
    st.sidebar.success("OpenAI API key loaded from Keychain")
else:
    openai_key = st.sidebar.text_input("OpenAI API Key", type="password")

# Blog URL Input
url = st.text_input("Enter Blog URL:", "")

# Generate Button
if st.button("🎙️ Generate Podcast", disabled=not openai_key):
    if not url.strip():
        st.warning("Please enter a blog URL")
    else:
        with st.spinner("Scraping blog and generating podcast..."):
            try:
                # Set API keys for the current process
                os.environ["OPENAI_API_KEY"] = openai_key

                html = fetch_url_with_curl(url)
                article_text = extract_text_from_html(html)

                if not article_text:
                    st.error("Failed to extract readable text from the blog")
                    st.stop()

                # Create agent for summarization
                agent = Agent(
                    name="Blog Summarizer",
                    model=OpenAIChat(id="gpt-4o"),
                    instructions=[
                        "Create a concise, engaging summary (max 2000 characters) suitable for a podcast.",
                        "The summary should be conversational and capture the main points.",
                        "Ignore any sign-in, join-now, or cookie boilerplate from the input content.",
                        "If the content is a social media post (like LinkedIn), focus on the core message and insights."
                    ],
                )
                
                # Get summary
                response: RunOutput = agent.run(
                    f"Summarize this blog text for a podcast:\n\n{article_text[:12000]}"
                )
                summary = response.content if hasattr(response, 'content') else str(response)
                
                if summary:
                    audio_path = f"/tmp/podcast-{uuid4()}.aiff"
                    synthesize_aiff_with_say(summary, audio_path)

                    with open(audio_path, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                    
                    # Display audio
                    st.success("Podcast generated! 🎧")
                    st.audio(audio_bytes, format="audio/aiff")
                    
                    # Download button
                    st.download_button(
                        "Download Podcast",
                        audio_bytes,
                        "podcast.aiff",
                        "audio/aiff"
                    )
                    
                    # Show summary
                    with st.expander("📄 Podcast Summary"):
                        st.write(summary)
                else:
                    st.error("Failed to generate summary")
                    
            except Exception as e:
                st.error(f"Error: {e}")
