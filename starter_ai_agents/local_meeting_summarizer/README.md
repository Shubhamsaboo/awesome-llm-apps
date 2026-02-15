# 🎙️ Local AI Meeting Summarizer

A completely private meeting summarizer that runs 100% locally on your machine. No API keys needed. No data leaves your computer.

## Features

- **Local Transcription** — OpenAI Whisper runs on your machine, no API calls
- **Local Summarization** — Ollama + Llama 3.1 for structured summaries
- **Action Item Extraction** — Automatically identifies tasks, owners, and deadlines
- **Decision Tracking** — Captures decisions made during the meeting
- **Timestamped Transcript** — Browse the full transcript with timestamps
- **Markdown Export** — Download the summary as a markdown file
- **Multiple Audio Formats** — MP3, WAV, M4A, MP4, WebM, OGG, FLAC

## How It Works

```
Audio File → Whisper (local transcription) → Ollama (local summarization) → Structured Summary
```

1. Upload a meeting recording
2. Whisper transcribes the audio locally
3. Ollama analyzes the transcript and extracts:
   - Executive summary
   - Key topics discussed
   - Decisions made
   - Action items with owners and deadlines
   - Open questions needing follow-up
   - Overall meeting sentiment

## Getting Started

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- FFmpeg (`brew install ffmpeg` on macOS)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Pull an LLM model
ollama pull llama3.1:8b

# Run the app
streamlit run local_meeting_summarizer.py
```

### Choosing Models

**Whisper Models** (transcription):
| Model | Speed | Accuracy | RAM |
|-------|-------|----------|-----|
| tiny | ⚡⚡⚡ | ★★ | ~1 GB |
| base | ⚡⚡ | ★★★ | ~1 GB |
| small | ⚡⚡ | ★★★★ | ~2 GB |
| medium | ⚡ | ★★★★★ | ~5 GB |
| large | 🐢 | ★★★★★ | ~10 GB |

**Ollama Models** (summarization):
- `llama3.1:8b` — Fast, good quality (recommended)
- `llama3.1:70b` — Higher quality, needs more RAM
- `mistral:7b` — Good alternative
- Any model available in Ollama works

## Privacy

Everything runs locally:
- **Whisper** processes audio on your CPU/GPU — no OpenAI API calls
- **Ollama** runs the LLM on your machine — no cloud inference
- **No data is sent anywhere** — your meetings stay private
