# 🕵️ AI Document Authenticity Agent

Drop any PDF or photo — payslip, invoice, ID, bank statement — and get a forensic authenticity readback: a `risk_band` (how authentic it looks), `inspection_quality` (how completely it could be inspected), and the evidence behind both.

Built on [Stipple](https://www.stipple.sh) — a hosted MCP server for document verification. The free anonymous tier works with **no API key and no signup**.

## Quickstart

```bash
pip install stipple
export STIPPLE_API_KEY=   # optional; anonymous free tier works without it
python agent.py ./payslip.pdf
python agent.py https://example.com/invoice.pdf --deep   # deep inspection
```

## Example Output

```
risk_band:           LOW — Nothing looks tampered.
inspection_quality:  limited
recommended action:  review_before_action

evidence (signals):
  - [pass] Amount words/figure mismatch: Spelled-out amounts agree with figures.
  - [pass] Font discontinuity in value: Numeric values share the font of surrounding text.
  - [skipped] Identifier checksum: No checksummable identifier present; skipped.
```

## How to read results

| Axis | Question it answers |
|---|---|
| `risk_band` | does anything look tampered? |
| `inspection_quality` | could we actually see enough to judge? |

A clean phone photo of a real payslip is commonly `low` + `limited` — low coverage is **not** risk. This is a signal with evidence, not a fraud verdict. Identical files are cached by content hash — re-checking the same bytes is free.

## How it works

Uses the Stipple REST API (`POST /v1/warrants`) via the `stipple.py` client (stdlib-only, copy it anywhere). The same check is available in any MCP client via `https://www.stipple.sh/mcp` — see the [stipple-kits](https://github.com/Sketchjar/stipple-kits) collection for 12+ more kits (tender search, 100-point ID checks, adverse media screening, fact-checking).
