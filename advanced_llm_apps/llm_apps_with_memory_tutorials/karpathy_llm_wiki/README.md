## 🧠 Karpathy LLM Wiki — Persistent Knowledge Base with L1/L2 Cache

A working implementation of [Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) with Claude Code. Instead of scattering notes across a dozen tools, you let an LLM maintain a structured wiki for you. Feed it raw sources — it extracts facts, cross-references them, and keeps the whole thing internally consistent.

The wiki becomes a **persistent, compounding artifact** — not a graveyard of stale notes.

Full implementation, MIT licensed: **[github.com/MehmetGoekce/llm-wiki](https://github.com/MehmetGoekce/llm-wiki)**

### The Problem

If you run any kind of technical practice — freelancing, consulting, side projects — your knowledge scatters fast. Jira tickets, Confluence docs, Slack threads, half-finished notes. Traditional answer is RAG, but RAG re-discovers everything from scratch with every query. Personal wikis are the alternative — but they die. Everyone starts one. Almost nobody maintains one.

As Karpathy puts it: *"the tedious part of maintaining a knowledge base is not the reading or the thinking — it's the bookkeeping."* Updating cross-references, fixing broken links, keeping metadata current. LLMs are perfect at bookkeeping. They do not get bored.

### The L1/L2 Cache Insight

The novel design choice in this implementation (not in Karpathy's gist): a **two-layer cache** modeled on CPU cache hierarchy.

- **L1 = Claude Memory (auto-loaded).** Small, fast, always available. Rules, gotchas, identity, preferences, credentials. Loaded at the start of every session — no `/wiki query` needed.
- **L2 = Wiki (on-demand).** Large, structured, queried when needed. Projects, workflows, research, deep knowledge.

The routing rule: *Would the LLM making a mistake without this knowledge be dangerous or embarrassing?* → L1. *Merely inconvenient?* → L2.

Credentials *must* live in L1 because the wiki is git-tracked. The L1 memory directory is excluded from git — making it the only safe place for secrets.

### Features

- **Five operations** — `/wiki ingest`, `/wiki query`, `/wiki lint`, `/wiki status`, `/wiki migrate`
- **Schema-driven consistency** — required properties per page type, automated lint rules
- **Health checks** — orphan detection, stale content (90+ days), broken references, credential leaks, hub completeness
- **Append-never-overwrite** — existing wiki content is sacred; new ingests append blocks
- **Logseq + Obsidian support** — outliner format ideal for LLM-generated content; flat markdown for manual editing
- **Zero external APIs** — runs entirely on local files + Claude Code. No RAG service, no database, no cloud dependency.

### How to Get Started

1. Clone the standalone implementation:

```bash
git clone https://github.com/MehmetGoekce/llm-wiki.git
cd llm-wiki
```

2. Run the setup script (interactive — picks Logseq or Obsidian, configures wiki path):

```bash
./setup.sh
```

3. Open the wiki in Claude Code and try the operations:

```bash
/wiki status        # show metrics dashboard
/wiki ingest <url>  # process a source, update 5–15 wiki pages
/wiki query <q>     # search wiki, synthesize answer with sources
/wiki lint --fix    # health check + auto-repair
```

### Schema Example

The schema is the contract between you and the LLM. See [`example_schema.md`](./example_schema.md) for a minimal Logseq schema definition (8 namespaces, 5 page types, lint rules, L1/L2 boundary).

### Tech Stack

- **Claude Code** — LLM brain. Custom slash commands, persistent memory, direct file access.
- **Logseq** (recommended) or **Obsidian** — wiki UI. Local-first markdown.
- **Git** — version control for the wiki content.
- No Python runtime, no API keys (beyond Claude Code itself), no databases.

### Background Reading

- Karpathy's original gist: [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- Detailed write-up of this implementation: ["I Built Karpathy's LLM Wiki with Claude Code and Logseq"](https://m3mobytes.substack.com/p/i-built-karpathys-llm-wiki-with-claude)
- Standalone repo (MIT, full source, schema templates, docs): [github.com/MehmetGoekce/llm-wiki](https://github.com/MehmetGoekce/llm-wiki)

### Contributing

Issues and PRs welcome on the standalone repo: [github.com/MehmetGoekce/llm-wiki/issues](https://github.com/MehmetGoekce/llm-wiki/issues)
