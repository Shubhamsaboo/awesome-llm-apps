## 🤖 MiniMax AI Agent

A Streamlit demo that chats with [MiniMax](https://platform.minimax.io/docs) models.
It is a self-contained provider integration: pick a model, a region and an API
surface, and the app talks to MiniMax directly over HTTP.

### Features

- **Models**
  - `MiniMax-M3` (default) — 1,000,000-token context window; accepts **text, image, and video** input; supports `adaptive` and `disabled` thinking modes.
  - `MiniMax-M2.7` — 204,800-token context window; text input; `always_on` thinking.
- **Regions** — Global (`api.minimax.io`) and Mainland China (`api.minimaxi.com`).
- **API surfaces** — the Chat Completions API (`/v1/chat/completions`) and the Messages API (`/anthropic/v1/messages`). Every region exposes both.
- **Multimodal input** — MiniMax-M3 can take an optional image URL alongside your prompt.

### How to get started

1. Clone the repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/starter_ai_agents/minimax_ai_agent
```

2. Install the dependencies

```bash
pip install -r requirements.txt
```

3. Get your MiniMax API key

Sign up on the [MiniMax platform](https://platform.minimax.io/docs) (or the
[Mainland China platform](https://platform.minimaxi.com/docs)) and create an API key.

4. Run the app

```bash
streamlit run minimax_ai_agent.py
```

### How it works

`minimax_provider.py` holds a small `MiniMaxClient`. You choose a **region**
(which host to reach) and an **API surface** (Chat Completions or Messages), and
the client builds the correct URL, headers and request body for that combination:

| Region | Chat Completions base URL | Messages base URL |
| --- | --- | --- |
| Global | `https://api.minimax.io/v1` | `https://api.minimax.io/anthropic` |
| Mainland China | `https://api.minimaxi.com/v1` | `https://api.minimaxi.com/anthropic` |

The API key is sent as a Bearer token. When you give MiniMax-M3 an image URL, the
client attaches it as a multimodal content part on the Chat Completions surface.

### Tests

Offline tests stub the HTTP layer, so they run without a key or network access:

```bash
python -m unittest test_minimax_provider
```
