# 🧭 Repowise - Context & Token Optimization for Coding Agents

Cut the tokens your coding agent burns on exploration. Most of an agent's spend
goes to greping for symbols, reading candidate files, then re-reading them as
context grows. [Repowise](https://github.com/repowise-dev/repowise) indexes your
repo once, offline, and hands the agent a curated answer instead of a pile of
files, plus a `distill` wrapper that compresses noisy command output before the
agent ever reads it.

100% local, no API key required for this demo, nothing leaves your machine.

## 📋 Overview

This app shows two token-optimization surfaces, both measured on your machine
when you run the demo (not hardcoded estimates):

1. **`repowise distill`** wraps any noisy command (tests, `git log`, builds) and
   returns an errors-first, reversible rendering. The 300 passing lines around 4
   failures get dropped behind a restorable marker.
2. **The context layer** (`repowise init --index-only` + MCP tools) builds a
   dependency graph, git history, and code-health score locally, then answers
   `get_context` / `get_answer` with one card instead of a fan-out of file reads.

### Key Benefits

- **💰 Up to 96% fewer context tokens** to load a commit's context vs raw reads
- **🔁 60 to 90% smaller command output** via `distill`, fully reversible
- **📞 70% fewer agent tool calls** at answer quality on par with raw exploration
- **🔒 100% local** - graph, git, health, and docs are built on your machine
- **🔌 MCP-native** - works with Claude Code, Cursor, Codex, any MCP client
- **🧠 Zero LLM for the signals** - graph, git, and health are deterministic

## 🚀 What's in this demo

- `quick_test.py` - 5-second install check, runs a real `distill` and prints the savings
- `repowise_demo.py` - full run:
  - **Part 1** shells out to the real `repowise distill` binary on a 253-test
    run (3 failures buried in 250 passing lines) and reports genuine before/after
    token counts
  - **Part 2** indexes a small sample repo locally with `repowise init
    --index-only` (no API key) and measures the raw read cost the context layer
    replaces
- `requirements.txt` - `repowise` + `tiktoken` (for exact token counts)

## 📦 Installation

```bash
pip install -r requirements.txt
# or just: pip install repowise
```

## 💻 Usage

```bash
python quick_test.py        # fast sanity check
python repowise_demo.py     # full distill + context demo
```

### Use it on your own repo

```bash
cd /path/to/your/repo
repowise init --index-only -y      # graph + git + health, no LLM, no key
repowise distill pytest -q         # compact, reversible test output
repowise mcp                       # serve get_context / get_answer to your agent
```

Wire the MCP server into your agent:

```bash
# Claude Code
claude mcp add repowise -- repowise mcp
```

```toml
# Codex CLI  (~/.codex/config.toml)
[mcp_servers.repowise]
command = "repowise"
args = ["mcp"]
```

## 📊 Real-World Performance

Measured on public codebases, reproducible in
[repowise-bench](https://github.com/repowise-dev/repowise-bench).

### Context layer (agent efficiency, paired SWE-QA runs)

| Metric | Result |
|--------|--------|
| Context to load a commit (`get_context` vs raw) | 2,391 vs 64,039 tokens (**~27x fewer, -96%**) |
| Files read per task | **-69% to -89%** |
| Tool calls per task | **-49% to -70%** |
| Answer quality | on par with raw exploration |

### Distill (command-output compression, per command)

| Command | Raw to distilled | Saved |
|---------|------------------|-------|
| `pytest -q` (11 failures) | 3,374 to 1,317 tokens | **61%** (all 11 failures kept) |
| `git log -50` | 3,064 to 331 tokens | **89%** |
| `git diff` (30 commits) | 62,833 to 8,635 tokens | **86%** |

Every omission is reversible with `repowise expand <ref>`, and small outputs
pass through untouched (a net-positive guard).

## 🎯 Best Use Cases

Reach for Repowise when:

- ✅ Your agent keeps re-reading the same files as context grows
- ✅ Test / build / git output floods the context window with noise
- ✅ You want architecture-grounded answers ("why does auth work this way?")
- ✅ You care about cost and quality, not just truncation

## 🛡️ How it stays honest

- **Reversible, not lossy** - `distill` stores dropped content and restores it on demand
- **Exit codes preserved** - `distill pytest` still fails your CI if tests fail
- **Deterministic signals** - graph, git, and code-health use no LLM
- **Freshness-aware** - MCP responses flag when the index drifts from live HEAD

## 🔗 Resources

- **GitHub**: https://github.com/repowise-dev/repowise
- **PyPI**: https://pypi.org/project/repowise/
- **Benchmarks**: https://github.com/repowise-dev/repowise-bench
- **Docs**: https://docs.repowise.dev

## 📄 License

Repowise is AGPL-3.0. Free for individuals and teams using it internally.

## 🙏 Credits

Built by the [Repowise](https://www.repowise.dev) team for engineers who got
tired of watching their AI agent `cat` the same file for the fourth time.
