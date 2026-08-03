# OpenAI Remote MCP Tool Bridge

Learn how to connect a plain OpenAI function-calling loop to a hosted Streamable HTTP MCP server—without an agent framework.

The script keeps the complete bridge visible:

1. Open a remote Streamable HTTP connection.
2. Discover every MCP tool with paginated `list_tools()` calls.
3. Convert MCP names, descriptions, and input schemas to OpenAI function tools.
4. Let the model decide whether to request a tool.
5. Dispatch that request through the live MCP session.
6. Return a bounded, model-safe result for the matching tool call.
7. Repeat until the model answers or the tool-call budget is reached.

## Setup

Use Python 3.11 or newer:

```bash
pip install -r requirements.txt
export OPENAI_API_KEY="your-openai-api-key"
```

The default server is Parallel Search MCP at `https://search.parallel.ai/mcp`, a runnable hosted endpoint that exposes read-only tools without MCP authentication.

## Discover tools without OpenAI

`--list-tools` connects to the server and prints its live tool names and descriptions. It does not require `OPENAI_API_KEY`.

```bash
env -u OPENAI_API_KEY python openai_remote_mcp_bridge.py --list-tools
```

## Run the bridge

Use a task that needs fresh information so the model has a natural reason to call a remote tool:

```bash
python openai_remote_mcp_bridge.py \
  "Read https://news.ycombinator.com/ now. What is the title and destination URL of the number-one story?"
```

The trace shows `[connect]`, `[discover]`, `[convert]`, each OpenAI-to-MCP request, each MCP-to-OpenAI result, and `[final]`.

By default, the model receives every compatible tool discovered on the trusted server. To expose only a subset, copy names from `--list-tools`:

```bash
python openai_remote_mcp_bridge.py \
  --tools tool_name_one,tool_name_two \
  "Complete a task that needs those tools."
```

You can also change the model, server, or total requested-call budget:

```bash
python openai_remote_mcp_bridge.py \
  --server-url https://your-trusted-server.example/mcp \
  --model gpt-4o-mini \
  --max-tool-calls 3 \
  "Complete a task with current information."
```

`MCP_SERVER_URL` and `OPENAI_MODEL` provide environment-variable defaults for the corresponding flags.

## What the conversion does

For each exposed MCP tool, the bridge maps:

```text
MCP tool.name        -> OpenAI function.name
MCP tool.description -> OpenAI function.description
MCP tool.inputSchema -> OpenAI function.parameters
```

OpenAI function names must contain 1–64 letters, numbers, underscores, or hyphens. The MCP input schema must describe a top-level JSON object. The bridge fails early with the incompatible tool's name instead of silently changing its contract.

Tool results prefer MCP `structuredContent`. Otherwise, text blocks are joined; image, audio, and other non-text payloads are replaced with compact markers. Oversized output is truncated before it enters model context.

Every requested tool call counts toward `--max-tool-calls`, including malformed, unknown, failed, and skipped requests. Every request receives a matching tool response, and the model gets one final no-tools turn when the budget is exhausted.

## Scope and safety

This tutorial intentionally supports one trusted, unauthenticated, read-only Streamable HTTP MCP server. Inspect a server with `--list-tools` before exposing it to the model.

Production concerns that are deliberately outside this example include OAuth, write-tool approval, multiple-server routing, MCP resources and prompts, and universal JSON Schema conversion. Add those policies for your application rather than treating `--tools` as an authorization boundary.

## Troubleshooting

- `OPENAI_API_KEY is required`: export a key, or use `--list-tools` to test MCP without OpenAI.
- `Unknown MCP tool`: run `--list-tools` against the same `--server-url` and update `--tools`.
- `not a valid OpenAI function name` or `must have an object input schema`: the selected server exposes a tool that cannot be represented directly as an OpenAI function tool.
- `Bridge failed`: verify the server uses Streamable HTTP, is reachable without MCP authentication, and is intended for read-only use.
