"""
🎙️ Local AI Meeting Summarizer

A completely private meeting summarizer that runs 100% locally:
- Transcribes audio with OpenAI Whisper (local, no API)
- Summarizes with Ollama + Llama 3.3 (local, no API)
- Extracts action items, decisions, and key topics
- No data leaves your machine. No API keys needed.

Usage:
    streamlit run local_meeting_summarizer.py
"""

import streamlit as st
import whisper
import tempfile
import os
import json
import requests
from pathlib import Path
from datetime import datetime

# --- Configuration ---
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.1:8b"
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]

# --- Helper Functions ---

def check_ollama_running() -> bool:
    """Check if Ollama is running and accessible."""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return resp.status_code == 200
    except requests.ConnectionError:
        return False


def get_ollama_models() -> list[str]:
    """Get list of available Ollama models."""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            return [m["name"] for m in models]
    except:
        pass
    return []


@st.cache_resource
def load_whisper_model(model_size: str):
    """Load and cache the Whisper model."""
    return whisper.load_model(model_size)


def transcribe_audio(audio_path: str, model_size: str) -> dict:
    """Transcribe audio file using local Whisper model."""
    model = load_whisper_model(model_size)
    result = model.transcribe(audio_path, verbose=False)
    return result


def generate_with_ollama(prompt: str, model: str) -> str:
    """Generate text using a local Ollama model."""
    resp = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 2048,
            },
        },
        timeout=120,
    )
    if resp.status_code == 200:
        return resp.json().get("response", "")
    else:
        raise Exception(f"Ollama error: {resp.status_code} — {resp.text}")


def summarize_transcript(transcript: str, model: str) -> dict:
    """Use Ollama to generate a structured meeting summary."""
    prompt = f"""You are an expert meeting summarizer. Analyze the following meeting transcript and produce a structured summary.

TRANSCRIPT:
{transcript}

Respond in the following JSON format (no markdown, just raw JSON):
{{
    "title": "Brief meeting title based on content",
    "duration_discussed": "Estimated time topics span",
    "summary": "2-3 paragraph executive summary of what was discussed",
    "key_topics": ["topic1", "topic2", "topic3"],
    "decisions_made": ["decision1", "decision2"],
    "action_items": [
        {{"task": "What needs to be done", "owner": "Person responsible (if mentioned)", "deadline": "When (if mentioned)"}}
    ],
    "open_questions": ["Any unresolved questions or items needing follow-up"],
    "sentiment": "Overall tone of the meeting (productive, tense, casual, etc.)"
}}"""

    response = generate_with_ollama(prompt, model)
    
    # Try to parse JSON from response
    try:
        # Find JSON in response (handle cases where model wraps in markdown)
        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            return json.loads(response[json_start:json_end])
    except json.JSONDecodeError:
        pass
    
    # Fallback: return raw text
    return {
        "title": "Meeting Summary",
        "summary": response,
        "key_topics": [],
        "decisions_made": [],
        "action_items": [],
        "open_questions": [],
        "sentiment": "N/A",
    }


def format_timestamp(seconds: float) -> str:
    """Format seconds into MM:SS."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


# --- Streamlit UI ---

st.set_page_config(
    page_title="🎙️ Local Meeting Summarizer",
    page_icon="🎙️",
    layout="wide",
)

st.title("🎙️ Local AI Meeting Summarizer")
st.caption("100% private — everything runs on your machine. No API keys. No data leaves your computer.")

# --- Sidebar: Settings ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Check Ollama
    ollama_running = check_ollama_running()
    if ollama_running:
        st.success("✅ Ollama is running")
        available_models = get_ollama_models()
        if available_models:
            llm_model = st.selectbox("LLM Model", available_models, index=0)
        else:
            st.warning("No models found. Run: `ollama pull llama3.1:8b`")
            llm_model = DEFAULT_MODEL
    else:
        st.error("❌ Ollama is not running")
        st.markdown("""
        **To get started:**
        1. Install Ollama: [ollama.com](https://ollama.com)
        2. Start it: `ollama serve`
        3. Pull a model: `ollama pull llama3.1:8b`
        """)
        llm_model = DEFAULT_MODEL
    
    st.divider()
    
    whisper_model = st.selectbox(
        "Whisper Model",
        WHISPER_MODELS,
        index=2,  # default: small
        help="Larger = more accurate but slower. 'small' is a good balance.",
    )
    
    st.divider()
    st.markdown("**How it works:**")
    st.markdown("""
    1. Upload a meeting recording
    2. Whisper transcribes it locally
    3. Ollama summarizes the transcript
    4. Get action items, decisions & key topics
    """)

# --- Main Content ---

# File uploader
uploaded_file = st.file_uploader(
    "Upload a meeting recording",
    type=["mp3", "wav", "m4a", "mp4", "webm", "ogg", "flac"],
    help="Supports MP3, WAV, M4A, MP4, WebM, OGG, and FLAC formats.",
)

if uploaded_file is not None:
    # Show audio player
    st.audio(uploaded_file)
    
    # Save to temp file
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name
    
    col1, col2 = st.columns(2)
    
    # --- Step 1: Transcribe ---
    with col1:
        st.header("📝 Transcript")
        
        if "transcript" not in st.session_state or st.button("🔄 Re-transcribe"):
            with st.spinner(f"Transcribing with Whisper ({whisper_model})..."):
                result = transcribe_audio(tmp_path, whisper_model)
                st.session_state.transcript = result
        
        if "transcript" in st.session_state:
            result = st.session_state.transcript
            full_text = result["text"]
            segments = result.get("segments", [])
            
            # Show stats
            st.metric("Duration", f"{result.get('segments', [{}])[-1].get('end', 0) / 60:.1f} min" if segments else "N/A")
            
            # Timestamped view toggle
            show_timestamps = st.toggle("Show timestamps", value=True)
            
            if show_timestamps and segments:
                for seg in segments:
                    ts = format_timestamp(seg["start"])
                    st.markdown(f"**`{ts}`** {seg['text'].strip()}")
            else:
                st.text_area("Full transcript", full_text, height=400)
    
    # --- Step 2: Summarize ---
    with col2:
        st.header("📊 Summary")
        
        if not ollama_running:
            st.warning("Start Ollama to generate summaries.")
        elif "transcript" in st.session_state:
            if "summary" not in st.session_state or st.button("🔄 Re-summarize"):
                with st.spinner(f"Summarizing with {llm_model}..."):
                    summary = summarize_transcript(
                        st.session_state.transcript["text"],
                        llm_model,
                    )
                    st.session_state.summary = summary
            
            if "summary" in st.session_state:
                s = st.session_state.summary
                
                # Title
                st.subheader(s.get("title", "Meeting Summary"))
                
                # Sentiment badge
                sentiment = s.get("sentiment", "")
                if sentiment:
                    st.caption(f"Tone: {sentiment}")
                
                # Summary
                st.markdown(s.get("summary", ""))
                
                # Key Topics
                topics = s.get("key_topics", [])
                if topics:
                    st.subheader("🏷️ Key Topics")
                    st.markdown(" · ".join(f"`{t}`" for t in topics))
                
                # Decisions
                decisions = s.get("decisions_made", [])
                if decisions:
                    st.subheader("✅ Decisions Made")
                    for d in decisions:
                        st.markdown(f"- {d}")
                
                # Action Items
                actions = s.get("action_items", [])
                if actions:
                    st.subheader("📋 Action Items")
                    for a in actions:
                        if isinstance(a, dict):
                            owner = f" → **{a.get('owner', 'TBD')}**" if a.get("owner") else ""
                            deadline = f" (by {a.get('deadline')})" if a.get("deadline") else ""
                            st.markdown(f"- [ ] {a.get('task', str(a))}{owner}{deadline}")
                        else:
                            st.markdown(f"- [ ] {a}")
                
                # Open Questions
                questions = s.get("open_questions", [])
                if questions:
                    st.subheader("❓ Open Questions")
                    for q in questions:
                        st.markdown(f"- {q}")
                
                st.divider()
                
                # Export
                export_text = f"""# {s.get('title', 'Meeting Summary')}
Date: {datetime.now().strftime('%Y-%m-%d')}
Tone: {s.get('sentiment', 'N/A')}

## Summary
{s.get('summary', '')}

## Key Topics
{chr(10).join(f'- {t}' for t in topics)}

## Decisions Made
{chr(10).join(f'- {d}' for d in decisions)}

## Action Items
{chr(10).join(f'- [ ] {a.get("task", str(a)) if isinstance(a, dict) else a}' for a in actions)}

## Open Questions
{chr(10).join(f'- {q}' for q in questions)}

---
Full Transcript:
{st.session_state.transcript.get('text', '')}
"""
                st.download_button(
                    "📥 Export Summary (Markdown)",
                    export_text,
                    file_name=f"meeting-summary-{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown",
                )
    
    # Clean up temp file
    try:
        os.unlink(tmp_path)
    except:
        pass

else:
    # Empty state
    st.info("👆 Upload a meeting recording to get started. Supports MP3, WAV, M4A, MP4, and more.")
    
    with st.expander("💡 Tips for best results"):
        st.markdown("""
        - **Audio quality matters** — clear recordings produce better transcripts
        - **Use 'small' or 'medium' Whisper model** for best accuracy/speed balance
        - **Llama 3.1 8B** works great for summaries; larger models give more detail
        - **Meetings under 1 hour** work best; for longer ones, consider splitting the audio
        """)
    
    with st.expander("🔧 Setup Guide"):
        st.markdown("""
        **1. Install Ollama** (for AI summarization)
        ```bash
        # macOS
        brew install ollama
        
        # Or download from https://ollama.com
        ```
        
        **2. Pull a model**
        ```bash
        ollama pull llama3.1:8b
        ```
        
        **3. Install Python dependencies**
        ```bash
        pip install -r requirements.txt
        ```
        
        **4. Run the app**
        ```bash
        streamlit run local_meeting_summarizer.py
        ```
        """)
