import streamlit as st
import asyncio
from manager import TourManager
from agents import set_default_openai_key

def tts(text):
    from pathlib import Path
    from openai import OpenAI

    client = OpenAI()
    speech_file_path = Path(__file__).parent / f"speech_tour.mp3"
        
    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="coral",
        input=text,
        instructions="""Speak with different tones based on the content sections:
                - Use an inviting and warm tone for the Introduction.
                - Speak in an authoritative tone for History sections.
                - Use a positive and curious tone when discussing Architecture.
                - Use an enthusiastic and lively tone when covering Culture.
                - Use a joyful and passionate tone when talking about Culinary topics.
                Keep the transitions smooth and natural between sections."""
        )
    response.stream_to_file(speech_file_path)
    return speech_file_path

def run_async(func, *args, **kwargs):
    try:
        return asyncio.run(func(*args, **kwargs))
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(func(*args, **kwargs))
    
st.sidebar.title("🔑 API Settings")
api_key = st.sidebar.text_input("Enter your OpenAI API key:", type="password")

if api_key:
    st.session_state["OPENAI_API_KEY"] = api_key
    st.sidebar.success("API key saved!")

set_default_openai_key(api_key)

st.title("🏛️ Self-Guided Audio Tour Generator")


location = st.text_input("📍 Enter the location for your tour:")

interests = st.multiselect(
    "🎯 Select your interests:",
    options=["History", "Architecture", "Culinary", "Culture"]
)

duration = st.slider(
    "⏱️ Select the duration of the tour (in minutes):",
    min_value=5,
    max_value=60,
    value=30,
    step=5
)

if st.button("🎧 Generate Tour"):
    if "OPENAI_API_KEY" not in st.session_state:
        st.error("Please enter your OpenAI API key in the sidebar.")
    elif not location:
        st.error("Please enter a location.")
    elif not interests:
        st.error("Please select at least one interest.")
    else:
        with st.spinner(f"Generating a {duration}-minute tour in {location} focused on {', '.join(interests)}."):
            mgr = TourManager()
            final_tour = run_async(
                mgr.run, location, interests, duration
            )

            with st.expander("🎬 Tour"):
                st.markdown(final_tour)
         
        with st.spinner("Generating Audio"):
            tour_audio = tts(final_tour)
            st.audio(tour_audio, format="audio/mp3")
            
            