# Evals

Manual evaluations for the mcp-builder skill.

## Format

Each eval file is a JSON array:

```json
[
  {
    "query": "User input to test",
    "expected_behavior": "OUTCOME. What the response should do."
  }
]
```

## Running Evals

In Claude Code:

```
Run the evals in evals/<reference>.json. For each query, spawn a Sonnet agent with the mcp-builder skill context and compare the response against expected_behavior. Report pass/fail for each.
```
