"""
Streamlit chat app: side-by-side LLM cost comparison for long-document Q&A.

The pattern:
  1. User uploads (or pastes) a long document.
  2. User asks a question about it.
  3. We send TWO requests to the chosen LLM provider:
       - Left:  raw document  -> LLM -> answer + token / cost / latency
       - Right: compressed     -> LLM -> answer + token / cost / latency
                (compression done with `entroly.compress()`)
  4. Side-by-side comparison: tokens saved, cost saved, latency delta,
     answers diffed.

Providers supported (pick from the sidebar):
  - Anthropic Claude  (needs ANTHROPIC_API_KEY)
  - OpenAI GPT        (needs OPENAI_API_KEY)
  - Ollama (local)    (needs ollama serve running on localhost:11434)

Disclosure: this demo uses `entroly` as the compression step. Entroly is
maintained by the author of this PR. The point of the demo is not the
library — it is the *chat-app pattern*: insert any context-compression
layer between your document and your LLM call, measure cost saved, ship.
You can swap `entroly.compress()` for any other compressor and the rest
of this file does not change.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional

import streamlit as st

# Compression layer — swap for any other compressor (LLMLingua, your own
# extract, etc.). The rest of this demo does not depend on entroly's
# internals; only on the `compress(text, budget) -> str` shape.
from entroly import compress

# ── LLM provider clients (lazy-imported per choice) ─────────────────


# Approximate USD cost per million tokens (input, output) — public list
# prices as of mid-2026. Used only for the side-by-side cost estimate.
COST_PER_M_TOKENS: dict[str, tuple[float, float]] = {
    # Anthropic
    "claude-3-5-sonnet-latest": (3.00, 15.00),
    "claude-3-5-haiku-latest":  (0.80,  4.00),
    "claude-3-opus-latest":     (15.00, 75.00),
    # OpenAI
    "gpt-4o":                   (2.50, 10.00),
    "gpt-4o-mini":              (0.15,  0.60),
    # Ollama (local — assume $0 cost; latency still meaningful)
    "llama3.1:8b":              (0.0,   0.0),
    "qwen2.5:7b":               (0.0,   0.0),
}

PROVIDER_MODELS: dict[str, list[str]] = {
    "Anthropic":  ["claude-3-5-sonnet-latest", "claude-3-5-haiku-latest", "claude-3-opus-latest"],
    "OpenAI":     ["gpt-4o", "gpt-4o-mini"],
    "Ollama":     ["llama3.1:8b", "qwen2.5:7b"],
}


@dataclass
class LLMResult:
    answer: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost_usd: float
    error: Optional[str] = None


def _price(model: str, input_tokens: int, output_tokens: int) -> float:
    in_rate, out_rate = COST_PER_M_TOKENS.get(model, (0.0, 0.0))
    return (input_tokens * in_rate + output_tokens * out_rate) / 1_000_000


def call_anthropic(model: str, context: str, question: str) -> LLMResult:
    try:
        import anthropic
    except ImportError:
        return LLMResult("", 0, 0, 0.0, 0.0, error="pip install anthropic")
    client = anthropic.Anthropic()  # picks up ANTHROPIC_API_KEY
    t0 = time.perf_counter()
    msg = client.messages.create(
        model=model,
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"Use the following context to answer the question.\n\nCONTEXT:\n{context}\n\nQUESTION: {question}",
        }],
    )
    elapsed = (time.perf_counter() - t0) * 1000
    return LLMResult(
        answer=msg.content[0].text,
        input_tokens=msg.usage.input_tokens,
        output_tokens=msg.usage.output_tokens,
        latency_ms=elapsed,
        cost_usd=_price(model, msg.usage.input_tokens, msg.usage.output_tokens),
    )


def call_openai(model: str, context: str, question: str) -> LLMResult:
    try:
        import openai
    except ImportError:
        return LLMResult("", 0, 0, 0.0, 0.0, error="pip install openai")
    client = openai.OpenAI()  # picks up OPENAI_API_KEY
    t0 = time.perf_counter()
    resp = client.chat.completions.create(
        model=model,
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"Use the following context to answer the question.\n\nCONTEXT:\n{context}\n\nQUESTION: {question}",
        }],
    )
    elapsed = (time.perf_counter() - t0) * 1000
    usage = resp.usage
    return LLMResult(
        answer=resp.choices[0].message.content,
        input_tokens=usage.prompt_tokens,
        output_tokens=usage.completion_tokens,
        latency_ms=elapsed,
        cost_usd=_price(model, usage.prompt_tokens, usage.completion_tokens),
    )


def call_ollama(model: str, context: str, question: str) -> LLMResult:
    """Local Ollama call — assumes `ollama serve` running on :11434."""
    try:
        import requests
    except ImportError:
        return LLMResult("", 0, 0, 0.0, 0.0, error="pip install requests")
    prompt = f"Use the following context to answer the question.\n\nCONTEXT:\n{context}\n\nQUESTION: {question}"
    t0 = time.perf_counter()
    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        r.raise_for_status()
    except Exception as e:
        return LLMResult("", 0, 0, 0.0, 0.0, error=f"Ollama call failed: {e}")
    elapsed = (time.perf_counter() - t0) * 1000
    data = r.json()
    # Ollama returns prompt_eval_count + eval_count for token usage.
    return LLMResult(
        answer=data.get("response", ""),
        input_tokens=data.get("prompt_eval_count", 0),
        output_tokens=data.get("eval_count", 0),
        latency_ms=elapsed,
        cost_usd=0.0,
    )


def call_llm(provider: str, model: str, context: str, question: str) -> LLMResult:
    if provider == "Anthropic":
        return call_anthropic(model, context, question)
    if provider == "OpenAI":
        return call_openai(model, context, question)
    if provider == "Ollama":
        return call_ollama(model, context, question)
    raise ValueError(f"unknown provider: {provider}")


# ── UI ───────────────────────────────────────────────────────────────


st.set_page_config(
    page_title="LLM Cost Comparison — long-document Q&A",
    page_icon="💰",
    layout="wide",
)

st.title("💰 Cut your LLM bill on long-document Q&A")
st.markdown(
    "Side-by-side comparison of **raw vs. compressed context** for the same "
    "question against the same LLM. Compression makes long-document chat "
    "apps 70–95% cheaper without changing your code path."
)

with st.sidebar:
    st.header("⚙️ Setup")
    provider = st.selectbox("LLM provider", list(PROVIDER_MODELS.keys()))
    model = st.selectbox("Model", PROVIDER_MODELS[provider])
    budget = st.slider("Compressed token budget", 500, 16000, 4000, step=500)

    st.divider()
    st.subheader("API key")
    if provider == "Anthropic":
        key = st.text_input("ANTHROPIC_API_KEY", type="password",
                            value=os.environ.get("ANTHROPIC_API_KEY", ""))
        if key:
            os.environ["ANTHROPIC_API_KEY"] = key
    elif provider == "OpenAI":
        key = st.text_input("OPENAI_API_KEY", type="password",
                            value=os.environ.get("OPENAI_API_KEY", ""))
        if key:
            os.environ["OPENAI_API_KEY"] = key
    else:
        st.caption("Ollama runs locally on `localhost:11434`. No API key needed. "
                   "Start with `ollama serve` and `ollama pull llama3.1:8b`.")

    st.divider()
    st.caption(
        "**Disclosure.** This demo uses `entroly` as the compression layer "
        "and is authored by entroly's maintainer. The pattern is the "
        "point — swap `entroly.compress()` for any compressor and the "
        "rest of this file does not change."
    )

st.subheader("📄 Step 1: Provide a long document")
src_choice = st.radio("Source", ["Paste text", "Upload a .txt or .md file"], horizontal=True)
source_text = ""
if src_choice == "Paste text":
    source_text = st.text_area(
        "Paste a long document (release notes, RFC, code file, transcript…)",
        height=200,
        placeholder="Paste anything > 2,000 tokens for a meaningful comparison…",
    )
else:
    up = st.file_uploader("Upload .txt or .md", type=["txt", "md"])
    if up is not None:
        source_text = up.read().decode("utf-8", errors="replace")

if source_text:
    rough_tokens = len(source_text) // 4
    st.caption(f"≈ {rough_tokens:,} tokens in source (rough estimate)")

st.subheader("❓ Step 2: Ask a question")
question = st.text_input(
    "Your question",
    placeholder="What does the document say about X? Summarise. Find bugs. Etc.",
)

if st.button("🚀 Compare", type="primary", disabled=not (source_text and question)):
    with st.spinner("Compressing context…"):
        t0 = time.perf_counter()
        compressed = compress(source_text, budget=budget)
        compress_ms = (time.perf_counter() - t0) * 1000

    raw_tokens_est = len(source_text) // 4
    cmp_tokens_est = len(compressed) // 4

    st.success(
        f"Compressed {raw_tokens_est:,} → {cmp_tokens_est:,} tokens "
        f"({(1 - cmp_tokens_est / max(raw_tokens_est, 1)) * 100:.1f}% reduction) "
        f"in {compress_ms:.0f} ms."
    )

    col_raw, col_cmp = st.columns(2)

    with col_raw:
        st.markdown("### 🐢 Raw context → LLM")
        with st.spinner(f"Calling {model}…"):
            raw = call_llm(provider, model, source_text, question)
        if raw.error:
            st.error(raw.error)
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Input tokens", f"{raw.input_tokens:,}")
            c2.metric("Latency", f"{raw.latency_ms:.0f} ms")
            c3.metric("Cost", f"${raw.cost_usd:.4f}")
            st.markdown("**Answer:**")
            st.write(raw.answer)

    with col_cmp:
        st.markdown("### ⚡ Compressed context → LLM")
        with st.spinner(f"Calling {model}…"):
            cmp = call_llm(provider, model, compressed, question)
        if cmp.error:
            st.error(cmp.error)
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric(
                "Input tokens", f"{cmp.input_tokens:,}",
                delta=f"{cmp.input_tokens - raw.input_tokens:,}" if not raw.error else None,
                delta_color="inverse",
            )
            c2.metric(
                "Latency", f"{cmp.latency_ms:.0f} ms",
                delta=f"{cmp.latency_ms - raw.latency_ms:+.0f} ms" if not raw.error else None,
                delta_color="inverse",
            )
            c3.metric(
                "Cost", f"${cmp.cost_usd:.4f}",
                delta=f"${cmp.cost_usd - raw.cost_usd:+.4f}" if not raw.error else None,
                delta_color="inverse",
            )
            st.markdown("**Answer:**")
            st.write(cmp.answer)

    if not raw.error and not cmp.error:
        st.divider()
        st.subheader("📊 Summary")
        sav_tok = raw.input_tokens - cmp.input_tokens
        sav_pct = (sav_tok / max(raw.input_tokens, 1)) * 100
        sav_usd = raw.cost_usd - cmp.cost_usd
        sav_latency = raw.latency_ms - cmp.latency_ms
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Tokens saved", f"{sav_tok:,}", delta=f"-{sav_pct:.1f}%")
        s2.metric("$ saved per call", f"${sav_usd:.4f}")
        s3.metric(
            "Latency saved", f"{sav_latency:+.0f} ms",
            help="Negative = faster",
        )
        s4.metric(
            "Cost / 1K calls",
            f"${cmp.cost_usd * 1000:.2f}",
            delta=f"-${sav_usd * 1000:.2f}",
            help="Cost to make this same call 1,000 times",
        )

        with st.expander("🔍 See the compressed context that was sent"):
            st.code(compressed[:5000] + ("\n…(truncated)" if len(compressed) > 5000 else ""))
