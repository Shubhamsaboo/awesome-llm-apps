# Desearch MCP Agent

Research questions with X search through Desearch's hosted Streamable HTTP
MCP server. The agent exposes only the `x-search` tool and cites source URLs.
No local MCP server is needed.

## Setup

From `4_4_mcp_tools`, install the dependencies needed by this example:

```bash
pip install "google-adk>=1.5.0,<2"
export GOOGLE_API_KEY="your-google-api-key"
export GOOGLE_GENAI_USE_VERTEXAI=FALSE
export DESEARCH_API_KEY="your-desearch-api-key"
adk web
```

Select `desearch_agent`, then ask:

> Search X for Python packaging discussions. Return at most 3 posts with links.

`DESEARCH_API_KEY` is required when the agent loads. It is sent in the
`Authorization: Bearer` header to `https://mcp.desearch.ai/mcp`.
Keep keys in your environment and out of source control. Searches use your
Desearch account's quota. A missing or invalid key must be corrected before
searching.

See the [Desearch MCP documentation](https://desearch.ai/docs/guide/sdk/mcp)
for authentication and tool details.
