# 🧠 AI Agent with Self-Hosted Persistent Memory (Contexto)

This demo shows an AI agent that remembers context across separate sessions using [Contexto](https://github.com/ekailabs/contexto) — a self-hosted context engine for AI agents. The agent is backed by any OpenRouter-supported model, and memory is stored and retrieved locally with no external memory service or vendor dependency. Run the script twice: on the second run the agent recalls what was said in the first session.

## Prerequisites

- Docker installed and running
- An [OpenRouter](https://openrouter.ai) API key

## Setup

**1. Start Contexto**

```bash
git clone https://github.com/ekailabs/contexto
cd contexto
docker compose up -d
```

Contexto starts an OpenAI-compatible proxy on `http://localhost:4010`.

**2. Clone this repo and navigate to the demo folder**

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_llm_apps/llm_apps_with_memory_tutorials/ai_agent_with_contexto_memory
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Set your OpenRouter API key**

```bash
export OPENROUTER_API_KEY=your_key_here
```

**5. Run the demo**

```bash
python main.py
```

Run it a second time to see the agent recall the previous session.

## How it works

- **Proxy intercept** — the OpenAI client is pointed at `http://localhost:4010/v1` instead of OpenRouter directly. Every chat completion request passes through Contexto first.
- **Memory retrieval & injection** — before forwarding the request to the LLM, Contexto retrieves relevant memories for the user ID and injects them into the system prompt automatically.
- **Memory storage** — after each response, Contexto stores the new exchange as a memory, making it available in future sessions.

No changes to the OpenAI SDK are required. Switching back to OpenRouter directly is a one-line change to `base_url`.

## Links

- Contexto GitHub: [https://github.com/ekailabs/contexto](https://github.com/ekailabs/contexto)
