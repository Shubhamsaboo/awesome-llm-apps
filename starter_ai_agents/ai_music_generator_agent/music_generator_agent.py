import os
from uuid import uuid4

import requests
from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIChat
from agno.tools.models_labs import FileType, ModelsLabTools
from agno.utils.log import logger
import streamlit as st

# Sidebar: User enters the API keys
st.sidebar.title("API Key Configuration")

openai_api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")
models_lab_api_key = st.sidebar.text_input("Enter your ModelsLab API Key", type="password")

# Streamlit App UI
st.title("🎶 ModelsLab Music Generator")
prompt = st.text_area("Enter a music generation prompt:", "Generate a 30 second classical music piece", height=100)

# Initialize agent only if both API keys are provided
if openai_api_key and models_lab_api_key:
    agent = Agent(
        name="ModelsLab Music Agent",
        agent_id="ml_music_agent",
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),  # Pass OpenAI API key here
        show_tool_calls=True,
        tools=[ModelsLabTools(api_key=models_lab_api_key, wait_for_completion=True, file_type=FileType.MP3)],  # Pass ModelsLab API key here
        description="You are an AI agent that can generate music using the ModelsLabs API.",
        instructions=[
            "When generating music, use the `generate_media` tool with detailed prompts that specify:",
            "- The genre and style of music (e.g., classical, jazz, electronic)",
            "- The instruments and sounds to include",
            "- The tempo, mood and emotional qualities",
            "- The structure (intro, verses, chorus, bridge, etc.)",
            "Create rich, descriptive prompts that capture the desired musical elements.",
            "Focus on generating high-quality, complete instrumental pieces.",
        ],
        markdown=True,
        debug_mode=True,
    )

    # Disable the button if either API key is missing
    disable_button = not openai_api_key or not models_lab_api_key

    if st.button("Generate Music", disabled=disable_button):
        if prompt.strip() == "":
            st.warning("Please enter a prompt first.")
        else:
            with st.spinner("Generating music... 🎵"):
                try:
                    music: RunResponse = agent.run(prompt)

                    if music.audio and len(music.audio) > 0:
                        save_dir = "audio_generations"
                        os.makedirs(save_dir, exist_ok=True)

                        # Download the generated audio
                        url = music.audio[0].url
                        response = requests.get(url)
                        filename = f"{save_dir}/music_{uuid4()}.mp3"
                        with open(filename, "wb") as f:
                            f.write(response.content)

                        # Streamlit audio player
                        st.success("Music generated successfully! 🎶")
                        audio_bytes = open(filename, "rb").read()
                        st.audio(audio_bytes, format="audio/mp3")

                        # Optional download button
                        st.download_button(
                            label="Download Music",
                            data=audio_bytes,
                            file_name="generated_music.mp3",
                            mime="audio/mp3"
                        )
                    else:
                        st.error("No audio generated. Please try again.")

                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    logger.error(f"Streamlit app error: {e}")
else:
    # Show warning if keys are not entered
    st.sidebar.warning("Please enter both the OpenAI and ModelsLab API keys to use the app.")
