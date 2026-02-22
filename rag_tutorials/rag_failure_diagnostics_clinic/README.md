# RAG Failure Diagnostics Clinic

A small, framework-agnostic **RAG failure diagnostics clinic**.

You paste a real bug description from your LLM + RAG pipeline.  
The script asks an LLM to classify the failure into one of several **reusable patterns**
and suggests a **minimal structural fix** (not just “add more context” or “try a better model”).

The goal is to show a pattern-driven way to debug RAG incidents that can be
adapted to any stack: LangChain, LlamaIndex, custom microservices, or in-house infra.

---

## What you will learn

By running this example, you will learn how to:

- Describe **real-world RAG bugs** in plain text so an LLM can reason about them.
- Use a small library of **failure patterns** to triage incidents quickly.
- Ask the model to propose **minimal structural changes** instead of pure prompt tweaks.
- Call an **OpenAI-compatible API** from a small Python script.
- Save each diagnosis into a JSON report for later analysis or post-mortems.

This is not a full framework.  
It is a compact **clinic app** that demonstrates a pattern you can adapt in your own stacks.

---

## Folder structure

This tutorial expects the following files in `rag_tutorials/rag_failure_diagnostics_clinic`:

- `README.md` ← this file  
- `rag_failure_diagnostics_clinic.py` ← minimal interactive CLI script  
- `requirements.txt` ← Python dependencies  

The script is completely self-contained.  
All pattern definitions and prompts live inside this folder.

---

## Failure patterns (P01–P12)

The clinic uses a small, opinionated set of **12 reusable failure patterns**.
Each bug is mapped to exactly one primary pattern, with optional secondary candidates.

You can modify or extend these patterns to match your own production incidents.

| ID   | Pattern name                                          | Typical symptom                                                |
| ---- | ----------------------------------------------------- | -------------------------------------------------------------- |
| P01  | Retrieval hallucination / grounding drift             | Answer confidently contradicts retrieved documents.            |
| P02  | Chunk boundary or segmentation bug                    | Relevant facts are split or truncated across chunks.           |
| P03  | Embedding mismatch / semantic vs vector distance      | Cosine similarity does not match true relevance.               |
| P04  | Index skew or staleness                               | Old or missing data even though source of truth is updated.    |
| P05  | Query rewriting or router misalignment                | Router sends queries to the wrong tool or dataset.             |
| P06  | Long-chain reasoning drift                            | Multi-step tasks gradually lose track of earlier constraints.  |
| P07  | Tool-call misuse or ungrounded tools                  | Tools are called with wrong arguments or without grounding.    |
| P08  | Session memory leak / missing context                 | Conversation loses important facts between turns or sessions.  |
| P09  | Evaluation blind spots                                | System passes tests but fails on real incidents.               |
| P10  | Startup ordering / dependency not ready               | Services crash or 5xx during the first minutes after deploy.   |
| P11  | Config or secrets drift across environments           | Works locally, breaks only in staging / prod due to settings.  |
| P12  | Multi-tenant / multi-agent interference               | Requests or agents step on each other’s state or resources.    |

The built-in examples roughly correspond to:

- Example 1 → retrieval hallucination / grounding drift (P01 style).  
- Example 2 → startup ordering / dependency not ready (P10 style).  
- Example 3 → config or secrets drift across environments (P11 style).

You are encouraged to replace these with your own incident snippets.

---

## How the clinic works

At a high level:

1. The script builds a **system prompt** that explains the 12 patterns above.
2. You pick one of three built-in examples or paste your own RAG / LLM bug description.
3. The model is asked to:
   - Choose a **primary pattern ID** (P01–P12).  
   - Optionally choose up to **two secondary candidates**.  
   - Explain the reasoning in short bullet points.  
   - Propose a **minimal structural fix** (changes to retrieval, routing, eval, or infra).  
4. The full answer is printed to the console and also saved into
   `rag_failure_report.json` together with the original bug text and model name.

The intent is to show how a small **pattern vocabulary + prompt** can turn an LLM
into a lightweight helper for incident triage.

---

## Prerequisites

- Python 3.9 or newer.
- An API key for any **OpenAI-compatible** chat completion endpoint:
  - For example, `OPENAI_API_KEY` for `https://api.openai.com/v1`.
  - Or your own proxy URL set via `OPENAI_BASE_URL`.
- Basic familiarity with RAG pipelines, logs, and failure modes.

---

## Setup

From the root of the `awesome-llm-apps` repo:

```bash
cd rag_tutorials/rag_failure_diagnostics_clinic
pip install -r requirements.txt
````

Minimal `requirements.txt`:

```text
openai>=1.6.0
```

Set your API key as an environment variable (recommended):

```bash
export OPENAI_API_KEY="sk-..."
# optional, if you use a custom endpoint
# export OPENAI_BASE_URL="https://your-proxy.example.com/v1"
# export OPENAI_MODEL="gpt-4o-mini"
```

> Tip: If you prefer Colab, you can also copy the entire
> `rag_failure_diagnostics_clinic.py` file into a single Colab cell and run it there.

---

## Running the clinic

From inside `rag_tutorials/rag_failure_diagnostics_clinic`:

```bash
python rag_failure_diagnostics_clinic.py
```

You will see a simple text UI:

* If `OPENAI_API_KEY` is not set, the script will ask for an API key.
* You can keep the default base URL (`https://api.openai.com/v1`) and model (`gpt-4o`)
  or override them.
* Then you choose:

  * `1` → built-in retrieval hallucination example (P01 style).
  * `2` → startup ordering example (P10 style).
  * `3` → config / secrets drift example (P11 style).
  * `p` → paste your own bug description.

Each run prints a diagnosis and writes a `rag_failure_report.json` file
containing the bug text, model settings, and assistant reply.

You can commit several reports into your own repo as a lightweight
**RAG incident library**.

---

## Extending this tutorial

Some ideas for extending this pattern:

* Replace the examples with anonymized incidents from your own logs.
* Add more patterns or split existing ones to match your stack.
* Emit a richer JSON schema (severity, owners, suspected components).
* Plug the reports into an evaluation dashboard or incident tracker.

---

## Optional further reading

If you want to see an example of an open source checklist that catalogues RAG failure modes,
one external project you can look at is:

- https://github.com/onestardao/WFGY/blob/main/ProblemMap/README.md

This tutorial is independent of that project.  
The link is only for readers who want additional material.
