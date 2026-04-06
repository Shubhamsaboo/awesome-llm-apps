# Multi-Agent Task Orchestrator

A Streamlit application that routes tasks to specialized AI agents, prevents duplicate work with SQLite-based tracking, and validates results through quality gates before marking them complete.

## Features

- **5 Specialized Agents**: code-architect, security-reviewer, researcher, doc-writer, test-engineer
- **Keyword-Based Routing**: Tasks are automatically assigned to the best-matching agent
- **Anti-Duplication**: SQLite registry with exact hash + fuzzy similarity matching (55% threshold)
- **Quality Gates**: Automated verification checks before accepting agent output
- **Multi-Provider**: Works with OpenAI (GPT-4o), Anthropic (Claude), or Demo mode

## How to get Started?

1. Clone the repository and navigate to this directory:
   ```bash
   cd awesome-llm-apps/advanced_ai_agents/multi_agent_apps/multi_agent_task_orchestrator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   streamlit run task_orchestrator.py
   ```

4. Choose your LLM provider in the sidebar (or use Demo mode with no API key).

## How it Works

```
Task Input
    |
    v
[Anti-Duplication Check] --duplicate--> Warning + Skip
    |
    | (new task)
    v
[Keyword Router] --> code-architect | security-reviewer | researcher | doc-writer | test-engineer
    |
    v
[LLM Execution] (OpenAI / Anthropic / Demo)
    |
    v
[Quality Gate] --> VERIFIED (mark done) | INCOMPLETE (warn) | FAILED (reject)
    |
    v
[SQLite Registry] (persistent task history)
```

## Key Patterns

| Pattern | Implementation |
|---------|---------------|
| Anti-duplication | SHA-256 hash + SequenceMatcher fuzzy matching |
| Task routing | Keyword scoring across 5 agent profiles |
| Quality gate | 4-check verification (non-empty, addresses task, structured, no refusal) |
| State persistence | SQLite database with full task lifecycle |

Orchestration patterns from [guardian-agent-prompts](https://github.com/milkomida77/guardian-agent-prompts).
