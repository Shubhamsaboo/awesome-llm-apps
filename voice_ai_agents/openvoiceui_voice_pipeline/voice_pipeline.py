"""
OpenVoiceUI Voice Pipeline — Full STT → LLM → TTS Voice AI Agent

Pipeline:
  1. STT  — Record audio in the browser, transcribe with OpenAI Whisper
  2. LLM  — openai-agents VoiceAssistant answers (with WebSearchTool for live data)
  3. TTS  — TTSDirector writes delivery instructions, gpt-4o-mini-tts synthesizes speech

Run with:
    streamlit run voice_pipeline.py
"""

import os
import asyncio
import streamlit as st
from openai import OpenAI
from agents import Runner, set_default_openai_key
from dotenv import load_dotenv

from pipeline_agents import voice_assistant_agent, tts_director_agent, AssistantResponse

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
        "messages": [],
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "voice": "nova",
        "tts_model": "gpt-4o-mini-tts",
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
        help="Used for Whisper (STT), the agent pipeline (LLM), and TTS.",
    )

    st.divider()
    st.subheader("🔊 Voice Settings")

    voices = ["alloy", "echo", "fable", "nova", "onyx", "shimmer"]
    st.session_state.voice = st.selectbox(
        "TTS Voice",
        voices,
        index=voices.index(st.session_state.voice),
    )

    tts_models = ["gpt-4o-mini-tts", "tts-1", "tts-1-hd"]
    st.session_state.tts_model = st.selectbox(
        "TTS Model",
        tts_models,
        index=tts_models.index(st.session_state.tts_model),
        help="gpt-4o-mini-tts supports delivery instructions for more expressive speech.",
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
    "**STT → LLM Agent → TTS** — speak a question, get an intelligent spoken response. "
    "The agent uses web search automatically for real-time questions."
)
st.divider()

if not st.session_state.openai_api_key:
    st.warning("👈 Enter your OpenAI API key in the sidebar to get started.")
    st.stop()

# Register the API key with the agents SDK and the raw OpenAI client
set_default_openai_key(st.session_state.openai_api_key)
oai_client = OpenAI(api_key=st.session_state.openai_api_key)

# ─────────────────────────────────────────────────────────────
#  Async helpers
# ─────────────────────────────────────────────────────────────

def run_async(coro):
    """Run an async coroutine from Streamlit's sync context."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)


async def run_agent_pipeline(user_text: str, history: list[dict]) -> tuple[AssistantResponse, str]:
    """
    Two-agent pipeline:
      1. VoiceAssistant  — produces a structured AssistantResponse
      2. TTSDirector     — produces delivery instructions for the TTS call
    """
    # Build a context string that includes recent conversation turns
    context_lines = []
    for msg in history[-6:]:          # last 3 exchanges (6 messages)
        role = "User" if msg["role"] == "user" else "Assistant"
        context_lines.append(f"{role}: {msg['content']}")
    context_lines.append(f"User: {user_text}")
    context = "\n".join(context_lines)

    # Agent 1 — answer the question
    assistant_result = await Runner.run(voice_assistant_agent, context)
    response: AssistantResponse = assistant_result.final_output

    # Agent 2 — write TTS delivery instructions
    tts_result = await Runner.run(tts_director_agent, response.text)
    tts_instructions: str = tts_result.final_output

    return response, tts_instructions

# ─────────────────────────────────────────────────────────────
#  Conversation history display
# ─────────────────────────────────────────────────────────────

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "audio" in msg:
            st.audio(msg["audio"], format="audio/mp3")
        if msg.get("used_web_search"):
            st.caption("🔍 Web search was used for this response.")

# ─────────────────────────────────────────────────────────────
#  Step 1 — STT: record and transcribe
# ─────────────────────────────────────────────────────────────

st.subheader("🎤 Step 1 — Speak Your Message")
audio_input = st.audio_input("Click the mic icon to record, then stop when done.")

if audio_input:
    with st.spinner("🔄 Step 1 — Transcribing with Whisper…"):
        transcript = oai_client.audio.transcriptions.create(
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
    #  Step 2 — LLM: run the agent pipeline
    # ─────────────────────────────────────────────────────────

    with st.spinner("🧠 Step 2 — Running agent pipeline…"):
        response, tts_instructions = run_async(
            run_agent_pipeline(user_text, st.session_state.messages)
        )

    if response.used_web_search:
        st.caption("🔍 Web search was used to answer this question.")

    # ─────────────────────────────────────────────────────────
    #  Step 3 — TTS: synthesize with delivery instructions
    # ─────────────────────────────────────────────────────────

    with st.spinner("🔊 Step 3 — Synthesizing speech…"):
        tts_kwargs = dict(
            model=st.session_state.tts_model,
            voice=st.session_state.voice,
            input=response.text,
        )
        # Delivery instructions are only supported by gpt-4o-mini-tts
        if st.session_state.tts_model == "gpt-4o-mini-tts":
            tts_kwargs["instructions"] = tts_instructions

        tts_response = oai_client.audio.speech.create(**tts_kwargs)
        audio_bytes = tts_response.content

    # Display the assistant turn
    with st.chat_message("assistant"):
        st.write(response.text)
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
        if response.used_web_search:
            st.caption("🔍 Web search was used for this response.")

    st.session_state.messages.append({
        "role": "assistant",
        "content": response.text,
        "audio": audio_bytes,
        "used_web_search": response.used_web_search,
    })

    st.rerun()
