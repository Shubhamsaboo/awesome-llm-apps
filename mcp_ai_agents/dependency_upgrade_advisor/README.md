# 📦 Dependency Upgrade Advisor

A Streamlit app that tells you what an upgrade will break before you run it. Paste a `requirements.txt` or `package.json`, tick the packages you want to upgrade, and get a short report per package: what changes between your version and the target, what to change in your code, and how to check it.

One agent does the work, built with the [Strands Agents SDK](https://strandsagents.com), and it reads two public MCP servers:

| MCP server | Used for | Needs |
|---|---|---|
| [Context7](https://context7.com) (`https://mcp.context7.com/mcp`) | Up-to-date library documentation, migration guides and code examples | No account. Anonymous use has lower rate limits; Context7 offers a free API key for higher ones |
| [DeepWiki](https://docs.devin.ai/work-with-devin/deepwiki-mcp) (`https://mcp.deepwiki.com/mcp`) | Questions answered from a public GitHub repository's code and docs | No account |

## What the report contains

For each package:

- **Verdict:** Safe, Needs changes or Risky, with the exact versions compared.
- **What breaks:** renames, removals and behavior changes, each with its source.
- **What to change:** short code snippets when the sources have them.
- **How to check:** a test, a command or a warning to look for.

The agent is told to report only what the tools returned and to say which part of the version range the sources do not cover.

## Setup

You need Python 3.10+ and an OpenAI API key. No other account or token is needed.

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...        # or type it in the sidebar
streamlit run dependency_upgrade_advisor.py
```

Then:

1. Paste your dependency file (a sample is pre-filled).
2. In the table, tick the packages and set **Target** to a version number or `latest`. Keep it to a few packages per run: each one is a separate agent run with several tool calls.
3. Click **Check upgrades**.

## How it works

```
 dependency file ──> parse_dependencies() ──> table ──> one Agent run per ticked package
                                                          │
                                         ┌────────────────┴────────────────┐
                                    Context7 MCP                      DeepWiki MCP
                          (resolve-library-id, query-docs)        (ask_wiki_question)
```

- `parse_dependencies()` reads `requirements.txt` (pins and ranges, skipping comments, `-r`, `-e` and URLs) and `package.json` (`dependencies` and `devDependencies`).
- `build_agent()` returns a plain Strands `Agent` that holds both MCP clients. Strands opens and closes the MCP connections; the app calls `agent.cleanup()` at the end.
- `tool_filters` allow-list only the read-only tools of each server.
- Each package starts from a clean conversation (`agent.messages.clear()`), and the expander title shows which tools were used.

## Adapt it

- **Use another model provider:** `build_model()` is the only place that picks the provider. Return a different Strands model, for example `AnthropicModel(model_id=...)` from `strands.models.anthropic` (install `strands-agents[anthropic]`), and update the sidebar label.
- **Add a source:** add a function that returns an `MCPClient` (for example a package-registry or changelog MCP server), add it to `tools=[...]` in `build_agent()`, and mention it in `SYSTEM_PROMPT`.
- **Change the report:** edit the sections at the end of `SYSTEM_PROMPT`.

## Limits

- The report is only as good as the sources. Context7 and DeepWiki can lag behind the newest release, and DeepWiki answers are generated from a repository index. Treat the report as a checklist, then run your tests.
- DeepWiki covers public GitHub repositories only.
- The app does not read your code, so it cannot tell which breaking changes actually affect you. The **How to check** section tells you what to search for.
