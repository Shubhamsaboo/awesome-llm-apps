# DNA Memory - AI Agent Memory System with Human-like Learning

Build AI agents that learn and grow like human brains - with forgetting, reinforcement, reflection, and knowledge graphs.

## Overview

DNA Memory is a zero-dependency memory system that goes beyond simple storage. It mimics how human memory actually works:

- **Three-layer architecture**: Working → Short-term → Long-term memory
- **Active forgetting**: Unused memories naturally decay
- **Automatic reflection**: Extracts patterns from scattered information
- **Knowledge graphs**: Builds connections between memories
- **Weight reinforcement**: Frequently accessed memories get stronger

Unlike cloud-based solutions (Mem0, Zep) or simple context managers (LangChain Memory), DNA Memory runs entirely locally and truly "learns" from experience.

## Features

- 🧠 **Human-like memory**: Not just storage, but actual learning
- 📉 **Forgetting mechanism**: Low-importance info naturally fades
- 📈 **Reinforcement**: Repeated use increases memory weight
- 🔄 **Pattern extraction**: Automatically finds insights from data
- 🕸️ **Knowledge graphs**: Links related memories together
- 🏠 **100% local**: Zero dependencies, your data stays private

## Prerequisites

- Python 3.8+
- No external packages required (pure Python)

## Installation

```bash
# Clone the repository
git clone https://github.com/AIPMAndy/dna-memory.git
cd dna-memory

# That's it! No pip install needed.
```

## Quick Start

### 1. Record Your First Memory

```bash
python3 scripts/evolve.py remember "I prefer concise responses" -t preference -i 0.9
```

Output:
```
✅ Recorded: [mem_a1b2c3d4] I prefer concise responses...
```

### 2. Recall Memories

```bash
python3 scripts/evolve.py recall "prefer"
```

Output:
```
[mem_a1b2c3d4] (preference) [Short-term] I prefer concise responses [0.90]
```

### 3. View Statistics

```bash
python3 scripts/evolve.py stats
```

Output:
```
📊 DNA Memory Statistics
   Short-term: 5 memories
   Long-term: 2 memories
   Links: 3 connections
```

## Running the Demo

The included demo script shows all core features:

```bash
python3 dna_memory_demo.py
```

This will:
1. Record several memories with different types
2. Demonstrate recall with weight reinforcement
3. Show automatic pattern extraction
4. Create memory links
5. Simulate forgetting over time

## How It Works

### Three-Layer Memory Architecture

```
┌─────────────────────────────────────────────┐
│ 🔴 Working Memory                           │
│ Current session temporary info              │
│ → Auto-filtered after session ends          │
└─────────────────┬───────────────────────────┘
                  ↓ Filter
┌─────────────────────────────────────────────┐
│ 🟡 Short-term Memory                        │
│ Last 7 days important info                  │
│ → Decays if unused, strengthens if accessed │
└─────────────────┬───────────────────────────┘
                  ↓ Consolidate
┌─────────────────────────────────────────────┐
│ 🟢 Long-term Memory                         │
│ Validated persistent knowledge             │
│ → Extracted patterns, high-weight memories  │
└─────────────────────────────────────────────┘
```

### Weight Dynamics

| Event | Weight Change | Explanation |
|-------|---------------|-------------|
| Accessed/Used | +0.1 | Frequently used = more important |
| User confirmed | +0.2 | Correct info gets boosted |
| User corrected | Mark error | Create new correct memory |
| 7 days unused | -0.1 | Unused memories fade |
| Linked to others | +0.05 | Connected memories are more stable |
| Extracted as pattern | Upgrade | Moves to long-term memory |

### Automatic Pattern Extraction

When you accumulate similar memories:

```
📝 Short-term memories:
   "GitHub push timed out"
   "GitHub clone timed out"
   "GitHub fetch timed out"

💡 Auto-extracted pattern:
   "GitHub network is unstable, needs retry mechanism"
   → Pattern upgraded to long-term memory
```

## Use Cases

| Scenario | Benefit |
|----------|---------|
| Personal AI Assistant | Remembers preferences, gets smarter over time |
| Knowledge Worker | Accumulates domain expertise, forms professional patterns |
| Customer Service Agent | Learns customer traits, optimizes communication |
| Autonomous Agent | Learns from mistakes, continuous self-improvement |
| Agent Developer | Add memory evolution to your agents |

## Configuration

Edit `assets/config.json` to customize behavior:

```json
{
  "decay_days": 7,           // Days before decay starts
  "decay_rate": 0.1,         // Weight reduction per decay
  "forget_threshold": 0.2,   // Below this = forgotten
  "reflect_trigger": 20,     // Auto-reflect after N memories
  "max_short_term": 100,     // Short-term memory limit
  "max_long_term": 500       // Long-term memory limit
}
```

## Command Reference

```bash
# Record memory
evolve.py remember "content" -t type -i importance(0-1)

# Recall memories
evolve.py recall "keyword"

# Reflect and extract patterns
evolve.py reflect

# Trigger forgetting
evolve.py decay

# Link memories
evolve.py link mem_001 mem_002 -r "causal"

# List/delete/export
evolve.py list [-L for long-term]
evolve.py delete mem_xxx
evolve.py export -o backup.json
```

## Memory Types

- `fact`: Factual information
- `preference`: User preferences
- `skill`: Learned skills/methods
- `error`: Mistakes to avoid
- `pattern`: Extracted insights
- `insight`: High-level understanding

## Data Storage

All data stored locally in JSON format:

```
~/.openclaw/workspace/memory/
├── short_term.json    # Short-term memories
├── long_term.json     # Long-term memories
├── patterns.md        # Extracted patterns
├── graph.json         # Knowledge graph
└── meta.json          # Statistics
```

## Comparison with Alternatives

| Feature | Mem0 | Zep | LangChain | DNA Memory |
|---------|------|-----|-----------|------------|
| Basic storage | ✅ | ✅ | ✅ | ✅ |
| Vector search | ✅ | ✅ | ✅ | ✅ |
| Multi-layer memory | ❌ | ⚠️ | ❌ | ✅ 3 layers |
| Active forgetting | ❌ | ❌ | ❌ | ✅ |
| Auto pattern extraction | ❌ | ❌ | ❌ | ✅ |
| Reflection loop | ❌ | ❌ | ❌ | ✅ |
| Knowledge graphs | ❌ | ⚠️ | ❌ | ✅ |
| Dynamic weight | ❌ | ❌ | ❌ | ✅ |
| Zero-dependency local | ❌ | ❌ | ❌ | ✅ |

## Contributing

Contributions welcome! Please check [CONTRIBUTING.md](https://github.com/AIPMAndy/dna-memory/blob/main/CONTRIBUTING.md)

## License

Apache 2.0 - Free for commercial use, modification allowed, attribution required.

## Author

**AI Chief Andy**

Former AI Product Lead at Tencent/Baidu → Unicorn VP → Startup CEO

Now focused on AI commercialization, helping founders amplify business with AI.

- GitHub: [@AIPMAndy](https://github.com/AIPMAndy)
- Twitter: [@pmai_andy](https://twitter.com/pmai_andy)

---

If this project helps you, please give it a ⭐ Star!

That's the biggest support for the author 🙏
