# AI Assistant with Biological Memory Decay 🧠

A Streamlit app that gives an AI assistant persistent memory across sessions using [YourMemory](https://github.com/sachitrafa/YourMemory) — an open-source memory layer built on the Ebbinghaus forgetting curve.

Unlike flat memory systems, YourMemory memories **decay over time**, **strengthen on recall**, and **connect through an entity graph** — so the assistant remembers what matters and forgets what doesn't.

## Features

- **Persistent memory** — context survives across sessions
- **Biological decay** — memories fade exponentially; important ones last longer
- **Entity graph** — related memories surface automatically via spaCy NER
- **Memory panel** — see all stored memories with live strength scores
- **Auto-store** — assistant detects and stores new facts from the conversation

## How It Works

1. Before every response, relevant memories are recalled using hybrid BM25 + vector retrieval
2. Recalled context is injected into the system prompt
3. After responding, the assistant flags new facts with `[STORE: fact]` — these are saved automatically
4. Memories below strength `0.05` are pruned every 24h by YourMemory's background job

## Setup

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Start the YourMemory server**
```bash
yourmemory-setup   # run once to initialise
yourmemory         # starts HTTP server on localhost:3033
```

**3. Run the app**
```bash
streamlit run yourmemory_agent.py
```

**4. Enter your Anthropic API key** in the sidebar and start chatting.

## Memory Decay Rates

| Category | Half-life | Use case |
|---|---|---|
| `strategy` | ~38 days | Approaches that worked |
| `fact` | ~24 days | Preferences, identity |
| `assumption` | ~19 days | Inferred context |
| `failure` | ~11 days | Errors, wrong approaches |
