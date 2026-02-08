# 🛡️ AI Agent Governance - Policy-Based Sandboxing

Learn how to build a governance layer that enforces deterministic policies on AI agents, preventing dangerous actions before they execute.

## Features

- **Policy-Based Sandboxing**: Define what your AI agent can and cannot do using declarative policies
- **Action Interception**: Catch and validate agent actions before execution
- **Audit Logging**: Full trail of agent actions for compliance and debugging
- **File System Guards**: Restrict read/write to specific directories
- **Network Guards**: Allowlist-only external API access
- **Rate Limiting**: Prevent runaway agents with configurable limits

## How It Works

1. **Policy Definition**: Define your security policies in YAML format
2. **Action Wrapping**: Wrap your agent's tools with the governance layer
3. **Interception**: Before any tool executes, the policy engine validates the action
4. **Decision**: Actions are allowed, denied, or require human approval
5. **Audit**: All decisions are logged for compliance and debugging

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Agent     │────▶│  Governance  │────▶│    Tool     │
│  (LLM)      │     │    Layer     │     │  Execution  │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                    ┌──────▼──────┐
                    │   Policy    │
                    │   Engine    │
                    └─────────────┘
```

## Requirements

- Python 3.8+
- OpenAI API key (or any LLM provider)
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/single_agent_apps/ai_agent_governance
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Set your API key:
   ```bash
   export OPENAI_API_KEY=your-openai-api-key
   ```

2. Run the governance demo:
   ```bash
   python ai_agent_governance.py
   ```

3. Try different actions and see how the policy engine handles them.

## Example Policy Configuration

```yaml
policies:
  filesystem:
    allowed_paths: ["/workspace", "/tmp"]
    denied_paths: ["/etc", "/home", "~/.ssh"]
    
  network:
    allowed_domains: ["api.openai.com", "api.github.com"]
    block_all_others: true
    
  execution:
    max_actions_per_minute: 60
    require_approval_for: ["delete_file", "execute_shell"]
    
  tools:
    allowed: ["read_file", "write_file", "web_search"]
    denied: ["execute_code", "send_email"]
```

## Example Output

```
🛡️ AI Agent Governance Demo
============================

📋 Loading policy: workspace_sandbox.yaml

🤖 Agent request: "Read the contents of /etc/passwd"
❌ DENIED: Path '/etc/passwd' is outside allowed directories

🤖 Agent request: "Write analysis to /workspace/report.md"  
✅ ALLOWED: Action permitted by policy

🤖 Agent request: "Make HTTP request to unknown-api.com"
❌ DENIED: Domain 'unknown-api.com' not in allowlist

🤖 Agent request: "Delete /workspace/temp.txt"
⏸️ PENDING: Action requires human approval
   [Y/n]: 
```

## Technical Details

### Policy Engine

The policy engine evaluates actions against a set of rules:

```python
class PolicyEngine:
    def evaluate(self, action: Action) -> Decision:
        # Check each policy rule
        for rule in self.rules:
            result = rule.evaluate(action)
            if result.is_terminal:
                return result
        return Decision.ALLOW
```

### Action Interception

Tools are wrapped with governance checks:

```python
def governed_tool(func):
    def wrapper(*args, **kwargs):
        action = Action(name=func.__name__, args=args, kwargs=kwargs)
        decision = policy_engine.evaluate(action)
        
        if decision == Decision.DENY:
            raise PolicyViolation(decision.reason)
        elif decision == Decision.REQUIRE_APPROVAL:
            if not get_human_approval(action):
                raise PolicyViolation("Human denied the action")
        
        # Log the action
        audit_log.record(action, decision)
        
        return func(*args, **kwargs)
    return wrapper
```

### Audit Logging

All actions are logged with full context:

```python
{
    "timestamp": "2024-01-15T10:30:00Z",
    "action": "write_file",
    "args": {"path": "/workspace/report.md"},
    "decision": "ALLOW",
    "policy_matched": "filesystem.allowed_paths",
    "agent_id": "research-agent-001"
}
```

## Key Concepts Learned

1. **Deterministic vs Probabilistic Safety**: Why policy enforcement is more reliable than prompt engineering
2. **Defense in Depth**: Multiple layers of validation for robust security
3. **Audit Trails**: Importance of logging for compliance and debugging
4. **Principle of Least Privilege**: Only grant the permissions agents actually need

## Extending the Tutorial

- Add custom policy rules for your use case
- Implement human-in-the-loop approval workflows
- Connect to external policy management systems
- Add real-time monitoring and alerting

## Related Projects

- [LangChain](https://github.com/langchain-ai/langchain) - LLM application framework
- [Guardrails AI](https://github.com/guardrails-ai/guardrails) - Input/output validation for LLMs
