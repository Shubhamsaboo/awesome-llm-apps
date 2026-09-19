# 🛡️ Autonomous Agent Financial Circuit Breaker & Token Optimization

Protect your API budget from runaway recursive loops in autonomous coding agents (**Claude Code**, **Cursor**, **Aider**, **OpenHands**) using a zero-dependency local circuit breaker proxy.

---

## 📋 Overview

Autonomous coding agents routinely run unattended in background terminals or IDE tasks. When an agent hits an unhandled test failure, build error, or syntax ambiguity at 2 AM, it enters recursive self-correction loops. 

Because LLM providers (OpenAI, Anthropic) only enforce monthly account caps—**zero per-session velocity circuit breakers exist**. A single stuck agent loop can burn through millions of tokens and rack up **$150 to $800+ USD** in unexpected API bills overnight.

This tool demonstrates how to implement a zero-dependency local HTTP reverse proxy that sits between your coding agent and LLM APIs to:
- Intercept token usage and spend in real-time
- Detect fuzzy tool loops ($\ge 85\%$ similarity via Levenshtein sequence matching)
- Enforce hard per-session spend ceilings ($ CAD/USD)
- Sever socket connections and issue OS kill signals (`taskkill` / `SIGKILL`) before exponential token costs occur

### Key Benefits
- **💰 100% Runaway Cost Prevention**: Hard spend ceilings guarantee agents cannot exceed your defined budget.
- **⚡ Zero Dependencies**: Pure Python 3.8+ Standard Library (`http.server`, `socket`, `difflib`, `sqlite3`). No bloated pip installations.
- **🔒 100% Local & Private**: All token telemetry and request logs stay strictly on your local machine in SQLite.
- **🛑 Fuzzy Loop Interception**: Catches repeating tool failures even when context strings vary slightly.

---

## 🚀 Features

- **Real-Time Token Interceptor**: Intercepts streaming SSE and JSON completions for Anthropic and OpenAI compatible APIs.
- **Fuzzy Tool Loop Terminator**: Identifies repeating failed command signatures using sequence similarity ratios.
- **Emergency Kill Switch**: Automatically sends process signals to terminate runaway agent worker processes.
- **Interactive Offline Simulator**: Test and verify circuit-breaker trip conditions without spending real API credits.
- **Local SQLite Audit Trail**: Permanent audit log of all turns, token counts, and circuit breaker events.

---

## 📦 Installation

Zero pip packages required! Runs out-of-the-box on Python 3.8+:

```bash
# Verify Python version
python --version
```

---

## 💻 Quickstart

### Step 1: Start the Circuit Breaker Proxy
```bash
python agentsentry_circuit_breaker.py serve --max-spend 5.00 --fuzzy-threshold 0.85
```

### Step 2: Route Your Autonomous Agent

#### Claude Code:
```bash
export ANTHROPIC_BASE_URL=http://127.0.0.1:8080
claude
```

#### Cursor / Aider / OpenAI SDK:
```bash
export OPENAI_BASE_URL=http://127.0.0.1:8080/v1
aider --model gpt-4o
```

---

## 🧪 Interactive Runaway Simulator

You can test circuit breaker mechanics offline without an active LLM API key:

```bash
# In terminal 1: Run proxy with a low spend cap
python agentsentry_circuit_breaker.py serve --max-spend 0.50

# In terminal 2: Run runaway simulator
python agentsentry_circuit_breaker.py simulate
```

---

## 🔗 Official Repository & Production Suite

For the complete production distribution with 1-click Windows background launcher (`.bat`), Linux daemon service (`.sh`), multi-model JSON rate limiters, and perpetual commercial license:
- **GitHub Repository**: [TheMerchCog/agentsentry](https://github.com/TheMerchCog/agentsentry)
- **Production Master Bundle**: [AgentSentry on Gumroad](https://togpole.gumroad.com/l/hozrck)
