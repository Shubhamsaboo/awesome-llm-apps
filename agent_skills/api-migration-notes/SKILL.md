---
name: api-migration-notes
description: >-
  Turns two OpenAPI 3.x JSON documents into consumer migration notes that cover
  every breaking API change. A deterministic differ classifies removed paths and
  operations, removed or renamed response fields, newly required request fields,
  type format and enum narrowing, parameter location changes, auth scheme
  changes, and removed status codes versus additive optional fields, new
  endpoints, and enum widening. A checker fails if any breaking change id is
  missing from the notes. Use when the user asks for OpenAPI, OAS, or swagger
  spec migration notes, consumer changelog coverage for a breaking API change,
  request and response examples for each spec diff, or to verify notes address
  every breaking change.
license: Apache-2.0
metadata:
  author: "Matt Van Horn"
  version: "1.0.0"
  source: "https://github.com/Shubhamsaboo/awesome-llm-apps"
---

# API Migration Notes

When an HTTP API changes, consumers need notes that name every breaking change.
This skill diffs two OpenAPI 3.x JSON documents with a deterministic script,
writes consumer-facing notes from that JSON, and refuses to ship notes that
miss a breaking change id.

Everything runs locally. The scripts make no network calls.

## When to use

- The user has two OpenAPI / OAS / swagger 3.x documents and wants migration notes
- The user asks which breaking API changes consumers must handle
- The user wants request and response examples for each spec change
- The user wants a checker to prove the notes cover every breaking change

## When not to use

- Rewriting application source for a framework or language migration
- Upgrading package dependencies
- Authoring or linting the OpenAPI document itself
- Diffing YAML until it has been converted to JSON
- GraphQL, gRPC, protobuf, or HAR traffic that is not an OpenAPI 3.x JSON document
- Editing the live API or publishing notes without the user asking

## Convert YAML first

The differ accepts JSON only. If the specs are YAML, convert them before running:

```bash
yq -o=json old.yaml > old.json
yq -o=json new.yaml > new.json
```

## Run the differ

From this skill directory:

```bash
python3 scripts/oas_diff.py old.json new.json > changes.json
```

Read the JSON. Every record has `id`, `kind`, `severity`, `old_pointer`,
`new_pointer`, `summary`, and `details`. Breaking ids are `BRK-###`. Additive
ids are `ADD-###`. Deprecations are `DEP-###`.

Read [references/classification.md](references/classification.md) before writing
prose. Trust the classifier for what changed; do not drop a breaking record
because it looks minor.

## Write the notes

Follow [references/notes-template.md](references/notes-template.md). For every
breaking record, write a `##` section that includes the id (`[BRK-003]` or
`<!-- change: BRK-003 -->`) and:

1. Who is affected
2. What breaks
3. A Before request or response example
4. An After request or response example
5. The exact change a client must make

Use the pointers and summaries from the JSON. Inventing a change that has no
id, or skipping an id, fails the checker.

## Run the checker

```bash
python3 scripts/check_notes.py notes.md changes.json
```

Exit codes:

- `0`: every breaking id is covered, no unknown ids, every breaking section has before/after examples
- `1`: uncovered ids, unknown ids, or missing examples (stderr/stdout lists them)
- `2`: usage or input error

If the checker fails, fix the notes and rerun it. Do not tell the user the notes
are complete until exit code 0.

## Files

- `scripts/oas_diff.py`: OpenAPI 3.x JSON differ with local `$ref` resolution
- `scripts/check_notes.py`: coverage checker for the notes Markdown
- `references/classification.md`: breaking vs additive vs deprecation rules
- `references/notes-template.md`: required notes shape
