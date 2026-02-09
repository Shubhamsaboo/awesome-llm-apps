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
