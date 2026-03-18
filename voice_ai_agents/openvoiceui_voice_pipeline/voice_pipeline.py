"""
OpenVoiceUI Voice Pipeline — Full STT → LLM → TTS Voice AI Agent

This tutorial demonstrates the core voice AI loop used in OpenVoiceUI:
  1. STT  — Record audio in the browser and transcribe with OpenAI Whisper
  2. LLM  — Send the transcript to GPT-4o for a conversational response
  3. TTS  — Synthesize the response as audio and play it back

Run with:
    streamlit run voice_pipeline.py
"""

import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────
#  Page config
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="OpenVoiceUI Voice Pipeline",
    page_icon="🎙️",
    layout="centered",
)

# ─────────────────────────────────────────────────────────────
#  Session state defaults
# ─────────────────────────────────────────────────────────────

def init_session_state():
    defaults = {
        "messages": [],          # conversation history: [{role, content}]
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "voice": "alloy",
        "model": "gpt-4o",
        "system_prompt": (
            "You are a helpful voice AI assistant. "
            "Keep your responses concise and conversational — "
            "they will be read aloud, so avoid markdown formatting."
        ),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ─────────────────────────────────────────────────────────────
#  Sidebar — configuration
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("⚙️ Configuration")

    st.session_state.openai_api_key = st.text_input(
        "OpenAI API Key",
        value=st.session_state.openai_api_key,
        type="password",
        help="Required for Whisper (STT), GPT-4o (LLM), and TTS.",
    )

    st.divider()
    st.subheader("🎤 Voice Settings")

    st.session_state.voice = st.selectbox(
        "TTS Voice",
        ["alloy", "echo", "fable", "nova", "onyx", "shimmer"],
        index=["alloy", "echo", "fable", "nova", "onyx", "shimmer"].index(
            st.session_state.voice
        ),
    )

    st.session_state.model = st.selectbox(
        "LLM Model",
        ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        index=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"].index(st.session_state.model),
    )

    st.divider()
    st.subheader("🤖 Agent Persona")

    st.session_state.system_prompt = st.text_area(
        "System Prompt",
        value=st.session_state.system_prompt,
        height=120,
    )

    st.divider()
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ─────────────────────────────────────────────────────────────
#  Header
# ─────────────────────────────────────────────────────────────

st.title("🎙️ OpenVoiceUI Voice Pipeline")
st.markdown(
    "A full **STT → LLM → TTS** voice conversation loop. "
    "Record your voice, get an AI response, hear it spoken back."
)
st.divider()

# Guard: require API key before anything else
if not st.session_state.openai_api_key:
    st.warning("👈 Enter your OpenAI API key in the sidebar to get started.")
    st.stop()

client = OpenAI(api_key=st.session_state.openai_api_key)

# ─────────────────────────────────────────────────────────────
#  Conversation history display
# ─────────────────────────────────────────────────────────────

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "audio" in msg:
            st.audio(msg["audio"], format="audio/mp3")

# ─────────────────────────────────────────────────────────────
#  Step 1 — STT: record and transcribe
# ─────────────────────────────────────────────────────────────

st.subheader("🎤 Step 1 — Record Your Message")
audio_input = st.audio_input("Click the mic icon to record, then click stop when done.")

if audio_input:
    with st.spinner("🔄 Transcribing with Whisper…"):
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=("recording.wav", audio_input.getvalue(), "audio/wav"),
        )
        user_text = transcript.text.strip()

    if not user_text:
        st.warning("No speech detected — please try again.")
        st.stop()

    st.success(f"**You said:** {user_text}")
    st.session_state.messages.append({"role": "user", "content": user_text})

    # ─────────────────────────────────────────────────────────
    #  Step 2 — LLM: generate a response
    # ─────────────────────────────────────────────────────────

    with st.spinner("🧠 Step 2 — Thinking…"):
        api_messages = [{"role": "system", "content": st.session_state.system_prompt}]
        api_messages += [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]

        completion = client.chat.completions.create(
            model=st.session_state.model,
            messages=api_messages,
        )
        assistant_text = completion.choices[0].message.content

    # ─────────────────────────────────────────────────────────
    #  Step 3 — TTS: synthesize the response
    # ─────────────────────────────────────────────────────────

    with st.spinner("🔊 Step 3 — Generating speech…"):
        tts_response = client.audio.speech.create(
            model="tts-1",
            voice=st.session_state.voice,
            input=assistant_text,
        )
        audio_bytes = tts_response.content

    # Display the assistant turn
    with st.chat_message("assistant"):
        st.write(assistant_text)
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)

    st.session_state.messages.append(
        {"role": "assistant", "content": assistant_text, "audio": audio_bytes}
    )

    st.rerun()
