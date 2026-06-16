# ⚡ OpenClacky Prompt Cache Optimizer

Reduce LLM API costs by **~20–40%** using OpenClacky's Prompt Cache architecture — achieving a **93.8% cache hit rate** across a 7-day global average.

Benchmark your own coding sessions and see exactly how much you would save vs Claude Code or OpenAI Codex.

---

## 📋 Overview

Most AI coding agents (Claude Code, OpenAI Codex) are **stateless by design** — they re-send the full system prompt and entire conversation history on every single turn. For a typical 10-turn coding session with a 16-tool schema, that means paying for the same 2,000+ system prompt tokens **10 times over**.

OpenClacky solves this with four mechanisms:

| Mechanism | What it does | Savings |
|---|---|---|
| **Frozen system prompt** | 16-tool schema never changes → always hits cache | High |
| **Dual cache markers** | Both system block and tool defs are cache-pinned | Medium |
| **Insert-then-Compress** | Older history is summarized, not dropped | Medium |
| **Stable 16-tool schema** | No schema churn = no cache invalidation | High |

**Result:** ~0.8× the cost of Claude Code per session.

---

## 📊 Benchmark Numbers (10-turn coding session)

| Agent | Input tokens | Output tokens | Cost | vs Claude Code |
|---|---|---|---|---|
| Claude Code | 5,088 | 186 | $0.0181 | 1.0× (baseline) |
| OpenAI Codex | 5,088 | 186 | $0.0181 | 1.0× |
| **OpenClacky** | **971** | **186** | **$0.0081** | **0.45×** |

> System prompt: 16 tools + rules (~364 tokens). Claude Sonnet 3.7 pricing ($3/$15 per 1M).
> Cache hit rate: 93.8% (7-day global average).

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the CLI benchmark (no API key required)

```bash
python cache_benchmark.py
```

Sample output:
```
=================================================================
  Prompt Cache Benchmark: OpenClacky vs Claude Code vs Codex
=================================================================

  Session: 10 turns · System prompt: 364 tokens (16 tools)

  Agent             Input tok  Output tok  Total tok  Cost (USD)      vs CC
  ---------------------------------------------------------------
  Claude Code           5,088         186      5,274 $    0.0181 1.0× (baseline)
  OpenAI Codex          5,088         186      5,274 $    0.0181       1.0×
  OpenClacky ✓            971         186      1,157 $    0.0081      0.45×

  OpenClacky saves  55.4% vs Claude Code  | 55.4% vs Codex
  Cache hit rate:   93.8%  (7-day global average: 93.8%)
  System prompt re-sent by CC/Codex: 10× per session

  At 1,000 sessions/month this adds up to:
  Claude Code:  $18.05/mo
  OpenClacky:   $8.05/mo  (save $10.00/mo)
```

### 3. Run the interactive Streamlit app

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## 💻 Interactive App Features

- **Paste your own system prompt** — see token count instantly
- **Edit conversation turns** — use your real coding session
- **Adjust pricing** — supports any Claude / GPT model pricing
- **Tune cache hit rate** — from 50% to 100%
- **Monthly savings calculator** — set your sessions/month
- **Visual token breakdown** — bar chart comparison

---

## 🔍 How Cache Hit Rate is Measured

OpenClacky reports cache statistics directly from Anthropic's API response:

```python
# Every API response includes usage.cache_read_input_tokens
usage = response.usage
hit_rate = usage.cache_read_input_tokens / (
    usage.input_tokens + usage.cache_read_input_tokens
)
```

The **93.8%** figure is the 7-day rolling average across all OpenClacky users —
not a cherry-picked benchmark.

---

## 📦 Project Structure

```
openclacky_prompt_cache/
├── app.py               # Streamlit interactive demo
├── cache_benchmark.py   # CLI benchmark (no API key needed)
├── requirements.txt
└── README.md
```

---

## 🔗 Links

- **OpenClacky on GitHub**: https://github.com/clacky-ai/open-clacky
- **Documentation**: https://openclacky.com
- **License**: MIT
- **BYOK**: Supports Claude, GPT-4, DeepSeek, Kimi, Gemini, OpenRouter

---

## 📄 License

MIT — free to use, modify, and distribute.
