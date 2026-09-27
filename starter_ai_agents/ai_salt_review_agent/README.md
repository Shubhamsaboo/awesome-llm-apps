# 🧂 AI Salt Review Agent

An AI agent that pauses a task to ask a real human for a yes/no decision, using [Salt](https://saltapp.ai) — end-to-end encrypted chat where humans and AI agents are equal contacts — instead of building a custom notification/approval UI.

Claude turns your plain-English task description into a short question, the agent registers itself as a Salt account and posts the question as an interactive card into a chat, and the script waits for a real person to tap Approve or Deny in the Salt app.

## Features

- **No webhook server to run** — the agent reads its own inbox with a short poll of Salt's `agent/updates` endpoint ("socket mode"), so this works from a laptop or a CI job with no public URL.
- **No custom UI** — the approval prompt is a Salt "card" (structured buttons, not free-form agent output), rendered natively in the Salt app on the reviewer's phone or browser.
- **No pre-existing account needed** — the script registers a brand-new Salt agent identity for you on first run.
- **Everything is a plain REST call** — Salt's official SDKs (`salt-agent-sdk`, `saltapp-python`) aren't published to npm/PyPI yet, so this talks directly to Salt's documented `/api/v1` endpoints with `requests`, plus one PGP keypair (generated locally with `PGPy`) to register the agent's identity.

## How it works

```
you ──task──▶ Claude ──writes a question──▶ agent
                                              │
                                              ▼
                                   registers on Salt (first run)
                                              │
                                              ▼
                              waits for you to open a chat with it
                                              │
                                              ▼
                                posts an Approve/Deny card
                                              │
                                              ▼
                              you tap a button in the Salt app
                                              │
                                              ▼
                                agent reads the tap, prints the decision
```

## Setup

### Requirements

- Python 3.9+
- An Anthropic API key
- The [Salt app](https://saltapp.ai) (web or mobile) to tap the button from

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/starter_ai_agents/ai_salt_review_agent
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Set your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

### Running the agent

```bash
python salt_review_agent.py \
    --username salt-demo-reviewer-1 \
    --task "Should I refund this customer's $20 order?"
```

On the first run, with no `SALT_API_KEY` set, the script registers a new Salt agent account under the username you passed and prints an API key:

```
export SALT_API_KEY="..."
```

Export it (so future runs skip registration) and open the Salt app on your phone or in a browser, search for the username you registered, and start a chat by saying hello. The script detects the new chat, asks Claude to phrase the question, and posts an Approve/Deny card into it. Tap a button — the script prints your decision and exits.

## Notes

- Salt is end-to-end encrypted for regular messages, but a "card" (declarative buttons/sections) is structured, first-party-rendered data rather than message ciphertext, which is what keeps this example free of any PGP message encryption code — it only needs a keypair to register the agent's identity.
- This is a short-lived CLI demo, so it polls a bounded number of times. A long-running agent should hold a websocket (`AgentUpdatesChannel`) instead of polling.
- This example only uses Salt's "ask a human" primitive. Salt agents can also message, invoice, and get paid — see [saltapp.ai](https://saltapp.ai) and the open-source client repos at [github.com/0000F8](https://github.com/0000F8).
