# WFGY 16 Problem Map RAG Failure Clinic 🩺

An interactive **RAG failure clinic** that helps you debug LLM and RAG pipelines using the **WFGY 16 Problem Map**.  
You paste a real bug description, the tool classifies it into **No.1–No.16**, and suggests a **minimal structural fix**, not just a generic prompt tweak.

This tutorial lives under `rag_tutorials/wfgy_rag_failure_clinic` and is fully self-contained.  
All extra knowledge comes from the open source WFGY repo on GitHub.

---

## 🧠 What you will learn

By running this example, you will learn how to:

- Use a **problem taxonomy** (the WFGY 16 Problem Map) to classify LLM and RAG failures.
- Turn that taxonomy into a **system prompt** that acts like a semantic firewall.
- Describe **real-world RAG bugs** in plain text so an LLM can reason about them.
- Call any **OpenAI-compatible API** (OpenAI, Nebius, your own proxy, etc.) from a small Python script.
- Map the diagnosis back to concrete docs and checklists in the WFGY Problem Map.

This is not a full framework.  
It is a compact **clinic app** that demonstrates a pattern you can adapt in your own stacks.

---

## 📁 Folder structure

This tutorial expects the following files in `rag_tutorials/wfgy_rag_failure_clinic`:

- `README.md` ← this file  
- `wfgy_rag_failure_clinic.py` ← minimal interactive CLI / Colab-friendly script  
- `requirements.txt` ← Python dependencies  

You do **not** need to copy any WFGY content into this repo.  
The script loads it directly from the public WFGY GitHub repo:

- WFGY main repo: [github.com/onestardao/WFGY](https://github.com/onestardao/WFGY)  
- WFGY Problem Map: [ProblemMap / README](https://github.com/onestardao/WFGY/tree/main/ProblemMap#readme)  
- TXTOS prompt file: [OS / TXTOS.txt](https://github.com/onestardao/WFGY/blob/main/OS/TXTOS.txt)

All WFGY assets are released under the MIT License.

---

## ✅ Prerequisites

- Python 3.9 or newer.
- An API key for any **OpenAI-compatible** chat completion endpoint.
  - For example, `OPENAI_API_KEY` for the default `https://api.openai.com/v1`.
  - Or a Nebius key and base URL, or your own compatible proxy.
- Basic familiarity with RAG pipelines, logs, and failure modes.

---

## ⚙️ Setup

From the root of the `awesome-llm-apps` repo:

```bash
cd rag_tutorials/wfgy_rag_failure_clinic
pip install -r requirements.txt
```

Minimal `requirements.txt`:

```text
openai>=1.6.0
requests>=2.31.0
```

Set your API key as an environment variable (recommended):

```bash
export OPENAI_API_KEY="sk-..."
# optional, if you use a custom endpoint
# export OPENAI_BASE_URL="https://your-proxy.example.com/v1"
```

> Tip: If you prefer Colab, you can also copy the entire `wfgy_rag_failure_clinic.py` file into a single Colab cell and run it there. The script is Colab-friendly out of the box.

---

## 🧩 WFGY 16 Problem Map reference

The **WFGY 16 Problem Map** is a checklist of recurring failure modes in LLM and RAG systems.
This clinic treats your bug report as a symptom and maps it into one of these sixteen buckets.

Below is a compact reference table.
Each row links back to the corresponding page in the WFGY repo.

| No. | problem domain (with layer/tags)       | what breaks                                   | doc                                                                                                              |
| --- | -------------------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| 1   | [IN] hallucination & chunk drift {OBS} | retrieval returns wrong or irrelevant content | [hallucination.md](https://github.com/onestardao/WFGY/blob/main/ProblemMap/hallucination.md)                     |
| 2   | [RE] interpretation collapse {OBS}     | chunk is right, logic is wrong                | [retrieval-collapse.md](https://github.com/onestardao/WFGY/blob/main/ProblemMap/retrieval-collapse.md)           |
| 3   | [RE] long reasoning chains {OBS}       | drifts across multi-step tasks                | [context-drift.md](https://github.com/onestardao/WFGY/blob/main/ProblemMap/context-drift.md)                     |
| 4   | [RE] bluffing / overconfidence         | confident but unfounded answers               | [bluffing.md](https://github.com/onestardao/WFGY/blob/main/ProblemMap/bluffing.md)                               |
| 5   | [IN] semantic ≠ embedding {OBS}        | cosine match does not equal true meaning      | [embedding-vs-semantic.md](https://github.com/onestardao/WFGY/blob/main/ProblemMap/embedding-vs-semantic.md)     |
| 6   | [RE] logic collapse & recovery {OBS}   | dead ends, needs controlled reset             | [logic-collapse.md](https://github.com/onestardao/WFGY/blob/main/ProblemMap/logic-collapse.md)                   |
| 7   | [ST] memory breaks across sessions     | lost threads, no continuity                   | [memory-coherence.md](https://github.com/onestardao/WFGY/blob/main/ProblemMap/memory-coherence.md)               |
| 8   | [IN] debugging is a black box {OBS}    | no visibility into the failure path           | [retrieval-traceability.md](https://github.com/onestardao/WFGY/blob/main/ProblemMap/retrieval-traceability.md)   |
| 9   | [ST] entropy collapse {OBS}            | attention melts, incoherent output            | [entropy-collapse.md](https://github.com/onestardao/WFGY/blob/main/ProblemMap/entropy-collapse.md)               |
| 10  | [RE] creative freeze                   | flat, literal outputs                         | [creative-freeze.md](https://github.com/onestardao/WFGY/blob/main/ProblemMap/creative-freeze.md)                 |
| 11  | [RE] symbolic collapse                 | abstract or logical prompts break             | [symbolic-collapse.md](https://github.com/onestardao/WFGY/blob/main/ProblemMap/symbolic-collapse.md)             |
| 12  | [RE] philosophical recursion           | self-reference loops, paradox traps           | [philosophical-recursion.md](https://github.com/onestardao/WFGY/blob/main/ProblemMap/philosophical-recursion.md) |
| 13  | [ST] multi-agent chaos {OBS}           | agents overwrite or misalign logic            | [Multi-Agent_Problems.md](https://github.com/onestardao/WFGY/blob/main/ProblemMap/Multi-Agent_Problems.md)       |
| 14  | [OP] bootstrap ordering                | services fire before dependencies are ready   | [bootstrap-ordering.md](https://github.com/onestardao/WFGY/blob/main/ProblemMap/bootstrap-ordering.md)           |
| 15  | [OP] deployment deadlock               | circular waits in infra                       | [deployment-deadlock.md](https://github.com/onestardao/WFGY/blob/main/ProblemMap/deployment-deadlock.md)         |
| 16  | [OP] pre-deploy collapse {OBS}         | version skew or missing secret on first call  | [predeploy-collapse.md](https://github.com/onestardao/WFGY/blob/main/ProblemMap/predeploy-collapse.md)           |

In this tutorial the three built-in examples are mapped as follows:

* Example 1 → **No.1** hallucination and chunk drift.
* Example 2 → **No.14** bootstrap ordering.
* Example 3 → **No.16** pre-deploy collapse and config drift.

For deeper recovery plans and checklists, open the full
[WFGY Problem Map overview](https://github.com/onestardao/WFGY/tree/main/ProblemMap#readme).

---

## 🩻 How the clinic works

At a high level:

1. The script **downloads** two small text files from the WFGY repo:

   * The Problem Map README (for the taxonomy).
   * The TXTOS file (for a stable prompting style).
2. It **builds a system prompt** that:

   * Explains the 16 Problem Map categories.
   * States rules for picking a primary diagnosis and an optional secondary.
   * Reminds the model that examples 1–3 are canonical templates.
3. You pick one of three **ready-made bug examples** or paste your own:

   * Retrieval hallucination around RAG context.
   * Deployment ordering / infra race around vector stores.
   * Pre-deploy secret/config drift.
4. The model returns:

   * A primary **Problem Map number (No.1–No.16)**.
   * An optional secondary candidate.
   * A short explanation and a proposed **minimal structural fix**.
5. You can then open the linked Problem Map doc for a deeper walkthrough of the failure mode and mitigations.

The goal is not to be perfect, but to show how a **problem taxonomy + prompt** can become a lightweight debugging assistant.

---

## 🚀 Running the clinic

From inside `rag_tutorials/wfgy_rag_failure_clinic`:

```bash
python wfgy_rag_failure_clinic.py
```

You will see a simple text UI:

* If `OPENAI_API_KEY` is not set, the script will ask for an API key.
* You can keep the default base URL (`https://api.openai.com/v1`) and model (`gpt-4o`) or override them.
* Then you choose:

  * `1` → built-in retrieval hallucination example (No.1 style).
  * `2` → bootstrap ordering / infra race example (No.14 style).
  * `3` → pre-deploy config drift example (No.16 style).
  * `p` → paste your own bug description.

A truncated sample interaction:

```text
$ python wfgy_rag_failure_clinic.py

Loaded WFGY assets. Ready to debug.

Choose an example or paste your own:
  [1] Example 1 - retrieval hallucination (No.1 style)
  [2] Example 2 - bootstrap ordering / infra race (No.14 style)
  [3] Example 3 - secrets / config drift (No.16 style)
  [p] Paste my own RAG / LLM bug
Your choice: 1

Running diagnosis with model: gpt-4o ...

Primary Problem Map match: No.1 - hallucination & chunk drift
Secondary candidate: No.8 - debugging is a black box

Why:
- Retrieved chunks explicitly say only cards and PayPal are supported.
- The answer confidently invents Bitcoin support.
- Logs show no retrieval or vector errors, so the drift is inside the LLM step.

Minimal structural fix:
- Tighten the answer contract so the model must quote and reason over retrieved snippets.
- Add an explicit "do not invent payment methods" clause in your system prompt.
- Log and surface all retrieval snippets next to the answer so operators can audit future failures.

For the full checklist, see:
https://github.com/onestardao/WFGY/blob/main/ProblemMap/hallucination.md
```

You can repeat the process for as many bugs as you want in a single run.

---

## 🧪 Minimal script (`wfgy_rag_failure_clinic.py`)

Below is a minimal implementation that matches the description above.
Place this in `rag_tutorials/wfgy_rag_failure_clinic/wfgy_rag_failure_clinic.py`.

```python
"""
WFGY RAG Failure Clinic
Minimal interactive demo for the WFGY 16 Problem Map inside awesome-llm-apps.
"""

import os
import textwrap
from getpass import getpass

import requests
from openai import OpenAI

PROBLEM_MAP_URL = "https://raw.githubusercontent.com/onestardao/WFGY/main/ProblemMap/README.md"
TXTOS_URL = "https://raw.githubusercontent.com/onestardao/WFGY/main/OS/TXTOS.txt"
WFGY_PROBLEM_MAP_HOME = "https://github.com/onestardao/WFGY/tree/main/ProblemMap"
WFGY_REPO = "https://github.com/onestardao/WFGY"


EXAMPLE_1 = """=== Example 1 — retrieval hallucination (No.1 style) ===

Context:
You have a simple RAG chatbot that answers questions from a product FAQ.
The FAQ only covers billing rules for your SaaS product and does NOT mention anything about cryptocurrency.

User prompt:
"Can I pay my subscription with Bitcoin?"

Retrieved context (from vector store):
- "We only accept major credit cards and PayPal."
- "All payments are processed in USD."

Model answer:
"Yes, you can pay with Bitcoin. We support several cryptocurrencies through a third-party payment gateway."

Logs:
No errors. Retrieval shows the FAQ chunks above, but the model still confidently invents Bitcoin support.
"""


EXAMPLE_2 = """=== Example 2 — bootstrap ordering / infra race (No.14 style) ===

Context:
You have a RAG API with three services: api-gateway, rag-worker, and vector-db (for example Qdrant or FAISS).
In local docker compose everything works.

Deployment:
In production, services are deployed on Kubernetes.

Symptom:
Right after a fresh deploy, api-gateway returns 500 errors for the first few minutes.
Logs show connection timeouts from api-gateway to vector-db.

After a few minutes, the errors disappear and the system behaves normally.
You suspect a startup race between api-gateway and vector-db but are not sure how to fix it properly.
"""


EXAMPLE_3 = """=== Example 3 — secrets / config drift around first deploy (No.16 style) ===

Context:
You added a new environment variable for the RAG pipeline: SECRET_RAG_KEY.
This is required by middleware that signs outgoing requests to an internal search API.

Local:
On developer machines, SECRET_RAG_KEY is defined in .env and everything works.

Production:
You deployed a new version but forgot to add SECRET_RAG_KEY to the production environment.
The first requests after deploy fail with 500 errors and "missing secret" messages in the logs.

After hot-patching the secret into production, the errors stop.
However, similar "first deploy breaks because of missing config" incidents keep happening.
"""


def fetch_text(url: str) -> str:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def build_system_prompt(problem_map: str, txtos: str) -> str:
    header = """
You are an LLM debugger that follows the WFGY 16 Problem Map.

Goal:
Given a description of a bug or failure in an LLM or RAG pipeline, you must:
- Map it to exactly one primary Problem Map number (No.1–No.16).
- Optionally propose one secondary candidate if it is very close.
- Explain your reasoning in plain language.
- Propose a minimal structural fix, not just prompt tweaking.
- When possible, point the user toward the relevant WFGY Problem Map documents.

You are not allowed to invent new problem categories.
You must choose from the sixteen WFGY Problem Map entries only.

About the three built-in examples:
- Example 1 is a clean retrieval hallucination pattern. It should map primarily to No.1.
- Example 2 is a bootstrap ordering or infra race pattern. It should map primarily to No.14.
- Example 3 is a first deploy secrets / config drift pattern. It should map primarily to No.16.
"""
    return (
        textwrap.dedent(header).strip()
        + "\n\n=== TXTOS excerpt ===\n"
        + txtos[:4000]
        + "\n\n=== Problem Map excerpt ===\n"
        + problem_map[:4000]
    )


def load_wfgy_assets() -> str:
    print("Downloading WFGY Problem Map and TXTOS prompt ...")
    problem_map_text = fetch_text(PROBLEM_MAP_URL)
    txtos_text = fetch_text(TXTOS_URL)
    system_prompt = build_system_prompt(problem_map_text, txtos_text)
    print("Loaded WFGY assets. Ready to debug.\n")
    return system_prompt


def make_client_and_model():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        api_key = getpass("Enter your OpenAI-compatible API key: ").strip()

    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    if not base_url:
        base_url = "https://api.openai.com/v1"

    model_name = os.getenv("OPENAI_MODEL", "").strip()
    if not model_name:
        model_name = input("Model name (press Enter for gpt-4o): ").strip() or "gpt-4o"

    client = OpenAI(api_key=api_key, base_url=base_url)
    print(f"\nUsing base URL: {base_url}")
    print(f"Using model: {model_name}\n")
    return client, model_name


def choose_bug_description() -> str:
    print("Choose an example or paste your own bug description:")
    print("  [1] Example 1 — retrieval hallucination (No.1 style)")
    print("  [2] Example 2 — bootstrap ordering / infra race (No.14 style)")
    print("  [3] Example 3 — secrets / config drift (No.16 style)")
    print("  [p] Paste my own RAG / LLM bug\n")

    choice = input("Your choice: ").strip().lower()
    print()

    if choice == "1":
        bug = EXAMPLE_1
        print("You selected Example 1. Full bug description:\n")
        print(bug)
        print()
        return bug

    if choice == "2":
        bug = EXAMPLE_2
        print("You selected Example 2. Full bug description:\n")
        print(bug)
        print()
        return bug

    if choice == "3":
        bug = EXAMPLE_3
        print("You selected Example 3. Full bug description:\n")
        print(bug)
        print()
        return bug

    print("Paste your bug description. End with an empty line.")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line.strip():
            break
        lines.append(line)

    user_bug = "\n".join(lines).strip()
    if not user_bug:
        print("No bug description detected, aborting this round.\n")
        return ""

    print("\nYou pasted the following bug description:\n")
    print(user_bug)
    print()
    return user_bug


def run_once(client: OpenAI, model_name: str, system_prompt: str) -> None:
    bug = choose_bug_description()
    if not bug:
        return

    print("Running diagnosis ...\n")

    completion = client.chat.completions.create(
        model=model_name,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Here is the bug description. "
                    "Follow the WFGY 16 Problem Map rules described above.\n\n"
                    + bug
                ),
            },
        ],
    )

    reply = completion.choices[0].message.content or ""
    print(reply)
    print("\nFor detailed checklists, visit:")
    print(f"- Problem Map home: {WFGY_PROBLEM_MAP_HOME}")
    print(f"- Full WFGY repo:   {WFGY_REPO}\n")


def main():
    system_prompt = load_wfgy_assets()
    client, model_name = make_client_and_model()

    while True:
        run_once(client, model_name, system_prompt)
        again = input("Debug another bug? (y/n): ").strip().lower()
        if again != "y":
            print("Session finished. Goodbye.")
            break
        print()


if __name__ == "__main__":
    main()

```

---

## 🔗 Attribution

* WFGY project: [https://github.com/onestardao/WFGY](https://github.com/onestardao/WFGY)
* Original Problem Map and TXTOS design by the WFGY author.
* This tutorial is a small integration example contributed to `awesome-llm-apps`
  to demonstrate how a **failure taxonomy** can be plugged into an LLM debugging tool.

You are free to adapt this pattern to your own taxonomies, evaluation suites, or internal incident post-mortems.

