# Screenpipe Work Memory Agent

This MCP agent answers questions about what actually happened on your computer.
It searches local screen recordings, audio transcripts, meetings, input events,
and UI context captured by [screenpipe](https://screenpipe.com).

Instead of pasting context into every prompt, ask questions such as:

- "Summarize what I worked on in the last two hours, grouped by project."
- "What did I promise during my meeting with Alex last week?"
- "Find the page where I saw that pricing."
- "Turn the client onboarding process I followed yesterday into an SOP."
- "Which repeated steps from this week are good automation candidates?"

## How it works

```text
screenpipe on your computer
    -> local screenpipe API
    -> screenpipe-mcp
    -> work memory agent
    -> your configured LLM
```

The agent uses screenpipe MCP tools to summarize activity, search OCR and audio,
inspect meetings and UI elements, and export recordings. It is instructed to
ground answers in observed evidence and label inferred SOP steps.

## Prerequisites

- Python 3.10+
- Node.js 18+ with `npx`
- screenpipe installed, running, and allowed to record the context you want to query
- An OpenAI API key, or an OpenAI-compatible local model endpoint

Download screenpipe from [screenpipe.com](https://screenpipe.com) or build it
from the [source-available repository](https://github.com/screenpipe/screenpipe).

## Setup

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/mcp_ai_agents/screenpipe_work_memory_agent

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
```

Add your key to `.env`:

```env
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
```

Check that screenpipe and `npx` are ready:

```bash
python screenpipe_work_memory_agent.py --check
```

## Run

Start an interactive session:

```bash
python screenpipe_work_memory_agent.py
```

Or run one question:

```bash
python screenpipe_work_memory_agent.py \
  "Summarize my work from the last two hours with supporting evidence"
```

The app launches the published `screenpipe-mcp` package with:

```bash
npx -y screenpipe-mcp
```

## Use a local model

Any OpenAI-compatible endpoint can be used. For example, with Ollama:

```env
OPENAI_API_KEY=ollama
OPENAI_MODEL=qwen3:8b
OPENAI_BASE_URL=http://localhost:11434/v1
```

## Privacy boundary

The screenpipe MCP server talks only to the local screenpipe API and stores no
data itself. The context returned by MCP tools is still sent to the LLM endpoint
you configure. Use a local endpoint when work data must remain on the device.

You control what screenpipe records, which apps and URLs are excluded, and how
long local data is retained.

## Embed capture in your own application

This example uses the installed screenpipe app because that is the fastest way
to try the agent. To embed capture directly in an Electron, Swift, or Tauri app,
see the runnable
[screenpipe SDK examples](https://github.com/screenpipe/screenpipe/tree/main/ee/sdk/examples),
including the
[Electron recorder example](https://github.com/screenpipe/screenpipe/tree/main/ee/sdk/examples/electron-app).
