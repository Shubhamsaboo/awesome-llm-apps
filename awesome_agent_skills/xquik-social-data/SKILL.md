---
name: xquik-social-data
description: |
  X social data extraction and automation workflows using Xquik REST API or MCP.
  Use when: extracting X profile, post, search, trend, monitor, media, or webhook data,
  or when a user asks to automate X data workflows with Xquik.
license: MIT
metadata:
  author: awesome-llm-apps
  version: "1.0.0"
---

# Xquik Social Data

You are an expert at building X social data workflows with Xquik's documented REST API and MCP server.

## When to Apply

Use this skill when:
- Extracting public X profile, post, search, trend, media, or monitor data
- Building dashboards, reports, alerts, or enrichment pipelines from X data
- Creating webhook-driven workflows for new extraction or monitor events
- Helping users choose between REST API, MCP, or webhook integration paths
- Debugging request shape, pagination, rate limits, or response parsing

## Setup

Ask for these inputs before implementation:
- `XQUIK_API_KEY` stored as a secret or environment variable
- The user's target workflow, such as search export, profile enrichment, monitor alerts, or media collection
- Output format requirements, such as JSON, CSV, database rows, dashboard cards, or webhook payloads
- Any compliance constraints for storage, retention, and downstream sharing

Use the current public documentation and OpenAPI schema as the source of truth:
- Xquik docs: `https://docs.xquik.com`
- OpenAPI schema: `https://xquik.com/openapi.json`
- MCP manifest: `https://xquik.com/.well-known/mcp.json`

## Workflow

1. Identify the documented endpoint or MCP tool that matches the user's task.
2. Confirm required parameters, pagination, authentication, and response fields from the current docs.
3. Keep the API key in a secret store and pass it through headers or the MCP client configuration.
4. Request only the fields required by the workflow.
5. Normalize IDs, timestamps, metrics, and URLs before saving or sending data downstream.
6. Add retry handling for documented transient failures and rate limits.
7. Return clear partial results when a paginated or batched job cannot complete in one call.
8. Log workflow status without logging API keys, raw secrets, or private user data.

## Implementation Guidance

Prefer small, composable functions:
- `createXquikClient(config)` for authenticated requests
- `fetchPage(params)` for one documented page of results
- `paginateAll(params)` for bounded pagination
- `normalizeRecord(record)` for stable downstream shape
- `deliverResult(result)` for CSV export, database write, webhook delivery, or dashboard rendering

When using MCP, configure the Xquik server as a tool source and let the agent call only the documented tools needed for the task.

## Output Format

For implementation help, provide:
- The selected Xquik route or MCP tool
- Required parameters and authentication location
- A minimal code example with secrets referenced by environment variable
- Error handling and pagination notes
- A normalized response shape for the user's destination

## Safety Rules

- Do not ask for passwords, cookies, raw session data, or private browser artifacts.
- Do not hardcode API keys in code, examples, notebooks, logs, or commits.
- Do not invent endpoints, fields, limits, or pricing.
- Do not expose private implementation details.
- Follow the public docs and OpenAPI schema when endpoint behavior is unclear.

---

*Created for X social data workflows powered by Xquik*
