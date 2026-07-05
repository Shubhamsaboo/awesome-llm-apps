# 🎸 Santana — Autonomous AI Agent

**Always-on autonomous agent with persistent memory, web search, code execution, and multi-platform delivery.** Runs 24/7 on a $7/mo VM with <$10/mo in LLM inference. No Docker, no Redis, no Postgres — just Python + SQLite.

![Santana hero banner](https://raw.githubusercontent.com/BadTechResearch/santana/main/docs/hero-banner.svg)

## Features

- **🧠 3-layer memory**: Session buffer → summaries → SQLite vector embeddings (all-MiniLM-L6-v2, CPU)
- **🌐 Web search**: Real-time Google + social search via Serper API
- **🐙 GitHub integration**: Read/write repos, manage files, check rate limits
- **⚡ Sandboxed code execution**: Restricted Python subprocess
- **🔒 Whitelisted terminal**: Secure command execution
- **📡 Multi-platform**: Telegram, Discord, REST API — unified agent loop
- **💰 Cost governor**: ALERT/THROTTLE/STOP thresholds — the agent controls its own spending
- **🔄 Self-awareness**: Knows its own code, tools, and prompt
- **🧪 97% test coverage**

## Quick Start

```bash
git clone https://github.com/BadTechResearch/santana
cd santana
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
python santana.py
```

15 minutes → a Telegram bot with persistent memory.

## Architecture

![Santana Architecture](https://raw.githubusercontent.com/BadTechResearch/santana/main/docs/hero-banner.svg)

```
santana/
├── santana.py              # Entry point
├── deepseek_client.py      # Direct DeepSeek API client
├── agent/                  # Core agent: self, context, evaluator, security
├── core/                   # Engine: provider chain, ReAct loop, DB, cost governor
├── tools/                  # 15+ tools (web, GitHub, code, MCP, YouTube, Twitter)
├── memory/                 # Persistent SQLite memory store
├── soul/                   # System prompts (SOUL.md, USER.md, RULES.md)
└── docs/                   # Documentation
```

## Cost breakdown (measured)

| Item | Cost/mo |
|------|---------|
| VM (GCP e2-micro, preemptible) | ~$5-7 |
| DeepSeek API (1M tokens/day, 95% cached) | ~$8-10 |
| Web search (Serper free tier) | $0 |
| **Total** | **$13-17/mo** |

## Links

- [GitHub](https://github.com/BadTechResearch/santana)
- [Release v2.0.0](https://github.com/BadTechResearch/santana/releases/tag/v2.0.0)
- [Architecture](https://github.com/BadTechResearch/santana/blob/main/docs/ARCHITECTURE.md)
- [Changelog](https://github.com/BadTechResearch/santana/blob/main/CHANGELOG.md)

## Stack

- **Runtime**: Python 3.11+, aiohttp, SQLite (WAL mode, aiosqlite)
- **LLM**: DeepSeek V4 Flash (primary), OpenRouter/Nous Portal (fallback)
- **Embeddings**: all-MiniLM-L6-v2 (80MB, CPU)
- **Framework**: Hermes Agent
