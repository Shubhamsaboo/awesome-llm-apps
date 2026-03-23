# 🛡️ Trust-Gated Multi-Agent Research Team

A Streamlit app that builds a multi-agent research pipeline where every AI agent must pass a **live trust verification** before it can participate. Uses [AgentStamp](https://agentstamp.org) — an open-source trust intelligence API — to score and gate agents in real time.

## Features

- **Live Trust Scoring** — Each agent is verified against AgentStamp's API (0-100 score, tiered: gold/silver/bronze)
- **Configurable Trust Threshold** — Slider to set your minimum acceptable trust score
- **Multi-Agent Pipeline** — Researcher → Analyst → Writer, each step builds on the previous
- **Visual Trust Dashboard** — See which agents pass and which get blocked, with scores and reasons
- **Dynamic Pipeline** — Only verified agents participate; blocked agents are excluded automatically

## How It Works

```
┌─────────────────────────────────────────────────────┐
│              AgentStamp Trust API                     │
│         (live scoring, 0-100 scale)                  │
└──────────┬──────────────┬──────────────┬────────────┘
           │              │              │
     ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
     │ Researcher │ │  Analyst  │ │  Writer   │
     │  Score: 36 │ │ Score: 36 │ │ Score: 0  │
     │  ✅ PASS   │ │ ✅ PASS   │ │ 🚫 BLOCK  │
     └─────┬─────┘ └─────┬─────┘ └───────────┘
           │              │
           ▼              ▼
     ┌───────────────────────┐
     │   Research Pipeline   │
     │  (trusted agents only)│
     └───────────────────────┘
```

## Getting Started

### Prerequisites

- Python 3.9+
- OpenAI API key
- Internet access to [agentstamp.org](https://agentstamp.org) (free, no API key required for trust lookups)

### Installation

```bash
pip install -r requirements.txt
```

### Run the App

```bash
streamlit run trust_gated_agents.py
```

### Usage

1. Enter your OpenAI API key in the sidebar
2. Paste wallet addresses for each agent role — browse [agentstamp.org/registry](https://agentstamp.org/registry) to find registered agents
3. Adjust the **Minimum Trust Score** slider (try 30 to see the gate in action)
4. Enter a research topic and click **Run Trust-Gated Research Pipeline**

## Demo Wallets

Browse [agentstamp.org/registry](https://agentstamp.org/registry) for registered agent wallets, or try:

| Wallet | Expected Result |
|--------|----------------|
| Any registered agent wallet | Passes trust gate (score 30+) |
| `0x0000000000000000000000000000000000000001` | Blocked — score 0, no identity on record |

## Why Trust-Gate Your Agents?

In multi-agent systems, you're delegating real work to autonomous agents. Without trust verification:

- **Unverified agents** could produce unreliable outputs
- **Compromised agents** could inject malicious content into your pipeline
- **Unknown agents** have no track record or accountability

AgentStamp provides a live, external trust signal — like a credit score for AI agents — so you can make informed decisions about which agents to trust with your tasks.

## Tech Stack

- **Streamlit** — Interactive UI
- **OpenAI** — GPT-4o-mini for agent reasoning
- **AgentStamp** — Trust verification API (`pip install agentstamp`)
