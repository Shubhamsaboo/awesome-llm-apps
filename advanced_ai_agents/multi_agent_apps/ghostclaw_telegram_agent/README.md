### GhostClaw — Bare-Metal Telegram AI Agent

A self-hosted AI agent you message on Telegram like a co-worker. Built on Anthropic's Claude API with tool use and persistent conversation memory. Runs as a single process on your machine — no containers, no cloud, no orchestration.

This is a minimal example showing how to wire a Telegram bot to Claude so the AI can read messages, use tools, and respond conversationally.

## Features

- **Telegram interface** — message your agent like a person. Supports text and voice notes.
- **Claude API with tool use** — uses Anthropic's messages API with tool definitions for multi-turn conversation and autonomous task execution.
- **Persistent memory** — conversation history stored in SQLite so context carries across sessions.
- **Bare metal** — runs directly on your machine. No Docker, no Kubernetes, no cloud functions.

## Requirements

Install dependencies:

```bash
pip install -r advanced_ai_agents/multi_agent_apps/ghostclaw_telegram_agent/requirements.txt
```

You'll need:

- `ANTHROPIC_API_KEY` — from [console.anthropic.com](https://console.anthropic.com)
- `TELEGRAM_BOT_TOKEN` — from [@BotFather](https://t.me/BotFather) on Telegram

## How to Run

```bash
export ANTHROPIC_API_KEY="your-key-here"
export TELEGRAM_BOT_TOKEN="your-token-here"
python advanced_ai_agents/multi_agent_apps/ghostclaw_telegram_agent/ghostclaw_telegram_agent.py
```

Message your bot on Telegram. It responds using Claude.

## How It Works

1. **Telegram polling** — the script listens for incoming messages via the Telegram Bot API.
2. **Message history** — each chat's conversation history is stored in SQLite, giving Claude context across messages.
3. **Claude API with tools** — messages are sent to Claude with tool definitions. Claude can use tools and responds conversationally.
4. **Tool use loop** — when Claude calls a tool, the script executes it and feeds the result back until Claude produces a final text response.
5. **Response** — Claude's response is sent back to the Telegram chat, chunked at 4096 chars if needed.
