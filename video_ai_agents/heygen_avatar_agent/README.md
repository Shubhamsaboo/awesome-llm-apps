# 🤖 HeyGen Avatar Agent

A real-time conversational video avatar you can customize for any use case — customer support, sales, tutoring, or your own idea. Powered by HeyGen LiveAvatar.

## Features

- Real-time lip-synced video avatar that speaks and listens in your browser
- HeyGen manages all speech recognition, LLM reasoning, and voice synthesis
- Four built-in persona templates (Customer Support, Sales, Tutor, Personal Assistant)
- Fully customizable system prompt — adapt the avatar to any role or use case
- Custom opening line — the avatar greets users in your brand's voice
- Sandbox mode for free testing (no credits, no paid plan required)
- Choose an avatar face in production (public LiveAvatar catalog, or your own ID)
- Zero WebRTC or audio encoding code needed — HeyGen's embed handles it

## How to get Started

1. **Clone the repo**
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/video_ai_agents/heygen_avatar_agent
   ```

2. **Create and activate a virtual environment**
   ```bash
   # macOS / Linux
   python -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Get your HeyGen (LiveAvatar) API key**
   - Open [LiveAvatar Developers](https://app.liveavatar.com/developers) (LiveAvatar is a HeyGen product)
   - Copy your API key
   - Create a `.env` file:
   ```bash
   HEYGEN_API_KEY=your_heygen_api_key_here
   ```
   (Or paste it directly in the sidebar — no .env file needed for quick testing)

5. **Run the app**
   ```bash
   streamlit run avatar_agent.py
   ```

6. **Configure and launch**
   - Set your persona in the sidebar
   - Use the **Sandbox (free)** tab to use Wayne, or **Choose Avatar Face** to pick another face
   - Click **Launch Avatar** — the live embed opens; use **Back to config** to return

## Project structure

The agent is split into small, single-responsibility modules so it stays easy to read and extend:

```
heygen_avatar_agent/
├── avatar_agent.py       # App flow — state, sidebar, launch (run this)
├── ui_helpers.py         # Layout CSS, previews, Sandbox / Faces / Live views
├── config.py             # Settings + API key resolution
├── personas.py           # Built-in persona presets (pure data)
├── liveavatar_client.py  # UI-agnostic LiveAvatar API client
├── requirements.txt
└── .env.example
```

- **Add a persona** — append a `Persona` to `PERSONAS` in `personas.py`; the sidebar picks it up automatically.
- **Tweak the UI** — gallery layout and preview cards live in `ui_helpers.py`.
- **Reuse the API** — `LiveAvatarClient` has no Streamlit dependency, so you can call it from any script or test.

## How it works

1. **Persona creation** — Your system prompt is sent to the LiveAvatar Contexts API, which stores the avatar's role, behavior, and knowledge boundaries. The opening line sets what the avatar says first when the session starts.

2. **Embed generation** — A single API call to `/v2/embeddings` provisions a fully managed session and returns an iframe URL. HeyGen handles WebRTC, room management, and all infrastructure behind the scenes.

3. **Live conversation** — The iframe runs in your browser. HeyGen's pipeline processes your speech (ASR), generates a response using the LLM with your system prompt as context, converts it to speech (TTS), and drives the avatar's lip-sync in real time. No client-side audio code required.

4. **Sandbox vs Production** — Sandbox mode uses a single free test face (**Wayne**, `dd73ea75-1218-4ef3-92ce-606d5f7fbc0a`) and sessions last ~1 minute. For production: uncheck Sandbox Mode, pick a face from the public avatar list (or paste your own avatar ID from the LiveAvatar dashboard), and sessions run at 2 credits/minute.
