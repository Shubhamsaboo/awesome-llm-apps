# AI Research Agent with Adversarial Fact-Checking

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-gpt--4o--mini-green)](https://openai.com)

A research agent that **fetches real web sources, writes a cited report, then adversarially fact-checks every claim** — flagging unsupported assertions and fabricated citations before you trust the output.

Most AI research tools just return whatever the LLM says. This one adds a **cold fact-checker** — a separate LLM pass that reads the report with no memory of writing it and asks: *"Does this claim actually have a supporting source, or was it made up?"*

---

## Features

- **Real source gathering** — fetches actual web pages, not hallucinated references
- **Inline citations** — every claim in the report links to a `[Source N]` reference
- **Adversarial fact-checking** — independent LLM pass that verifies claim-to-source mapping
- **Unsupported claim detection** — flags assertions that lack evidence
- **Source quality assessment** — evaluates diversity and authority of sources
- **Confidence scoring** — configurable threshold (default 0.75) below which reports are flagged
- **Full audit trail** — every research session, source fetch, and fact-check logged to SQLite
- **Streamlit web UI** — visual pipeline progress with claim-by-claim verification results
- **CLI mode** — run from the terminal via `research_agent.py`

---

## How the Adversarial Fact-Check Works

```
Research topic
    │
    ▼
1. Research Planning
   └─ LLM generates 3-6 targeted search queries for the topic
    │
    ▼
2. Source Gathering
   └─ Fetches real web pages (Wikipedia, .gov, academic sources, news)
    │
    ▼
3. Report Synthesis
   └─ Writes a structured report with [Source N] inline citations
    │
    ▼
4. Adversarial Fact-Check
   └─ Cold verifier checks EVERY claim:
      • Is it cited?
      • Does the source actually say this?
      • Was anything exaggerated or fabricated?
    │
    ▼
VERIFIED (confidence ≥ 0.75)  —or—  FLAGGED (unsupported claims found)
```

**Why this matters:** LLMs confidently cite sources that don't exist and make claims
no source supports. The adversarial fact-checker has no stake in the report being
correct — its only job is to find gaps between what was claimed and what the
sources actually say.

---

## Quickstart

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the Streamlit app
streamlit run app.py
```

Enter your OpenAI API key in the sidebar, type a research topic, and click **Research & Fact-Check**.

### CLI mode

```bash
export OPENAI_API_KEY=sk-...

# Research a topic
python research_agent.py "What are the health effects of intermittent fasting?"

# List past research
python research_agent.py --list

# Inspect a specific session
python research_agent.py --show a3f2
```

---

## Example Output

### Verified result

```
─────────── Research Topic ───────────
What are the health effects of intermittent fasting?

Refined topic: Health effects, benefits, and risks of intermittent fasting
based on current scientific evidence

  1. intermittent fasting health benefits meta-analysis
  2. intermittent fasting risks side effects
  3. intermittent fasting weight loss clinical trials
  4. intermittent fasting skeptical criticism limitations

──────── Gathering Sources ────────
  Gathered 6 sources

──────── Fact-Check Verdict ────────
VERIFIED (82%)

All major claims are supported by cited sources. The report correctly
notes disagreement between studies on long-term effects. One minor claim
about autophagy lacks a direct citation but is consistent with Source 3.

Source quality: Good — mix of NIH, Harvard Health, and peer-reviewed
journal summaries. Would benefit from a primary research paper.

  ✓ "IF reduces insulin resistance by 20-31%" — Source 2 (NIH)
  ✓ "Time-restricted eating shows comparable weight loss" — Source 4
  ✓ "Side effects include headaches and irritability" — Source 3
  ✗ "Autophagy increases after 16 hours" — no direct citation
```

### Flagged result

```
──────── Fact-Check Verdict ────────
FLAGGED (38%)

Multiple claims lack citations. The report states "studies show a 40%
reduction in cancer risk" but no provided source supports this specific
statistic. Source 2 discusses cancer research in general terms but does
not cite this figure. The report also attributes a quote to the WHO
that does not appear in any fetched source.

  ✗ "40% reduction in cancer risk" — Source 2 does not support this
  ✗ "WHO recommends IF for metabolic syndrome" — no source
  ✓ "IF can lower blood pressure" — Source 1 (Harvard Health)
```

---

## Architecture

```
app.py               Streamlit frontend — topic input, pipeline progress, results
research_agent.py    Core logic — plan, gather, synthesize, fact-check, CLI
├── Database         sqlite3 (stdlib) — research sessions / source fetches
├── LLM              openai — JSON-mode completions for each pipeline stage
├── HTTP             httpx — source fetching, 50 KB cap, 15 s timeout
└── CLI              argparse — run / --list / --show
```
