# 🧠 Entroly Context Optimization

Reduce LLM API costs by **70–95%** through intelligent context compression. Your AI coding tools only see 5% of your codebase — Entroly gives them the full picture for a fraction of the cost.

This app demonstrates how to use [Entroly](https://github.com/juyterman1000/entroly) to dramatically reduce token usage with any LLM application. Unlike truncation or RAG-only approaches, Entroly uses information-theoretic selection to keep what matters and compress what doesn't.

## Features

- 💰 **70–95% token reduction** verified across real workloads
- ⚡ **<10ms latency** — pure Rust+Python, no neural inference
- 🎯 **Zero accuracy loss** — benchmark-verified (n=100, Wilson 95% CIs)
- 🧠 **Content-aware** — handles code, logs, JSON, prose, CSV, email, XML, stack traces
- 🔒 **Fully local** — no API keys, no cloud, no data leaves your machine
- 🔄 **Deterministic** — same input → identical output (SHA-256 verified)

## How It Works

1. **Detect** — Auto-classifies content type (code, JSON, logs, prose, etc.)
2. **Score** — TF-IDF + Marginal Information Gain (MIG) ranks sentences by unique information
3. **Select** — Greedy submodular maximization picks the optimal subset (provably (1−1/e)-optimal)
4. **Deliver** — Compressed output preserves structure and critical information

## Getting Started

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run the demo
```bash
streamlit run entroly_demo.py
```

### Use in your own code (2 lines)
```python
from entroly import compress, compress_messages

# Compress any content — code, JSON, logs, prose
compressed = compress(api_response, budget=2000)

# Compress a full LLM conversation
messages = compress_messages(messages, budget=30000)
```

### Use as a proxy (zero code changes)
```bash
entroly proxy --port 9377
ANTHROPIC_BASE_URL=http://localhost:9377 claude
OPENAI_BASE_URL=http://localhost:9377/v1 cursor
```

## Demo Walkthrough

The Streamlit app has three tabs:

| Tab | What It Shows |
|---|---|
| **📄 Single Content** | Compress code, logs, JSON, or custom text to any token budget |
| **💬 Conversation** | Compress a multi-turn LLM conversation (preserves recent messages) |
| **📊 Benchmark** | Run compression at 6 budget levels, see savings and latency |

## Verified Performance

| Benchmark | Accuracy Retention | Token Savings |
|---|---|---|
| NeedleInAHaystack | 100% | 99.5% |
| LongBench (HotpotQA) | 106.2% | 85.3% |
| Berkeley Function Calling | 100% | 79.3% |
| SQuAD 2.0 | 97.4% | 39.3% |

> All results measured with gpt-4o-mini, Wilson 95% confidence intervals. CIs overlap on every benchmark — accuracy is statistically indistinguishable from baseline.

## Works With 38+ AI Agents

Claude Code, Cursor, Copilot, Codex CLI, Aider, Gemini CLI, Windsurf, VS Code, and 30+ more. One command: `entroly wrap <agent>`.

## Resources

- 📦 GitHub: https://github.com/juyterman1000/entroly
- 📄 PyPI: https://pypi.org/project/entroly/
- 📚 Cookbook: https://github.com/juyterman1000/entroly/tree/main/cookbook
- 📜 License: Apache 2.0
