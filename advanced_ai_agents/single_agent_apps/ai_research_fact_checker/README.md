# AI Research Agent with Cross-Provider Adversarial Fact-Checking

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![OpenAI](https://img.shields.io/badge/Research-OpenAI-green)](https://openai.com)
[![Anthropic](https://img.shields.io/badge/Fact--Check-Anthropic-purple)](https://anthropic.com)

A research agent that **searches the web for real sources, writes a cited report, then fact-checks every claim using a completely different AI provider** — eliminating shared model biases.

Most AI research tools check their own work with the same model that wrote it. This one uses **OpenAI for research** and **Anthropic Claude for fact-checking** — different training data, different biases, genuinely independent verification.

---

## Features

- **Real web search** — DuckDuckGo search returns actual URLs (no hallucinated references, no API key needed for search)
- **Clean content extraction** — newspaper4k for articles, BeautifulSoup fallback for docs/Wikipedia (no raw HTML noise)
- **Inline citations** — every claim in the report links to a `[Source N]` reference
- **Cross-provider fact-checking** — research (OpenAI) and fact-check (Anthropic Claude) use different AI systems with different training data
- **Unsupported claim detection** — flags assertions that lack evidence
- **Source quality assessment** — evaluates diversity and authority of sources
- **Confidence scoring** — configurable threshold (default 0.75) below which reports are flagged
- **Full audit trail** — every research session, source fetch, and fact-check logged to SQLite
- **Streamlit web UI** — visual pipeline progress with claim-by-claim verification results
- **CLI mode** — run from the terminal via `research_agent.py`

---

## Why Cross-Provider Fact-Checking?

```
┌─────────────────────┐         ┌─────────────────────┐
│   OpenAI (GPT)      │         │  Anthropic (Claude)  │
│                     │         │                     │
│  • Plans research   │         │  • Reads the report │
│  • Searches web     │         │  • Checks EVERY     │
│  • Writes report    │         │    claim against     │
│  • Cites sources    │         │    source material   │
│                     │         │  • Flags fabricated  │
│  Training data A    │         │    or unsupported    │
│  Biases A           │         │    assertions        │
│                     │         │                     │
│                     │         │  Training data B     │
│                     │         │  Biases B            │
└─────────────────────┘         └─────────────────────┘
```

A single model checking its own work shares the same blind spots. By using a different provider for verification, the fact-checker can catch errors the research model is systematically blind to.

---

## Pipeline

```
Research topic
    │
    ▼
1. Research Planning (OpenAI)
   └─ Generates 3-6 targeted search queries
    │
    ▼
2. Source Gathering (DuckDuckGo + newspaper4k)
   └─ Real web search → fetch URLs → extract clean article text
    │
    ▼
3. Report Synthesis (OpenAI)
   └─ Writes a structured report with [Source N] inline citations
    │
    ▼
4. Cross-Provider Fact-Check (Anthropic Claude)
   └─ Independent verifier checks EVERY claim:
      • Is it cited?
      • Does the source actually say this?
      • Was anything exaggerated or fabricated?
    │
    ▼
VERIFIED (confidence ≥ 0.75)  —or—  FLAGGED (unsupported claims found)
```

---

## Quickstart

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set API keys (both required)
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...

# 3. Run the Streamlit app
streamlit run app.py
```

### CLI mode

```bash
# Research a topic
python research_agent.py "What are the health effects of intermittent fasting?"

# List past research
python research_agent.py --list

# Inspect a specific session
python research_agent.py --show a3f2
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI key for research planning and report synthesis |
| `ANTHROPIC_API_KEY` | Yes | Anthropic key for independent fact-checking |
| `OPENAI_BASE_URL` | No | Custom endpoint for OpenAI-compatible providers |
| `RESEARCH_AGENT_MODEL` | No | Research model (default: `gpt-4o-mini`) |
| `FACTCHECK_AGENT_MODEL` | No | Fact-check model (default: `claude-sonnet-4-20250514`) |

---

## Architecture

```
app.py               Streamlit frontend — topic input, pipeline progress, results
research_agent.py    Core logic — plan, search, extract, synthesize, fact-check, CLI
├── Search           ddgs — real DuckDuckGo web search, no API key needed
├── Extraction       newspaper4k + beautifulsoup4 — clean text from web pages
├── Research LLM     openai — JSON-mode completions for planning and synthesis
├── Fact-Check LLM   anthropic — independent verification with different model
├── Database         sqlite3 (stdlib) — research sessions / source fetches
└── CLI              argparse — run / --list / --show
```
