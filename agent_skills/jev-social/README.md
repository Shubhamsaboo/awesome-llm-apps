# Jev Social

Jev chooses a typed social-search route; the local `socai` CLI performs that
read-only search in the user's browser; the script prints compact,
source-linked evidence instead of raw CLI output.

## Requirements

- Python 3.11+
- `OPENROUTER_API_KEY` with Jev access
- A local [`socai`](https://github.com/socai-io/socai) CLI
- An already signed-in local Chrome session when the platform requires one

No Python packages are required.

## Run

From this directory:

```bash
python3 scripts/jev_social.py \
  "Find recent AI creator posts on TikTok" \
  --platform auto \
  --limit 4
```

Jev uses OpenRouter's rolling `~typesafe/jev-latest` alias by default. Set
`OPENROUTER_JEV_MODEL` when a reproducible model pin is required.

The only executable operation the script can construct is:

```text
socai <instagram|tiktok|linkedin> search --num <1..20> --pretty -- <goal>
```

It passes arguments directly to the process, with no shell interpolation. A
request to publish, engage, message, or use another platform routes to
`unsupported` and does not execute `socai`.

## What this demonstrates

- an LLM decision over a typed action space rather than generated shell code;
- an explicit boundary between Jev's choice and browser execution;
- validation of model output before execution;
- compact evidence projection instead of leaking raw browser or CLI state;
- separate Jev and browser timings.

The full [Jev Social](https://github.com/socai-io/jev-social) application adds
an iterative action loop, streamed cards, detail and comment reads, explicit
TikTok media capture, and a cited research report.

## Eval

From the repository root:

```bash
python3 agent_skills/evals/jev-social/test_jev_social.py
```

The eval is offline. It checks route validation, fixed command construction,
result projection, redaction, and failure behavior with a fake `socai`
executable. It never contacts OpenRouter or a social platform.
