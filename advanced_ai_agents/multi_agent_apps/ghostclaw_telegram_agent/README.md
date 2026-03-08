### GhostClaw — Bare-Metal Telegram AI Agent

A self-hosted AI agent you message on Telegram like a co-worker. Built on Anthropic's Claude Agent SDK. Runs as a single process on your machine — no containers, no cloud, no orchestration.

This is a minimal example showing how to wire a Telegram bot to Claude's Agent SDK so the AI can read messages, use tools, and respond conversationally. The full [GhostClaw](https://github.com/b1rdmania/ghostclaw) project builds on this pattern with 22 skills (Gmail, Slack, Discord, web research, scheduled tasks, and more).

## Features

- **Telegram interface** — message your agent like a person. Supports text and voice notes.
- **Claude Agent SDK** — uses Anthropic's official agent framework for tool use, multi-turn conversation, and autonomous task execution.
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
3. **Claude Agent SDK** — messages are sent to Claude with tool definitions. Claude can use tools (web search, file operations, etc.) and responds conversationally.
4. **Response** — Claude's response is sent back to the Telegram chat.

## Going Further

The full GhostClaw project extends this pattern with:

- 22 built-in skills (Gmail, Slack, Discord, GitHub, voice, scheduled tasks)
- Per-group personality via CLAUDE.md files
- Mission Control dashboard at localhost:3333
- WhatsApp support
- Autonomous scheduled tasks (cron or natural language)

Check out the full project: [github.com/b1rdmania/ghostclaw](https://github.com/b1rdmania/ghostclaw)
