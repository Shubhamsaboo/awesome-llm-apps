"""
Standalone verifier — proves the demo actually calls an LLM.

Run this with your own API key to capture a real round-trip:

    export ANTHROPIC_API_KEY=sk-ant-...
    python verify.py

    # or with OpenAI:
    export OPENAI_API_KEY=sk-...
    python verify.py --provider openai

Output is plain text suitable for pasting into the README's
"Sample real run" section to prove the integration works end-to-end.

The script makes ONE real API call (raw context) and ONE more (compressed
context), then prints the captured response.usage numbers from the
provider's SDK. No Streamlit, no UI — just the bare LLM round-trip.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

from entroly import compress


# ── Fixed sample input so anyone re-running gets comparable numbers ──

SAMPLE_DOC = """\
Release notes for v1.7.0
========================

Added: support for streaming responses from the /chat endpoint. Clients
that pass `stream=true` will receive SSE chunks instead of a single JSON
body. The chunk format matches OpenAI's Chat Completions streaming
schema. Token usage is reported in the final chunk's `usage` field.

Added: rate limiting per API key. The default tier is 60 requests per
minute. Enterprise plans get 600 requests per minute. Exceeded limits
return HTTP 429 with a `Retry-After` header indicating when to retry.

Fixed: a long-standing bug where multi-byte UTF-8 characters at chunk
boundaries during streaming would split mid-codepoint, occasionally
producing invalid JSON when clients tried to parse partial output.
Streaming now buffers until a codepoint boundary is reached.

Fixed: the `/auth/refresh` endpoint was logging the refresh token in
debug mode, which leaked credentials into stdout when DEBUG=1. Refresh
tokens are now redacted in all log paths.

Changed: the default temperature is now 0.7 (was 1.0). Users who relied
on the previous default should pass `temperature=1.0` explicitly.

Deprecated: the /v0/embeddings endpoint. It will be removed in v2.0.
Use /v1/embeddings instead. The schema is identical; only the path
changed.

Security: CVE-2026-0042 — a path traversal vulnerability in the file
upload handler allowed unauthenticated users to read files outside the
upload directory. The handler now canonicalises the upload path before
writing.

Performance: the cold-start time for the worker process dropped from
4.2 s to 1.1 s after we lazy-load the embedding model. Memory usage at
idle dropped from 1.2 GB to 280 MB.
"""

SAMPLE_QUESTION = "What security issue was fixed in v1.7.0?"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider",
        choices=["anthropic", "openai"],
        default="anthropic",
        help="LLM provider to verify against (default: anthropic)",
    )
    parser.add_argument(
        "--budget", type=int, default=200,
        help="Token budget for compressed context (default: 200)",
    )
    args = parser.parse_args()

    # Compress
    t0 = time.perf_counter()
    compressed = compress(SAMPLE_DOC, budget=args.budget)
    compress_ms = (time.perf_counter() - t0) * 1000

    print("=" * 70)
    print("LLM INTEGRATION VERIFICATION")
    print("=" * 70)
    print(f"Provider:     {args.provider}")
    print(f"Sample doc:   {len(SAMPLE_DOC):,} chars (~{len(SAMPLE_DOC)//4:,} tokens)")
    print(f"Question:     {SAMPLE_QUESTION!r}")
    print(f"Compressed:   {len(compressed):,} chars (~{len(compressed)//4:,} tokens) in {compress_ms:.0f} ms")
    print()

    if args.provider == "anthropic":
        result_raw, result_cmp = _run_anthropic(SAMPLE_DOC, compressed, SAMPLE_QUESTION)
    else:
        result_raw, result_cmp = _run_openai(SAMPLE_DOC, compressed, SAMPLE_QUESTION)

    print("-" * 70)
    print("RAW CONTEXT")
    print("-" * 70)
    print(f"  input_tokens:  {result_raw['input_tokens']}")
    print(f"  output_tokens: {result_raw['output_tokens']}")
    print(f"  latency_ms:    {result_raw['latency_ms']:.0f}")
    print(f"  answer:        {result_raw['answer'][:200]}...")
    print()
    print("-" * 70)
    print("COMPRESSED CONTEXT")
    print("-" * 70)
    print(f"  input_tokens:  {result_cmp['input_tokens']}")
    print(f"  output_tokens: {result_cmp['output_tokens']}")
    print(f"  latency_ms:    {result_cmp['latency_ms']:.0f}")
    print(f"  answer:        {result_cmp['answer'][:200]}...")
    print()
    print("-" * 70)
    print("DELTA")
    print("-" * 70)
    saved_tokens = result_raw["input_tokens"] - result_cmp["input_tokens"]
    saved_pct = (saved_tokens / max(result_raw["input_tokens"], 1)) * 100
    saved_ms = result_raw["latency_ms"] - result_cmp["latency_ms"]
    print(f"  tokens saved:  {saved_tokens:,} ({saved_pct:.1f}% reduction)")
    print(f"  latency saved: {saved_ms:+.0f} ms")
    print("=" * 70)
    print("[OK] LLM call verified end-to-end. response.usage was real, not synthetic.")
    return 0


def _run_anthropic(raw_ctx: str, cmp_ctx: str, question: str):
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("error: set ANTHROPIC_API_KEY first", file=sys.stderr)
        sys.exit(2)
    try:
        import anthropic
    except ImportError:
        print("error: pip install anthropic", file=sys.stderr)
        sys.exit(2)
    client = anthropic.Anthropic()
    return _call_anthropic(client, raw_ctx, question), _call_anthropic(client, cmp_ctx, question)


def _call_anthropic(client, ctx: str, question: str) -> dict:
    t0 = time.perf_counter()
    msg = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"Use the following context to answer the question.\n\nCONTEXT:\n{ctx}\n\nQUESTION: {question}",
        }],
    )
    return {
        "answer": msg.content[0].text,
        "input_tokens": msg.usage.input_tokens,
        "output_tokens": msg.usage.output_tokens,
        "latency_ms": (time.perf_counter() - t0) * 1000,
    }


def _run_openai(raw_ctx: str, cmp_ctx: str, question: str):
    if not os.environ.get("OPENAI_API_KEY"):
        print("error: set OPENAI_API_KEY first", file=sys.stderr)
        sys.exit(2)
    try:
        import openai
    except ImportError:
        print("error: pip install openai", file=sys.stderr)
        sys.exit(2)
    client = openai.OpenAI()
    return _call_openai(client, raw_ctx, question), _call_openai(client, cmp_ctx, question)


def _call_openai(client, ctx: str, question: str) -> dict:
    t0 = time.perf_counter()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"Use the following context to answer the question.\n\nCONTEXT:\n{ctx}\n\nQUESTION: {question}",
        }],
    )
    return {
        "answer": resp.choices[0].message.content,
        "input_tokens": resp.usage.prompt_tokens,
        "output_tokens": resp.usage.completion_tokens,
        "latency_ms": (time.perf_counter() - t0) * 1000,
    }


if __name__ == "__main__":
    sys.exit(main())
