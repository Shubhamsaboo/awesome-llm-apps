# 🎙️ OpenVoiceUI Voice Pipeline — Full STT → LLM Agent → TTS

A complete voice AI agent that demonstrates the end-to-end voice conversation loop using the **openai-agents SDK**:

**Speak → Whisper STT → Agent Pipeline (with Web Search) → Expressive TTS**

Inspired by the architecture behind [OpenVoiceUI](https://github.com/MCERQUA/OpenVoiceUI), an open-source voice AI platform.

---

## How It Works

| Step | What Happens | Powered By |
|------|-------------|------------|
| 🎤 **STT** | Browser mic recording transcribed to text | OpenAI Whisper |
| 🧠 **VoiceAssistant Agent** | Answers the question; uses WebSearchTool for real-time data | openai-agents + GPT-4o |
| 🎬 **TTSDirector Agent** | Writes delivery instructions (tone, pace, emphasis) | openai-agents + GPT-4o-mini |
| 🔊 **TTS** | Synthesizes expressive speech from text + instructions | gpt-4o-mini-tts |

The app maintains full conversation history, passing the last 3 exchanges to the agent so it can respond in context.

---

## Agent Architecture

```
User Voice Input
      │
      ▼
 [Whisper STT]  ──── transcript ────►
                                     [VoiceAssistant Agent]
                                       - GPT-4o
                                       - WebSearchTool (auto-triggered for live data)
                                       - Structured output: { text, used_web_search }
                                             │
                                             ▼
                                     [TTSDirector Agent]
                                       - GPT-4o-mini
                                       - Writes delivery instructions
                                             │
                                             ▼
                                     [gpt-4o-mini-tts]
                                       - Synthesizes expressive audio
                                             │
                                             ▼
                                      🔊 Audio Response
```

---

## Features

- **Browser mic recording** via Streamlit's built-in `st.audio_input()`
- **Two-agent pipeline** using the `openai-agents` SDK
- **Automatic web search** — the VoiceAssistant uses `WebSearchTool` when the question needs real-time data
- **Expressive TTS** — TTSDirector writes delivery instructions; `gpt-4o-mini-tts` uses them to vary tone and emphasis
- **Multi-turn conversation** — recent history passed as context on every turn
- **Structured output** via Pydantic — agent responses are typed, not raw strings

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Get an OpenAI API key

Sign up at [platform.openai.com](https://platform.openai.com) and create an API key.
Optionally set it as an environment variable:

```bash
export OPENAI_API_KEY=sk-...
```

### 3. Run

```bash
streamlit run voice_pipeline.py
```

Enter your API key in the sidebar, click the mic, and start talking.

---

## What You'll Learn

1. **STT with Whisper** — how to pass browser-captured audio to `client.audio.transcriptions.create()`
2. **openai-agents SDK** — how to define `Agent` objects with tools and structured `output_type`
3. **WebSearchTool** — how to give an agent live internet access with one line
4. **Pydantic structured output** — how to parse typed agent responses instead of raw strings
5. **Two-agent chaining** — how one agent's output feeds the next agent's input
6. **Expressive TTS** — how to use `gpt-4o-mini-tts` with `instructions` for natural-sounding speech
7. **Async in Streamlit** — the `asyncio.run()` + RuntimeError fallback pattern

---

## Resources

- [openai-agents SDK docs](https://openai.github.io/openai-agents-python/)
- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
- [OpenAI TTS API](https://platform.openai.com/docs/guides/text-to-speech)
- [OpenVoiceUI — open-source voice AI platform](https://github.com/MCERQUA/OpenVoiceUI)
