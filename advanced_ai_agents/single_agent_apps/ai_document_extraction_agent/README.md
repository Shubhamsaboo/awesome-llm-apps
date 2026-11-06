## 📄 AI Document Extraction Agent

An AI-powered agentic document extraction system that reads any PDF and extracts structured data according to a user-defined JSON Schema. The agent iteratively parses, extracts, and refines its output until every field and every array record is filled — no templates, no per-document tuning.

Based on the approach behind [KYNEX Harness](https://github.com/Nikit117/kynex-harness), which is ranked on the [ExtractBench leaderboard](https://github.com/run-llama/ExtractBench) with **92.97 Overall Value F1** across 370 enterprise documents, verified by LlamaIndex.

### Features

- Schema-guided extraction from any PDF — invoices, reports, forms, filings, contracts
- Iterative agent loop: extracts, reviews, fills gaps, and stops when done or no improvement
- Handles arrays of arbitrary length (line items, records, schedules)
- Null-aware: missing fields are `null`, not invented
- Works with any JSON Schema — define once, extract from any document of that type
- Live progress: see what the agent fills on each iteration

### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/single_agent_apps/ai_document_extraction_agent
```

2. Install the required dependencies

```bash
pip install -r requirements.txt
```

3. Get your OpenAI API Key

- Sign up at [platform.openai.com](https://platform.openai.com) and create an API key
- Recommended model: `gpt-5.4` for best extraction quality

4. Run the Streamlit App

```bash
streamlit run document_extraction_agent.py
```

5. Upload a PDF, paste a JSON Schema (or use the built-in sample invoice schema), and click **Extract**

### How it Works?

The Document Extraction Agent uses an iterative approach inspired by how a human analyst would process a document:

1. **Parse** — Extracts text from every page of the PDF using PyMuPDF

2. **Plan** — Analyzes the JSON Schema to identify all fields and nested structures that need to be filled, including arrays with repeated records

3. **Extract** — Sends the document text and schema to the LLM, which returns a structured JSON object with all values it can find

4. **Iterate** — Reviews the extraction for null fields and empty arrays. If gaps remain, the agent re-reads the document with the partial extraction as context, focusing on what it missed

5. **Converge** — Stops when all fields are filled, or when an iteration makes no improvement (no new fields found)

### Architecture

```
PDF Document ──→ Text Parser ──→ Document Context
                                       │
JSON Schema  ──→ Field Planner ──→ Target Fields
                                       │
                              ┌────────▼────────┐
                              │  Extraction LLM  │◄──── Iteration Loop
                              │  (GPT-5.4)  │       (max N rounds)
                              └────────┬────────┘
                                       │
                              Structured JSON Output
```

### What Makes This Approach Different?

- **Schema-driven, not template-driven:** One schema handles all documents of a type. A single invoice schema works for invoices from any vendor, however different each one looks.

- **Iterative, not one-shot:** Most extraction tools make one pass. This agent reviews its own work and fills gaps — catching array items it missed, resolving ambiguous fields on a second look.

- **Production-grade scoring:** The full KYNEX Harness is evaluated on [ExtractBench](https://github.com/run-llama/ExtractBench), a benchmark of 370 real enterprise documents across 67 document types, scoring **92.97 F1** — meaning it correctly extracts ~93% of all values across invoices, filings, reports, and forms.
