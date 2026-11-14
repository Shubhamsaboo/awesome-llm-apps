# LangChain page Q&A with AdsCrawl

A small evidence Q&A pipeline: read up to five user-supplied public URLs through [AdsCrawl](https://www.adscrawl.net) using `AdsCrawlReadTool.ainvoke()`, then answer a question using LangChain's `ChatPromptTemplate` and `ChatOpenAI.with_structured_output()`.

It is deliberately not an autonomous crawler: exact duplicate URLs are removed, pages are read sequentially with at most one attempt each, and the model cannot choose more URLs or follow links. This is a rendered-page tool integration, not an MCP session or CDP example.

Maintained/submitted by AdsCrawl. This is a **community example**, not a LangChain-maintained integration, official catalog listing or endorsement by LangChain/OpenAI. It has not been run end-to-end against live services in this submission.

## Install

Use Python 3.11+ and Git in a separate environment (required by LangChain Core 1.8):

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The `langchain-adscrawl` dependency is pinned to a reviewed GitHub source commit. The package is source-distributed, not yet published to PyPI. Its [source and maintenance guide](https://github.com/AdsCrawl/langchain-adscrawl) follow LangChain's standalone integration approach.

## Run

Export your own keys; `.env` is not loaded automatically:

```bash
export ADSCRAWL_API_KEY="YOUR_ADSCRAWL_API_KEY"
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
python main.py \
  --url https://example.com \
  --content-mode html \
  --question "What is the purpose of this page?" \
  --model YOUR_CURRENT_OPENAI_MODEL
```

Replace the placeholder keys and model name first. Choose a currently available OpenAI model with structured-output support; there is no hard-coded model default. Configuration and all URL inputs are checked before the first fetch. The program makes no automatic AdsCrawl or model retry.

To use the tool without a model or an OpenAI key:

```bash
python main.py --url https://example.com --content-mode html --fetch-only
```

`--fetch-only` still makes real AdsCrawl requests. Add more explicit pages by repeating `--url` (up to five unique URLs).

## Content and answer limits

`markdown` is the default for article-like sources. AdsCrawl's `markdown` and `json` modes use Readability and can return HTTP 422 when no article is found. For general pages, explicitly choose `--content-mode html`; there is no automatic fallback or hidden second request. See the [official API contract](https://docs.adscrawl.net/api-reference/html).

Each source is truncated to `--max-chars` (default 12,000) before model input; a marker makes that truncation explicit. The output is an answer, a `sufficient_evidence` flag and source citations. Answers claiming sufficient evidence must include a citation, and citation URLs must come from the fetched source set. **The code checks source membership, not whether every generated statement or quotation is true.**

Pages are untrusted data. The system prompt says not to obey page instructions, but this is not a complete prompt-injection or hallucination defense. Review the answer and original sources before relying on it.

## Costs and privacy

The source code is free; using AdsCrawl and the selected OpenAI model can consume credits or incur API charges. Each attempted URL read may use service credits, including a failed or timed-out attempt. A local cancellation does not prove a remote task stopped.

The URL/configuration goes to AdsCrawl. In Q&A mode, the question and bounded page excerpts go to OpenAI; `--fetch-only` does not send them to a model. Your application tracing/callbacks may also record URLs and content. Avoid sensitive URLs or data unless you have reviewed provider and tracing policies. Errors print only sanitized categories, not raw provider responses or tracebacks.

## Offline validation

```bash
python -m pytest --disable-socket --allow-unix-socket -q
python main.py --help
```

Tests use synthetic keys and mocked readers/model outputs, with network sockets disabled. They cover de-duplication, URL limits, preflight failures, truncation, citation boundaries, no automatic retries, sanitized errors and a mocked pipeline. They do **not** establish live authentication, page availability, real extraction quality or model compatibility. The underlying tool package separately includes the applicable LangChain standard unit tests.
