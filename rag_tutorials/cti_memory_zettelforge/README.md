## 🛡️ Agentic CTI Memory with ZettelForge

A runnable tutorial showing how to give an AI agent **persistent memory for cyber threat intelligence** — with automatic entity extraction, threat-actor alias resolution, a STIX 2.1 knowledge graph, and intent-classified blended retrieval. Powered by [ZettelForge](https://github.com/rolandpg/zettelforge).

Runs entirely in-process. No API keys. No cloud.

### The problem

Every SOC loses analysts. When a senior one leaves, two or three years of investigation context walks out with them. General-purpose AI memory tools can't fix this for security teams — they can't tell APT28 from Fancy Bear, don't know CVE-2024-3094 is the XZ backdoor, and can't parse Sigma or YARA. ZettelForge is built for analysts who think in threat graphs instead of chat histories.

### What this tutorial demonstrates

- **Automatic entity extraction** — CVEs, threat actors, IOCs (IPs, domains, hashes, URLs, emails), MITRE ATT&CK techniques, tools, campaigns, intrusion sets, and 10 more STIX 2.1 types extracted from free-text reports without manual tagging
- **Threat-actor alias resolution** — `APT28`, `Fancy Bear`, `STRONTIUM`, `FOREST BLIZZARD`, and `Sofacy` all resolve to the same actor node. Recall against one name returns notes written with any of them
- **STIX 2.1 knowledge graph** — entities become nodes, co-occurrence becomes edges, and LLM-inferred causal triples (e.g. `APT28 uses Cobalt Strike`) feed multi-hop queries
- **Intent-classified blended retrieval** — queries are classified as factual, temporal, relational, causal, or exploratory, and each intent weights vector similarity vs. knowledge-graph traversal differently
- **Cross-memory synthesis** — natural-language answer across everything the agent has ever stored

### How it works

Each `mm.remember(report)` call triggers:

1. Regex + (optional) LLM NER extracts 19 STIX 2.1 entity types
2. Entities become nodes in the knowledge graph; co-occurrence becomes edges; LLM infers causal triples
3. 768-dim embedding is stored in LanceDB (in-process, ~7ms/embed via fastembed)
4. Entity-overlap supersession marks stale notes so new intel doesn't get drowned in old

Each `mm.recall(query)` call triggers:

1. Intent classifier tags the query
2. Vector similarity (LanceDB) and BFS graph traversal (knowledge graph) run in parallel
3. Results are merged by policy weights, then reranked with a cross-encoder
4. Ranked list of relevant memories returned

Each `mm.synthesize(query)` call retrieves the same way, then asks the LLM to produce a direct answer grounded in the retrieved memories.

### How to get started

1. Clone the repository and change into this directory:

   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/rag_tutorials/cti_memory_zettelforge
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the tutorial:

   ```bash
   python cti_memory_zettelforge.py
   ```

That's it — the tutorial ships with five short CTI reports baked into the script. First run downloads the fastembed ONNX model (~100 MB); subsequent runs are fast.

### Optional: Enable LLM features

Entity extraction and synthesis get significantly richer when an LLM is available. ZettelForge auto-detects Ollama on `localhost:11434`:

```bash
# Install Ollama from https://ollama.com/download
ollama pull qwen2.5:3b
ollama serve
```

Re-run the tutorial and you'll see `mm.synthesize()` return a real LLM-generated summary across all the stored intel.

### What's next

- **Ingest detection rules**: Sigma and YARA rules are first-class memory primitives in ZettelForge — their MITRE/CVE/actor tags become graph edges in the same ontology as your free-text notes:

  ```python
  from zettelforge.sigma import ingest_rule as ingest_sigma
  from zettelforge.yara  import ingest_rule as ingest_yara

  ingest_sigma("rules/proc_creation_win_office_macro.yml", mm)
  ingest_yara("rules/webshell_china_chopper.yar", mm, tier="warn")
  ```

- **Wire the MCP server into Claude Code** so your agent has persistent CTI memory across sessions:

  ```json
  {
    "mcpServers": {
      "zettelforge": {
        "command": "python3",
        "args": ["-m", "zettelforge.mcp"]
      }
    }
  }
  ```

  Exposed tools: `remember`, `recall`, `synthesize`, `entity`, `graph`, `stats`.

### Expected output (abridged)

```
==============================================================================
  STEP 1 — Initialize CTI memory
==============================================================================
MemoryManager ready. Storage defaults to ~/.amem.
Embeddings: fastembed (768-dim ONNX, in-process, ~7ms/embed).
LLM features activate automatically if Ollama is reachable on :11434.

==============================================================================
  STEP 2 — Ingest 5 CTI reports
==============================================================================
  remember() <- [2024-03-12 analyst-notes] APT28 was observed using Cobalt Strike...
  remember() <- [2024-05-04 threat-brief] Fancy Bear has shifted tactics — Microsoft...
  remember() <- [2024-03-29 vuln-intel] CVE-2024-3094 — the XZ Utils backdoor — was...
  remember() <- [2024-02-18 hunt-report] STRONTIUM infrastructure overlaps with a...
  remember() <- [2024-04-02 patch-notes] Microsoft patched CVE-2024-21412 in the...

Stored 5 reports. Entity extraction, graph updates, and vector indexing ran automatically.

==============================================================================
  STEP 3 — Alias resolution: APT28 = Fancy Bear = STRONTIUM
==============================================================================
Different reports used different names for the same threat actor.
A single recall() returns notes across ALL aliases:

  1. APT28 was observed using Cobalt Strike for lateral movement via T1021.002...
  2. Fancy Bear has shifted tactics — Microsoft now tracks them as FOREST BLIZZARD...
  3. STRONTIUM infrastructure overlaps with a 2023 Sandworm campaign targeting...
  ...
```

### Resources

- **Repo**: https://github.com/rolandpg/zettelforge
- **PyPI**: https://pypi.org/project/zettelforge/
- **Docs**: https://docs.threatrecall.ai/
- **License**: MIT
