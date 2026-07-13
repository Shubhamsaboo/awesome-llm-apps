## 🧪 Eval-First RAG

Most RAG demos stop at **retrieve → generate**. This one adds the layer that actually matters in production: after every answer it runs an **evaluation pass** that scores retrieval confidence and answer groundedness, then flags the failure mode standard RAG silently ships — a **confident answer the retrieved context does not support** (a "confident hallucination").

This Streamlit app runs locally with only an OpenAI API key. It ships with a small built-in financial document so it works with zero setup, and you can paste in your own.

### Features

- **Answer + self-evaluation**: every response comes with a groundedness score and a verdict
- **Three verdicts**: `grounded`, `honest_refusal` (correctly declines when the answer isn't in context), and `confident_hallucination` (the dangerous case — flagged in red)
- **Retrieval confidence**: top cosine-similarity score, surfaced alongside the answer
- **LLM-as-judge**: a strict evaluator scores support-by-context, not fluent wording
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

4. Paste your OpenAI API key in the sidebar, then try:
   - *"What was FY2025 revenue?"* → **grounded**
   - *"What was the FY2025 dividend per share?"* → **honest refusal** (the doc says no dividend was declared)
   - *"What is Acme's 2026 revenue guidance?"* → **confident-hallucination trap** (not in the doc)
