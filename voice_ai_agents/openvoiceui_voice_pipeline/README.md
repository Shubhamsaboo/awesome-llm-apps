# 🎙️ OpenVoiceUI Voice Pipeline — Full STT → LLM → TTS Agent

A self-contained voice AI agent that demonstrates the complete voice conversation loop:
**Speech-to-Text → Language Model → Text-to-Speech**, all running in the browser.

Inspired by the architecture behind [OpenVoiceUI](https://github.com/MCERQUA/OpenVoiceUI), an open-source voice AI platform.

---

## How It Works

| Step | What Happens | Powered By |
|------|-------------|------------|
| 🎤 **STT** | User records audio in the browser | OpenAI Whisper |
| 🧠 **LLM** | Transcript is sent to a language model | OpenAI GPT-4o |
| 🔊 **TTS** | Response is synthesized and played back | OpenAI TTS |

The app maintains full conversation history so the AI remembers context across turns.

---

## Features

- **Browser mic recording** via Streamlit's built-in `st.audio_input()`
- **Whisper transcription** — handles accents, noise, and natural speech
- **Multi-turn conversation** — full history passed to the LLM on every turn
- **Configurable persona** — edit the system prompt in the sidebar
- **Voice selection** — choose from 6 OpenAI TTS voices (alloy, echo, fable, nova, onyx, shimmer)
- **Model selection** — swap between GPT-4o, GPT-4o-mini, and GPT-4-Turbo

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Get an OpenAI API key

Sign up at [platform.openai.com](https://platform.openai.com) and create an API key.
You can also set it as an environment variable so it pre-fills in the sidebar:

```bash
export OPENAI_API_KEY=sk-...
```

### 3. Run the app

```bash
streamlit run voice_pipeline.py
```

Open the URL shown in your terminal, enter your API key in the sidebar, and start talking.

---

## What You'll Learn

This tutorial is a minimal but complete implementation of the voice AI loop used in production voice assistants:

1. **Audio capture** — how to get raw audio bytes from a browser session
2. **STT with Whisper** — how to call `client.audio.transcriptions.create()` correctly
3. **Stateful conversation** — how to maintain and pass conversation history to the LLM
4. **TTS synthesis** — how to call `client.audio.speech.create()` and play audio in Streamlit
5. **Session state management** — how to store conversation turns across Streamlit reruns

---

## Resources

- [OpenAI Whisper API docs](https://platform.openai.com/docs/guides/speech-to-text)
- [OpenAI Chat Completions API docs](https://platform.openai.com/docs/guides/text-generation)
- [OpenAI TTS API docs](https://platform.openai.com/docs/guides/text-to-speech)
- [OpenVoiceUI — open-source voice AI platform](https://github.com/MCERQUA/OpenVoiceUI)
