# Progressive PDF RAG & Deterministic Verifier

A self-contained example demonstrating **no-vector-DB long-PDF navigation** and **deterministic claim verification** using standard PyPI libraries (`pymupdf`, `streamlit`, `openai`).

Instead of chunking an entire PDF into a vector store and trusting an LLM's mental math or citations, this app separates **progressive reading** from **deterministic verification**:

1. **Zero-LLM Structural Indexing (`pdf_navigator.py`)**
   - Extracts embedded PDF bookmarks (with a font-size heading heuristic fallback when bookmarks are missing).
   - Builds an in-memory BM25 lexical index over pages (supports English and CJK text).
2. **Token-Bounded Progressive Navigation (`agent.py`)**
   - `get_outline` → inspect section titles and page ranges first without loading body text.
   - `search_pages` → rank candidate pages with short snippets.
   - `read_pages` → load only the exact pages needed under a strict character budget.
3. **Deterministic Claim Verification (`claim_verifier.py`)**
   - **Verbatim quote check**: normalizes PDF line-wrap hyphens, smart quotes, and whitespace; catches wrong-page citations by checking if the quote actually lives on another page.
   - **Numeric check**: parses currency symbols, commas, percentages, parenthesized negatives like `(6.0)`, and page-level scale headers like `($ in millions)`.
   - **Safe AST formula recomputation**: verifies every operand on its cited source page first, then recomputes the arithmetic expression via Python's `ast` module (no `eval()` / `exec()`) to catch both hallucinated inputs and arithmetic errors.

## Setup

Use Python 3.11 or newer:

```bash
pip install -r requirements.txt
```

## Run the Streamlit App

```bash
streamlit run app.py
```

- **Tab 2 (Zero-API-Key Explorer & Verifier)** works completely offline right away using the built-in 4-page sample financial report (`Acme Robotics FY2025 Annual Report`) or any PDF you upload.
- **Tab 1 (Ask & Verify Agent)** works with OpenAI or any OpenAI-compatible endpoint (OpenRouter, Ollama, DeepSeek, etc.) by entering an API key (and optional Base URL) in the sidebar.

## Run from the CLI

Run the offline progressive navigation + verification demo (no API key required):

```bash
python agent.py --demo-verify
```

Or run the full LLM agent on the built-in sample PDF (or your own `--pdf path/to/file.pdf`):

```bash
export OPENAI_API_KEY="your-openai-api-key"
python agent.py --sample \
  --question "What was FY2025 gross margin and the maximum Net Debt/EBITDA covenant?"
```

## Run the Unit Tests

```bash
pytest test_verifier.py
```

All tests run offline without an API key and verify bookmark/font-heuristic outlines, BM25 retrieval, verbatim quote & wrong-page detection, scaled/negative number verification, AST safety guards, formula checks, and hardened agent error handling.

---

*Inspired by the progressive navigation and deterministic verification architecture of [AnchorDoc](https://github.com/ryanvii/AnchorDoc).*
