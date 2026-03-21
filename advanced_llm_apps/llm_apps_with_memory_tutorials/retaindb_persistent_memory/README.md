# LLM App with Persistent Memory using RetainDB

A Streamlit chatbot that **remembers users across sessions** using [RetainDB](https://retaindb.com) — a persistent memory API for AI agents.

Unlike in-memory solutions (which reset on every page refresh or server restart), RetainDB stores memories in the cloud. Come back tomorrow, open a new tab, or redeploy your app — the AI still knows who you are.

## Features

- 💾 **Cross-session memory** — memories survive restarts and redeployments
- 🔍 **Semantic retrieval** — finds relevant past context, not just recent messages
- ⚡ **Fast** — 13ms avg retrieval latency globally
- 🔑 **Simple API** — two REST calls: `POST /v1/context/query` to retrieve, `POST /v1/learn` to store

## How it works

```
User sends message
       │
       ▼
POST /v1/context/query  ──► RetainDB retrieves relevant past memories
       │
       ▼
GPT-4o-mini (with memories injected as system context)
       │
       ▼
POST /v1/learn  ──► Stores the conversation turn for future sessions
```

## Setup

### 1. Get API keys

- **RetainDB**: free key at [retaindb.com](https://retaindb.com)
- **OpenAI**: key at [platform.openai.com](https://platform.openai.com)

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run

```bash
streamlit run retaindb_memory_app.py
```

Open http://localhost:8501, enter your API keys, and start chatting.

## Test cross-session memory

1. Tell the AI something: *"My name is Alex and I'm building a SaaS in TypeScript"*
2. Refresh the page (clears the session-level chat history)
3. Ask: *"What do you know about me?"*

The AI will recall what you told it — because the memory lives in RetainDB, not in the browser tab.

## Learn more

- [RetainDB docs](https://retaindb.com/docs)
- [LongMemEval benchmark](https://retaindb.com/benchmark) — 88% preference recall (SOTA)
- [npm SDK](https://www.npmjs.com/package/@retaindb/sdk) — for Node.js / TypeScript apps
