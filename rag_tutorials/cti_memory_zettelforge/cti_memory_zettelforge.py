"""
CTI Memory with ZettelForge — runnable tutorial.

Demonstrates a CTI-specialized agentic memory system:
  1. Ingests 5 short threat-intel reports
  2. Shows automatic entity extraction (CVEs, threat actors, IOCs, ATT&CK)
  3. Shows threat-actor alias resolution (APT28 = Fancy Bear = STRONTIUM)
  4. Shows intent-classified blended retrieval (vector + knowledge graph)
  5. Shows cross-memory synthesis

Runs fully in-process — no API keys, no cloud. Entity extraction uses
regex + STIX 2.1 types out of the box. If Ollama is running locally,
LLM-powered extraction and synthesis automatically activate.

Usage:
    pip install -r requirements.txt
    python cti_memory_zettelforge.py
"""

from zettelforge import MemoryManager


# ---------------------------------------------------------------------------
# Demo data — five short CTI reports. Notice the aliases used across reports:
# "APT28" vs "Fancy Bear" vs "STRONTIUM" all refer to the same threat actor.
# ZettelForge resolves them to a single node in the knowledge graph.
# ---------------------------------------------------------------------------
REPORTS = [
    (
        "2024-03-12 analyst-notes",
        "APT28 was observed using Cobalt Strike for lateral movement via "
        "T1021.002 (SMB/Windows Admin Shares) against a defense contractor. "
        "The loader beaconed to 185.244.25.xx over port 443.",
    ),
    (
        "2024-05-04 threat-brief",
        "Fancy Bear has shifted tactics — Microsoft now tracks them as "
        "FOREST BLIZZARD. Recent campaigns exploit CVE-2024-21412 in "
        "Windows SmartScreen to bypass Mark-of-the-Web protections.",
    ),
    (
        "2024-03-29 vuln-intel",
        "CVE-2024-3094 — the XZ Utils backdoor — was introduced by a "
        "long-running supply-chain operation attributed to the actor 'Jia Tan'. "
        "Affects liblzma and any tool that links it (including sshd on most "
        "Linux distros).",
    ),
    (
        "2024-02-18 hunt-report",
        "STRONTIUM infrastructure overlaps with a 2023 Sandworm campaign "
        "targeting Ukrainian telecoms. Shared C2 at 91.219.239.xx. "
        "Technique chain: T1566.001 -> T1059.001 -> T1021.002.",
    ),
    (
        "2024-04-02 patch-notes",
        "Microsoft patched CVE-2024-21412 in the March 2024 rollout. "
        "Detection rules for FOREST BLIZZARD tooling now live in the "
        "SigmaHQ repo under rules/windows/process_creation/.",
    ),
]


QUERIES = [
    # Factual — direct entity lookup
    "What tools does Fancy Bear use?",
    # Relational — multi-hop across alias boundary
    "Which CVEs are APT28 exploiting?",
    # Temporal — when did what happen
    "What happened with the XZ Utils backdoor?",
    # Causal — cross-report synthesis across aliases
    "Summarize known STRONTIUM / FOREST BLIZZARD / APT28 tooling and CVEs.",
]


def rule(title: str) -> None:
    print("\n" + "=" * 78)
    print(f"  {title}")
    print("=" * 78)


def main() -> None:
    rule("STEP 1 — Initialize CTI memory")
    mm = MemoryManager()
    print("MemoryManager ready. Storage defaults to ~/.amem.")
    print("Embeddings: fastembed (768-dim ONNX, in-process, ~7ms/embed).")
    print("LLM features activate automatically if Ollama is reachable on :11434.")

    rule("STEP 2 — Ingest 5 CTI reports")
    for source, body in REPORTS:
        print(f"  remember() <- [{source}] {body[:68]}...")
        mm.remember(body, domain="cti")
    print(f"\nStored {len(REPORTS)} reports. Entity extraction, graph updates,")
    print("and vector indexing ran automatically.")

    rule("STEP 3 — Alias resolution: APT28 = Fancy Bear = STRONTIUM")
    print("Different reports used different names for the same threat actor.")
    print("A single recall() returns notes across ALL aliases:\n")
    results = mm.recall("What does APT28 do?")
    for i, note in enumerate(results[:5], 1):
        snippet = getattr(note, "content", str(note))[:110]
        print(f"  {i}. {snippet}...")

    rule("STEP 4 — Intent-classified blended retrieval")
    for q in QUERIES:
        print(f"\n? {q}")
        hits = mm.recall(q)
        for note in hits[:3]:
            snippet = getattr(note, "content", str(note))[:100]
            print(f"    -> {snippet}...")

    rule("STEP 5 — Cross-memory synthesis")
    question = (
        "Summarize what we know about APT28 / Fancy Bear / STRONTIUM — "
        "tooling, CVEs exploited, and techniques."
    )
    print(f"? {question}\n")
    try:
        answer = mm.synthesize(question)
        print(answer)
    except Exception as exc:
        # Synthesize requires an LLM provider (Ollama or llama-cpp). If neither
        # is configured, fall back to listing the raw notes the retriever found.
        print(f"[synthesize() requires an LLM provider — {type(exc).__name__}: {exc}]")
        print("\nFalling back to ranked recall:")
        for note in mm.recall(question)[:5]:
            snippet = getattr(note, "content", str(note))[:120]
            print(f"  -> {snippet}...")

    rule("Done")
    print("Next steps:")
    print("  * Start Ollama (`ollama pull qwen2.5:3b && ollama serve`) to enable")
    print("    LLM-powered entity extraction and synthesize().")
    print("  * Ingest Sigma/YARA rules as first-class memory primitives:")
    print("      from zettelforge.sigma import ingest_rule as ingest_sigma")
    print("      from zettelforge.yara  import ingest_rule as ingest_yara")
    print("  * Wire the built-in MCP server into Claude Code:")
    print('      "zettelforge": {"command": "python3", "args": ["-m", "zettelforge.mcp"]}')
    print("\nDocs: https://docs.threatrecall.ai/")
    print("Repo: https://github.com/rolandpg/zettelforge")


if __name__ == "__main__":
    main()
