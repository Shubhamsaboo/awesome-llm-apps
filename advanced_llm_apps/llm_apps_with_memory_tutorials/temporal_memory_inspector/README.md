## 🕰️ Temporal Memory Inspector

This credential-free Streamlit app demonstrates a failure mode that ordinary chat history cannot solve: a fact changes, but an agent must still answer both "what is true now?" and "what was true then?" without leaking the later update into the historical answer.

The example stores two shipping-estimate revisions in local [Lians](https://github.com/Lians-ai/Lians) memory, then lets you switch between current and point-in-time recall. It runs entirely on your machine with SQLite and a local embedding model; no LLM API key or external database is required.

### Features

- Current recall returns the latest valid shipping estimate
- Point-in-time recall reconstructs the estimate before a later correction
- Revisions are seeded newest-first to prove recall does not depend on insertion order
- Every result includes a SHA-256-verifiable receipt
- Local SQLite storage with no API key

### How to get started

1. Clone the repository and open this example:

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_llm_apps/llm_apps_with_memory_tutorials/temporal_memory_inspector
```

2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Verify the current and historical results from the command line:

```bash
python verify.py
```

4. Launch the interactive app:

```bash
streamlit run app.py
```

### What to try

Choose **Current state** to see the corrected Monday estimate. Choose **August 2 at noon** to move the memory boundary three hours before the correction and recover the earlier Friday estimate.

The same pattern applies to support agents, policy assistants, research agents, and any workflow where facts change over time.
