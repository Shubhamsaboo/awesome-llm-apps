# 📝 AI AI-Text Detector Agent

Is this prose AI-written? Get a probability, the lean, and the specific linguistic tells — with honest abstention on non-prose (forms, tables, scans) instead of guessing.

Built on [Stipple](https://www.stipple.sh) — a hosted MCP server for document work. The free anonymous tier works with **no API key and no signup**.

## Quickstart

```bash
pip install stipple
python agent.py ./essay.pdf
python agent.py --text "It is important to note that, in today's fast-paced world..."
```

## Example Output

```
AI-written probability: 0.99  (lean: ai)
prose ratio: 0.82

linguistic tells:
  - It is important to note that in today's fast-paced world
  - Furthermore, it is crucial to remember that

reasoning: The text relies entirely on formulaic transition clichés and generic
corporate buzzwords devoid of any specific substance.
limitations: The probability is the model's CONFIDENCE, not a calibrated truth...
```

## Read it correctly

| Question | Tool |
|---|---|
| Was this *written* by AI? (style) | this agent |
| Is this document *genuine/tampered*? (forensics) | [AI Document Authenticity Agent](../ai_document_authenticity_agent/) |

A human can write generically; an AI can write plainly. One triage signal, never a verdict.

## How it works

Uses the Stipple REST API (`POST /v1/detect-ai-text`) via the `stipple.py` client (stdlib-only). The same capability is available in any MCP client via `https://www.stipple.sh/mcp`. More kits: [stipple-kits](https://github.com/Sketchjar/stipple-kits).
