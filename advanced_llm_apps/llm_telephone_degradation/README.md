# 📞 LLM Telephone: Watch an Answer Degrade

Pass a seed answer through rotating LLMs and watch fidelity drop step by step. Optional claims show which facts survive each rewrite.

Built on [echoChain](https://github.com/smusali/echoChain), a CLI that measures information degradation across chained model transforms, with a judge panel, claim-level fidelity, cost caps, and survival analysis.

## What it shows

1. A seed answer is rewritten in a loop: answer → question → answer.
2. Two models rotate across steps so loss is not tied to one model’s habits.
3. A separate judge scores fidelity against the seed and, when claims are given, marks each claim supported or not.
4. The chart and step list make compounding loss visible. Same-model and paraphrase controls in echoChain matter because they isolate rotation and wording effects from raw rewrite noise.

## Cost

A default run (4 steps, the two default rotating models, default judge, Redis seed with two claims) measured at **$COST_PLACEHOLDER USD** under a $1.00 budget.

## Setup

Python 3.11 or later. An [OpenRouter](https://openrouter.ai/) API key is required for Estimate and Run (dry-run reads catalog prices).

```bash
cd advanced_llm_apps/llm_telephone_degradation
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then set OPENROUTER_API_KEY
streamlit run app.py
```

You can also paste the key in the sidebar instead of using `.env`.

## How it works

1. The app writes your seed and claims to a temporary seed file (`[[seed]]` / `[[seed.claim]]`).
2. **Estimate** runs `echochain run ... --dry-run` and shows call, token, and cost upper bounds.
3. **Run** runs `echochain run ... --out TMPDIR --budget USD --yes --quiet`, then reads `manifest.json` and `chain.jsonl`.
4. The UI charts `fidelity_vs_seed` (and `claim_fidelity` when claims exist) on answer steps, and expands each step’s text and claim verdicts.
5. **Analyze** runs `echochain analyze RUN --out DIR` and shows `curves.svg`.

The app never imports echoChain’s Python modules. It uses only the CLI and the run files.

## Requirements

```
echochain>=0.2,<0.3
streamlit
```
