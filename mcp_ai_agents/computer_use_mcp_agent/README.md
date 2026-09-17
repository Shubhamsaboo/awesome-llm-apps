# 🖱️ Computer Use MCP Agent

A terminal agent that controls a real Windows desktop with natural language. It talks to the [screen-control](https://github.com/Xeakaes/computer-use-for-all-agents) MCP server, which exposes 16 tools: screenshot, OCR, frame diff, mouse, keyboard, held-key tracking, window enumeration, focus, per-window input, window capture, close, and a game mode.

The agent runs an OpenAI-compatible tool-calling loop: the model picks tools, the MCP server executes them on the desktop, and results (including screenshots) go back to the model until the task is done.

## Features

- **Real desktop control**: click, type, scroll, focus windows, and close windows on a live Windows machine
- **See the screen**: full-screen or per-window screenshots, OCR text extraction, and frame diff for change detection
- **OpenAI-compatible models**: works with OpenAI, Gemini (OpenAI-compat endpoint), Groq, OpenRouter, or any local server that speaks the Chat Completions API
- **Safety features built into the server**: session token auth, blocked deadly shortcuts such as Alt+F4, and a focus guard that refuses keystrokes aimed at the wrong window
- **Inspect mode**: `--list-tools` prints every tool the server offers, with no model call and no input injection

## Tech Stack

- **Python 3.10+**
- **mcp** (official Model Context Protocol SDK): connects to the server over Streamable HTTP
- **openai** SDK: Chat Completions with tool calling

## Workflow

1. Start the screen-control server on Windows (see its README: `python server.py`, plus `python mcp_server.py --http --port 8751` for the MCP transport)
2. This agent connects to `http://127.0.0.1:8751/mcp` with the session token from the server's `.token` file
3. It converts the MCP tool list into OpenAI tool schemas
4. The model drives the desktop through `session.call_tool(...)` until it answers without tool calls

```
you ──> model ──> tool call ──> MCP server ──> Windows desktop
 ^                                                    |
 └────────────── final answer <── screenshot/OCR <────┘
```

## Getting Started

### Prerequisites

- A Windows machine running the [screen-control](https://github.com/Xeakaes/computer-use-for-all-agents) server (REST + MCP transports)
- Python 3.10+
- An API key for an OpenAI-compatible provider

### Setup

```bash
cd mcp_ai_agents/computer_use_mcp_agent
pip install -r requirements.txt

# Windows side (from the screen-control repo):
#   python server.py                     # REST API on :8745, writes .token
#   python mcp_server.py --http --port 8751
```

### Run

```bash
# See what the server offers (no model call, no input):
python main.py --list-tools

export OPENAI_API_KEY=sk-...            # or GROQ_API_KEY / OPENROUTER_API_KEY + --api-base

python main.py "Take a screenshot and tell me what you see"
python main.py "Open Notepad, type hello world, then read it back with OCR"
python main.py "List my windows and focus the one named Spotify"

# Gemini through its OpenAI-compatible endpoint:
python main.py --api-base https://generativelanguage.googleapis.com/v1beta/openai/ \
    --model gemini-2.5-flash "What is on my screen right now?"

# Groq:
python main.py --api-base https://api.groq.com/openai/v1 \
    --model llama-3.3-70b-versatile --api-key "$GROQ_API_KEY" "..."
```

Without a task argument the agent reads tasks from stdin, one per line.

### Token

The agent needs the server's session token. Resolution order:

1. `--token` flag
2. `--token-file` flag (default: `.token` in the current directory)
3. `SCREEN_CONTROL_TOKEN` environment variable

Copy `.token` from the screen-control checkout, or pass `--token-file /path/to/screen-control/.token`. To control a machine over the network, tunnel port 8751 and pass `--base-url https://your-host` (the token still travels in the `X-Auth-Token` header).

## Safety Notes

- The server binds to 127.0.0.1 and requires a per-start session token; anything the agent does runs under that token
- Deadly shortcuts (Alt+F4 and friends) are blocked server-side, and the focus guard refuses typing when the foreground window does not match the one the agent targeted
- Models sometimes click the wrong thing. Start with read-only tasks (screenshot, list windows, OCR) before letting the model move your mouse
- Use `--max-steps` to bound how many tool calls a single task can make
