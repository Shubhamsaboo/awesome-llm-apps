## 🧪 Eval-First RAG

Most RAG demos stop at **retrieve → generate**. This one adds the layer that actually matters in production: after every answer it runs an **evaluation pass** that scores retrieval confidence and answer groundedness, then flags the failure mode standard RAG silently ships — a **confident answer the retrieved context does not support** (a "confident hallucination").

This Streamlit app runs locally with only an OpenAI API key. Paste in any document — a 10-K excerpt, a report, meeting notes — and ask questions against it.

### Features

- **Answer + self-evaluation**: every response comes with a groundedness score and a verdict
- **Three verdicts**: `grounded`, `honest_refusal` (correctly declines when the answer isn't in context), and `confident_hallucination` (the dangerous case — flagged in red)
- **Retrieval confidence**: top cosine-similarity score, surfaced alongside the answer
- **LLM-as-judge**: a strict evaluator scores support-by-context, not fluent wording
- **Audit any answer**: paste any answer to score it against the retrieved context — a deterministic way to watch the evaluator catch a wrong claim
- **Strict / Loose grounding toggle**: Strict answers from context only; Loose lets the model answer freely so you can see ungrounded answers get flagged
- **Bring your own document**: no bundled data — paste any text and query it
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

4. Add your OpenAI API key (sidebar, or a local `.env` with `OPENAI_API_KEY=...`), paste a document in the sidebar, then see each verdict:

   - **Grounded** — ask something your document answers → the answer comes back with a high groundedness score.
   - **Honest refusal** — ask something *not* in your document → in Strict mode the model replies "Not found in context," scored as a correct refusal.
   - **Confident hallucination** — switch to Loose mode (the model may answer from memory), or use **Audit an answer** to paste a claim your document contradicts → the evaluator flags it in red with groundedness ~0.

> Note: modern aligned models often *refuse* rather than hallucinate on clean factual questions (a good thing) — Strict mode shows that. Loose mode and the answer-audit make the ungrounded-answer failure reproducible so you can watch the evaluator catch it deterministically.
