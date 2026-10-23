# agent-guard

**Stdlib-only Python guard rails for unattended AI agents**

- **Per-category budget caps** checked before each call
- **Loop breaker** to prevent infinite agent runs
- **Owner-action gate** for critical decisions
- **Append-only JSONL run log** for tracking and debugging

### Features
- **No dependencies** (pure Python)
- **No network calls** (runs locally)
- **MIT licensed** (open-source)

### Usage
```python
from agent_guard import AgentGuard

# Initialize the guard with budget limits
guard = AgentGuard(budget={'llm_calls': 100, 'api_calls': 50})

# Run your agent with guardrails
guard.run_agent(your_agent_function)
```

### License
MIT

### Links
- [GitHub Repository](https://github.com/renvt89/agent-guard)
- [Documentation](https://github.com/renvt89/agent-guard#usage)