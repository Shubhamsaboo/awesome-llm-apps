## 🧪 Eval-First RAG

Most RAG demos stop at **retrieve → generate**. This one adds the layer that actually matters in production: after every answer it runs an **evaluation pass** that scores retrieval confidence and answer groundedness, then flags the failure mode standard RAG silently ships — a **confident answer the retrieved context does not support** (a "confident hallucination").

This Streamlit app runs locally with only an OpenAI API key. It ships with a small built-in financial document so it works with zero setup, and you can paste in your own.

### Features

- **Answer + self-evaluation**: every response comes with a groundedness score and a verdict
- **Three verdicts**: `grounded`, `honest_refusal` (correctly declines when the answer isn't in context), and `confident_hallucination` (the dangerous case — flagged in red)
- **Retrieval confidence**: top cosine-similarity score, surfaced alongside the answer
- **LLM-as-judge**: a strict evaluator scores support-by-context, not fluent wording
- **Audit any answer**: paste any answer to score it against the retrieved context — a deterministic way to watch the evaluator catch a wrong claim
- **Strict / Loose grounding toggle**: Strict answers from context only; Loose lets the model answer freely so you can see ungrounded answers get flagged
- **Zero-setup corpus**: built-in sample doc with specific numbers so hallucinations are easy to catch; editable to test your own text
- **Minimal stack**: OpenAI embeddings + `gpt-4o-mini` + NumPy cosine search — no vector DB required

### Why it's different

In finance, healthcare, or legal RAG, a confident wrong answer is worse than an honest "I don't know" — but most eval setups score both the same. This app makes that distinction visible in the loop. It's a compact demo of the eval-first pattern behind [finrag-eval](https://github.com/Ruthwik-Data/finrag-eval), where the same approach surfaced a metric bug now merged into DeepEval.

### How to Get Started?

1. Clone the GitHub repository
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/rag_tutorials/eval_first_rag
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the Streamlit app:
```bash
streamlit run eval_first_rag.py
```

4. Add your OpenAI API key (sidebar, or a local `.env` with `OPENAI_API_KEY=...`), then try:

   **Strict mode (context only):**
   - *"What was Apple's FY2024 revenue?"* → ✅ **grounded** ($391.0B)
   - *"How much did Apple spend on marketing in FY2024?"* → ✅ **honest refusal** (not in the summary)

   **Loose mode (answer freely):**
   - *"What was Tesla's FY2024 revenue?"* → ⚠️ **confident hallucination** — the model answers from its own memory, but the answer isn't grounded in the retrieved Apple context, so the evaluator flags it. This is the classic RAG failure: answering from parametric memory instead of the documents.

> Note: modern aligned models often *refuse* rather than hallucinate on clean factual questions (a good thing) — Strict mode shows that. Loose mode makes the ungrounded-answer failure reproducible so you can see the evaluator catch it.

**Guaranteed demo of the ⚠️ flag** (deterministic, no reliance on model behavior): ask *"What was Apple's FY2024 revenue?"*, then paste this into **"Audit an answer"**:
> `Apple reported FY2024 revenue of $450.0 billion.`

The real figure is $391.0B, so the evaluator flags it as a **confident hallucination** (groundedness 0.0) every time.
