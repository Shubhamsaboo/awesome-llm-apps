# API Migration Notes

Diff two OpenAPI 3.x JSON documents, then write consumer migration notes that
cover every breaking change. The differ classifies the spec. The notes name
who is affected and show before/after request and response examples. The
checker fails if a breaking id is missing.

## Install

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/api-migration-notes
```

## Run

Ask the agent:

> Write consumer migration notes for these two OpenAPI documents.

Or run the deterministic core directly:

```bash
python3 scripts/oas_diff.py old.json new.json > changes.json
python3 scripts/check_notes.py notes.md changes.json
```

JSON input only. Convert YAML with `yq -o=json spec.yaml > spec.json` first.
The scripts use only the Python standard library and make no network calls.
