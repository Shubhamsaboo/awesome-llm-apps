# 📰 Local AI News Brief — with Receipts

A morning tech brief that runs **fully local** (Ollama) and leaves **receipts**: the whole pipeline is one plain-text workflow file, statically audited *before a single token is spent*, and every run writes a hash-chained trace you can verify after.

No Python here — the entire app is one YAML file run by a single binary ([nika](https://github.com/supernovae-st/nika), AGPL-3.0 Rust engine; I'm its author).

## Features

- **One file is the whole app**: fetch the Hacker News front-page feed → keep the top 8 stories → a local model writes the brief → save `brief.md`. Diffable, reviewable, reusable.
- **Checked before it runs**: `nika check` audits the DAG, types, secret flows and an honest cost floor — *before* anything executes. Broken pipeline = named finding, zero tokens spent.
- **Receipts after it runs**: every run writes a hash-chained trace; `nika trace verify` exits 0 or names the first broken link. The proof comes from the runner, not from the model's prose.
- **Local-first**: defaults to `ollama/llama3.2:3b`. Zero API keys. Swap one line for any provider (Claude, GPT, Gemini, Qwen…) — the logic doesn't change.
- **Zero-setup dry run**: an offline mock provider lets you prove the whole pipeline without Ollama or keys.

## How to get Started

1. Install the engine (single binary) and, for the real run, [Ollama](https://ollama.com):

```bash
brew install supernovae-st/tap/nika     # or grab a release tarball
ollama pull llama3.2:3b                  # ~2 GB, once
```

2. Audit the pipeline before running it (offline):

```bash
nika check news_brief.nika.yaml
```

3. Run it:

```bash
nika run news_brief.nika.yaml                    # real local run
nika run news_brief.nika.yaml --model mock/echo  # zero-setup dry run (no Ollama, no keys)
```

4. Read `brief.md` — then verify the run wasn't tampered with:

```bash
nika trace verify .nika/traces/*.ndjson   # exit 0 = chain intact
```

## How it works

Four tasks, one DAG: `fetch_feed` (RSS, parsed natively) → `top_stories` (a jq reshape) → `brief` (the only LLM call, budget-visible) → `save`. Change the feed URL, the story count, or the model — it's all in the file's `vars:`.
