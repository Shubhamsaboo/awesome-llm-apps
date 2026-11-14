# Read-only Browser Agent with OpenAI Agents SDK and AdsCrawl MCP

Ask a question about one public, browser-rendered page from a Python CLI. The OpenAI Agents SDK discovers AdsCrawl's hosted MCP tools, opens one browser session, reads the page, and explicitly closes the session before returning an answer.

This is a small SDK/MCP integration example, not a crawler, login agent, production session manager, or OpenAI-maintained integration.

## How it works

- The Python application connects to `https://api.adscrawl.net/mcp` using Streamable HTTP and an `x-api-key` header.
- `MCPServerStreamableHttp` lists the server's actual tool schemas. The example does not guess tool arguments.
- A tool allowlist exposes only `browser_open`, `browser_navigate`, `browser_read`, and `browser_close`. Screenshot, click, and form tools are not exposed.
- A small server subclass permits only one open attempt and checks the actual `browser_close` result for a literal `confirmed: true`. A model's final prose is not accepted as proof of shutdown.

The MCP connection is client-side: the application sends the AdsCrawl header to AdsCrawl. The OpenAI model receives the task and tool results, not an API key placed in the prompt.

## Requirements and costs

Use Python 3.11 or newer, an OpenAI API key with access to a tool-capable model, and an AdsCrawl account/API key. This example was checked offline with Python 3.12.3, `openai-agents==0.24.0`, and `mcp==2.3.0`.

The source code is free and open source. Running it can incur OpenAI API charges and consumes AdsCrawl account credits. Browser sessions share the API key's service and concurrency limits. A target website can still require login or deny access; this example does not promise to bypass access controls.

## Run

From the repository root:

```bash
cd mcp_ai_agents/openai_agents_adscrawl_mcp
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
```

Replace the two placeholder values in the local `.env` file with your own keys. Do not commit `.env`, paste keys into prompts, or put them in a URL. The included `.gitignore` excludes local keys and virtual environments. Existing environment variables take precedence over `.env`.

```bash
python main.py
```

The default target is `https://example.com`. The page heading is normally `Example Domain`. After a successful read and verified close, the program prints the answer, source URL, and:

```text
Browser shutdown confirmed: true
```

You can ask about a different public page you are authorized to access:

```bash
python main.py --url https://example.com --question "What is this page for?"
```

Set `OPENAI_MODEL` if you want to select a model available to your OpenAI project. If it is unset, the Agents SDK's default model is used.

## Session cleanup is explicit

`browser_open` creates a remote browser session. Exiting the Python context manager closes the MCP transport; it does **not** prove that the remote browser stopped. The agent is instructed to call `browser_close`, and the program checks that tool's real response for `confirmed: true`.

If a run fails, times out, is cancelled, or the process is killed before a confirmed close, the remote session may still be active. Explicitly close that session with `browser_close` and verify confirmation before retrying. The demo does not persist session identifiers or guarantee cleanup after a crash. Automatic tool retries and a second `browser_open` are disabled to reduce accidental duplicate sessions.

## Privacy and limitations

This example is read-only and does not expose screenshot or form-action tools. AdsCrawl's `browser_screenshot` creates a publicly accessible JPEG link, so it is intentionally excluded. Treat page text as untrusted input, review answers, and use only pages you may access.

Agents SDK tracing is disabled by the example. This disables that SDK tracing feature, not the model request itself: the question and returned page content are still processed by the configured OpenAI model. Raw transport exceptions and tool payloads are not printed because they may contain sensitive URLs. The URL checks are basic input validation, not a production DNS/SSRF security policy.

## Offline checks

```bash
python -m unittest -v
python main.py --help
```

The tests use synthetic results and mocked transport calls. They check environment handling, the tool allowlist, one-open enforcement, and close-confirmation parsing. They do not call OpenAI, create an AdsCrawl session, or establish a live end-to-end success claim. To perform a live test, supply your own authorized keys and review service usage and shutdown confirmation.

## References

- [AdsCrawl MCP integration guide](https://www.adscrawl.net/integrations/mcp/)
- [Existing AdsCrawl entry in the official MCP Registry](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.AdsCrawl%2Fads-crawl/versions/latest)
- [OpenAI Agents SDK MCP documentation](https://openai.github.io/openai-agents-python/mcp/)

Contributed by AdsCrawl, the provider of one of the external services used here. This example is not an OpenAI endorsement or an official OpenAI integration listing.
