# 🛡️ Trust-Gated Multi-Agent Research Team

Build a multi-agent research pipeline where every AI agent must pass a **trust verification** before participating, and every action is recorded in a **hash-chained audit trail** that is independently verifiable.

## Features

- **Trust Gating** — Agents are scored (0-100) and tiered (gold/silver/bronze). Only agents meeting the threshold can participate
- **Cryptographic Audit Trail** — Every agent action is recorded with SHA-256 hashes chaining to the previous entry. If any record is tampered with, all subsequent hashes break
- **Multi-Agent Pipeline** — Researcher → Analyst → Writer, each building on the previous output
- **Visual Dashboard** — See which agents pass, which get blocked, and verify the entire audit chain
- **Zero External Dependencies** — Fully self-contained. Only requires `openai` and `streamlit`

## How It Works

```
                ┌─────────────────────┐
                │   Trust Registry    │
                │  (verify agents)    │
                └──┬───────┬───────┬──┘
                   │       │       │
             ┌─────▼──┐ ┌──▼────┐ ┌▼────────┐
             │Research │ │Analyst│ │ Writer  │
             │ ✅ 75   │ │ ✅ 60 │ │ 🚫 5   │
             └────┬───┘ └──┬────┘ └─────────┘
                  │        │
                  ▼        ▼
          ┌──────────────────────┐
          │  Research Pipeline   │
          │  (trusted only)      │
          └──────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │  Hash-Chained Audit  │
          │  (tamper-evident)    │
          └──────────────────────┘
```

1. **Trust Check** — Each agent's score is verified against the minimum threshold
2. **Gate** — Agents below the threshold are blocked from the pipeline
3. **Execute** — Verified agents run in sequence, each building on the previous output
4. **Audit** — Every action (including trust checks) is recorded in a hash chain

## Getting Started

### Prerequisites

- Python 3.9+
- OpenAI API key

### Installation

```bash
pip install -r requirements.txt
```

### Set your API key (optional — can also paste in the sidebar)

```bash
export OPENAI_API_KEY=your-api-key
```

### Run

```bash
streamlit run trust_gated_agents.py
```

### Quick Start (3 steps)

1. Paste your OpenAI API key in the sidebar
2. Click **Run Trust-Gated Pipeline** — agents are pre-selected with an untrusted bot as Writer
3. Watch: Researcher (75) and Analyst (60) pass, Untrusted Bot (5) gets blocked

Swap the Writer dropdown to "Report Writer (score 45)" to see all 3 pass.

## Audit Trail

The audit trail uses the same hash-chaining pattern as blockchain transaction logs:

```json
[
  {
    "seq": 0,
    "agent": "researcher-001",
    "action": "trust_verification",
    "hash": "a1b2c3...",
    "prev_hash": "0000000000000000000000000000000000000000000000000000000000000000"
  },
  {
    "seq": 1,
    "agent": "researcher-001",
    "action": "pipeline_step_1",
    "hash": "d4e5f6...",
    "prev_hash": "a1b2c3..."
  }
]
```

Each entry's `hash` is computed from: `sequence + timestamp + agent + action + input_hash + output_hash + trust_score + prev_hash`. Changing any field in any entry invalidates every subsequent hash.

The exported JSON is independently verifiable — no special tools needed, just SHA-256.

## Why This Matters

In multi-agent systems, two problems compound:

1. **Trust** — How do you know which agents are reliable before giving them work?
2. **Accountability** — After something goes wrong, how do you reconstruct what happened?

Trust gating solves #1 by checking credentials before execution. The audit trail solves #2 by creating a tamper-evident record that survives the agents' own execution — stored externally, not in the agent's own memory.

## Tech Stack

- **Streamlit** — Interactive UI with visual trust dashboard
- **OpenAI** — GPT-4o-mini for agent reasoning
- **SHA-256** — Hash-chained audit trail (no external crypto dependencies)
