# Prompt Compression Demo

A self-contained example of **learned prompt compression** using [SuperCompress](https://supercompress.vercel.app). This demo shows how to trim long LLM context before inference — reducing token costs by ~65% with minimal quality loss.

Instead of blindly truncating context (which loses answers in the middle), this demo scores each line of context against the current question and keeps only the most relevant lines under a fixed budget.

## Features

- Compress long agent context before sending to any LLM
- Drop-in compatible with OpenAI, Anthropic, or any chat API
- Two modes: **Hosted API** (no local ML deps) or **local compression** (full privacy)
- Measurable compression ratio and quality metrics
- ~60ms latency on CPU, ~5K-param policy

## How to Get Started

### Prerequisites

- Python 3.10+
- [Optional] An API key from [supercompress.vercel.app/dashboard](https://supercompress.vercel.app/dashboard) (for hosted API mode)

### Installation

```bash
pip install supercompress
```

### Run the Demo

```bash
python prompt_compression_demo.py
```

## Usage

Edit `prompt_compression_demo.py` to change the context text and question. The script will:
1. Take your long context and question
2. Run SuperCompress to score and select the most relevant lines
3. Print before/after stats: tokens, KV savings, compression ratio
4. [Optional] Send the compressed context to an LLM via OpenAI, Anthropic, etc.

## Features in Detail

- **Hosted API mode**: No local ML dependencies — runs on Vercel serverless
- **Local mode**: Full privacy — all computation happens on your machine
- **Any LLM backend**: Compress first, then pass to whatever model you're using
