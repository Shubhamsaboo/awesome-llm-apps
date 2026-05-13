# Cut your LLM bill 70–95% on long-document Q&A

A Streamlit chat app that demonstrates a **production-grade pattern** for
slashing LLM costs when your users ask questions over long documents
(release notes, source files, RFCs, transcripts, support tickets, etc.).

For the same question against the same model, the app sends two
requests side-by-side and shows you the delta in **measured** numbers
from your own documents and your own provider account:

- **Input tokens** for raw vs. compressed context (from the provider's
  `response.usage`)
- **USD cost** at the model's public list rate
- **Latency** end-to-end per call
- **Answer text** for both, so you can read them and judge whether
  compression cost you any quality

The numbers vary by document and by question — paste your own and the
app shows you what *you* would save. This is not specific to any one
compression library; it's a structural pattern: insert a
context-compression step between your document store and your LLM
call.

## What this app is

- A **Streamlit** chat UI that takes a long document + a question
- Two real LLM calls per question — raw vs. compressed context
- Side-by-side metrics: tokens, cost, latency, full answers
- Three LLM providers: **Anthropic Claude**, **OpenAI GPT**, and **local Ollama**

## What you'll learn

- The **chat-app pattern** for long-document Q&A that scales economically
- How to drop a compression layer into any existing LLM pipeline in
  ~3 lines of code
- Real cost math from real provider APIs — not synthetic benchmarks
- A baseline you can swap the compressor in to compare different
  approaches (LLMLingua, your own extract, etc.)

## Quickstart

```bash
git clone <this repo>
cd llm-cost-comparison
pip install -r requirements.txt

# Pick one — depending on which provider you want to test:
export ANTHROPIC_API_KEY=sk-...
export OPENAI_API_KEY=sk-...
#  …or run Ollama locally:
ollama serve & ollama pull llama3.1:8b

streamlit run entroly_demo.py
```

Then in your browser:

1. Choose a provider + model in the sidebar
2. Paste a long document (or upload a `.txt` / `.md`)
3. Ask any question
4. Hit **Compare** — watch the numbers

## The pattern, in three lines

Drop this into any existing LLM app:

```python
from entroly import compress

compressed = compress(your_long_document, budget=4000)  # ← the only new line
answer = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": f"{compressed}\n\nQ: {question}"}],
)
```

That's the whole change. `compress()` is a pure function that returns a
shorter string carrying the same information density. You don't change
your LLM client, your prompt template, or your downstream handling.

## The contract any compressor must satisfy

A compressor used in this pattern is just a function that returns a
shorter string carrying the same information density as its input:

```python
def compress(text: str, budget: int) -> str: ...
```

The constraints worth respecting are minimal:

- **Pure** — same input, same output. Lets you cache by input hash.
- **No LLM call inside** — the whole point is to avoid an extra paid
  inference. Compression should be deterministic and CPU-bound.
- **Token-budgeted** — the caller passes a target token count and the
  compressor stays at or under it.

Beyond that, the algorithmic choice is up to the compressor. Extractive
summarisation, TF-IDF + greedy selection, embedding-based clustering,
LLM-distilled prompts cached offline — any of them slots in. See the
**Swap the compressor** section below for concrete alternatives the
demo accepts without code changes elsewhere.

## Swap the compressor

The app calls `entroly.compress(text, budget)`. To compare other
compression approaches, replace that one call:

```python
from llmlingua import PromptCompressor              # alternative
compressed = PromptCompressor().compress_prompt(text, target_token=4000)
# OR: your own extractive summariser, or BM25 top-k, etc.
```

The rest of `entroly_demo.py` — the LLM calls, the metrics, the UI —
doesn't depend on which compressor you use. That's the architecture
this demo is teaching.

## When this pattern is worth using

Use case fits if **any** of these is true for your app:

- Average context > 4,000 tokens per request
- You make many requests against similar source material (FAQ over docs,
  helpdesk over knowledge base, agentic loops re-reading the same code)
- You're paying for a frontier model on every call and the bill is
  growing faster than your usage

Skip if:

- Your context is already short (< 2,000 tokens)
- You need the **exact** wording of the source preserved (legal,
  compliance, copy-paste use cases)

## Files

| File | Purpose |
|------|---------|
| [`entroly_demo.py`](entroly_demo.py) | Streamlit app (~270 lines, single file) |
| [`requirements.txt`](requirements.txt) | Pinned deps |
| `README.md`         | This file |

## Provider-specific notes

**Anthropic** — Token counts come from `response.usage.input_tokens` /
`output_tokens`. Cost rates: $3 / $15 per million for Sonnet, $0.80 /
$4 for Haiku. Approximate as of mid-2026.

**OpenAI** — Token counts from `response.usage.prompt_tokens` /
`completion_tokens`. Cost rates: $2.50 / $10 per million for gpt-4o,
$0.15 / $0.60 for gpt-4o-mini.

**Ollama** — Local. Token counts from `prompt_eval_count` /
`eval_count`. Cost shown as $0 (electricity not modelled) — useful for
benchmarking compression's *latency* impact on local inference, where
cost is unbounded user time rather than dollars.

## Disclosure

This demo uses [`entroly`](https://github.com/juyterman1000/entroly) as
the compression layer and is authored by entroly's maintainer. The
chat-app pattern is the deliverable — the library is one pluggable
piece. Use `LLMLingua`, your own extractive summariser, or any other
compressor and the demo's wiring is identical.

## License

Same as the repo this lives in. Code is unencumbered for any use.
