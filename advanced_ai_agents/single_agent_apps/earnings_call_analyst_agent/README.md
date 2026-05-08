# 📡 Earnings Call Analyst Agent

An investor-grade earnings call companion that turns any YouTube earnings call into a playback-synced analyst workspace. Paste a call URL, watch the video, and let ADK agents surface the numbers, tone shifts, filing context, and market-moving surprises that are easy to miss in a live call.

This is built for the real earnings workflow: instead of reading a transcript after the fact, you can follow management commentary with an agentic research layer that keeps every insight tied to the quote that triggered it.

![📡 Earnings Call Analyst Agent architecture](assets/earnings-call-analyst-agent-architecture.png)

## Features

### Agentic Call Research

- Identifies the company, ticker, fiscal period, and peer set from the YouTube metadata and transcript opening
- Builds a research pack with SEC filings and current market context
- Uses an ADK news agent with Google Search grounding before falling back to finance feeds
- Hides unresolved context instead of showing empty research panels

### Quote-Anchored Signal Detection

- Creates analyst cards only when the transcript contains a real investor signal
- Anchors every card to the exact quote and timestamp that triggered it
- Filters out greetings, safe-harbor boilerplate, and generic upbeat commentary
- Reveals cards as playback reaches the relevant moment in the call

### Earnings Intelligence Cards

- Flags financial metrics, margin pressure, guidance language, demand commentary, pricing, cash flow, and capex signals
- Separates company-specific statements from peer or sector context when evidence is available
- Calls out CFO hedging, confidence shifts, defensiveness, and unusually specific language
- Adds compact tables or chart summaries only when they clarify the finding

### Caption + Audio Resilience

- Uses YouTube captions when available for precise timestamps
- Falls back to ADK-powered audio transcription for captionless videos
- Realigns generated cards to the closest caption segment so the video and quote stay in sync
- Keeps a local heuristic fallback for basic metric and tone flags when Gemini is unavailable

## How to get Started?

This agent lives in `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent`.

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent
```

2. Install the required dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Configure Vertex AI or Gemini API key:

```bash
cp .env.example .env
```

For Vertex AI / Google Cloud auth:

```bash
GOOGLE_GENAI_USE_VERTEXAI=True
GOOGLE_CLOUD_PROJECT=your-google-cloud-project-id
GOOGLE_CLOUD_LOCATION=global
```

For Gemini API key auth:

```bash
GOOGLE_GENAI_USE_VERTEXAI=False
GOOGLE_API_KEY=your-google-api-key
```

4. Run the FastAPI app:

```bash
PYTHONPATH=.. python -m uvicorn earnings_call_analyst_agent.live_demo.server:app --host 127.0.0.1 --port 4188
```

5. Open the app:

```text
http://127.0.0.1:4188
```

Paste a YouTube earnings call URL. The app builds the research pack first, then reveals analyst cards as the video reaches each quote.
