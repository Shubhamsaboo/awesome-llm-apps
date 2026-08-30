# 🤝 Multi-Agent Trust Layer - Secure Agent-to-Agent Communication

Learn how to build a trust layer for multi-agent systems that enables secure delegation, trust scoring, and policy enforcement between AI agents.

## Features

- **Agent Identity**: Each agent has a verifiable identity with a human sponsor
- **Trust Scoring**: Behavioral monitoring with a 0-1000 trust score
- **Delegation Chains**: Cryptographically narrow scope when delegating tasks
- **Policy Enforcement**: Enforce compliance rules across agent interactions
- **Audit Trail**: Full observability of agent-to-agent communications

## How It Works

```
┌─────────────────┐         ┌─────────────────┐
│   Agent A       │◀───────▶│   Trust Layer   │
│  (Orchestrator) │   TLS   │                 │
└─────────────────┘         │  • Identity     │
                            │  • Trust Score  │
┌─────────────────┐         │  • Delegation   │
│   Agent B       │◀───────▶│  • Policy       │
│  (Specialist)   │   TLS   │  • Audit        │
└─────────────────┘         └─────────────────┘
```

1. **Registration**: Agents register with verified identity and human sponsor
2. **Trust Establishment**: Initial trust score based on sponsor reputation
3. **Delegation**: Parent agents can delegate tasks with narrowed permissions
4. **Monitoring**: All actions are tracked and trust scores updated
5. **Enforcement**: Policies determine what each agent can do

## Requirements

- Python 3.8+
- OpenAI API key (or any LLM provider)
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/multi_agent_apps/multi_agent_trust_layer
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

2. Run the trust layer demo:
   ```bash
   python multi_agent_trust_layer.py
   ```

3. Watch agents interact through the trust layer with full observability.

## Example: Agent Delegation Chain

```python
# Orchestrator agent creates a delegation for a specialist
delegation = trust_layer.create_delegation(
    from_agent="orchestrator-001",
    to_agent="researcher-002",
    scope={
        "allowed_actions": ["web_search", "summarize"],
        "max_tokens": 10000,
        "time_limit_minutes": 30,
        "allowed_domains": ["arxiv.org", "github.com"]
    },
    task_description="Research recent papers on AI safety"
)

# Researcher can only perform actions within the delegated scope
result = researcher.execute_with_delegation(
    delegation=delegation,
    action="web_search",
    params={"query": "AI safety papers 2024"}
)
```

## Trust Score System

Trust scores range from 0-1000:

| Score Range | Level | Permissions |
|-------------|-------|-------------|
| 900-1000 | Trusted | Full access within role |
| 700-899 | Standard | Normal operations |
| 500-699 | Probation | Limited actions, extra logging |
| 300-499 | Restricted | Human approval required |
| 0-299 | Suspended | No autonomous actions |

### Score Updates

```python
# Positive behaviors increase trust
+10: Successfully completed delegated task
+5:  Stayed within scope boundaries
+2:  Provided accurate information

# Negative behaviors decrease trust
-50: Attempted action outside scope
-30: Provided inaccurate information
-20: Exceeded resource limits
-100: Security violation
```

## Example Output

```
🤝 Multi-Agent Trust Layer Demo
================================

📋 Registering agents...
✅ Registered: orchestrator-001 (Human Sponsor: alice@company.com)
✅ Registered: researcher-002 (Human Sponsor: bob@company.com)
✅ Registered: writer-003 (Human Sponsor: carol@company.com)

🔐 Creating delegation chain...
✅ Delegation: orchestrator-001 → researcher-002
   Scope: web_search, summarize
   Time Limit: 30 minutes

🤖 Agent researcher-002 executing: web_search
   Query: "AI safety papers 2024"
✅ Action ALLOWED (within delegated scope)
   Trust Score: 850 → 860 (+10)

🤖 Agent researcher-002 executing: send_email
❌ Action DENIED (not in delegated scope)
   Trust Score: 860 → 810 (-50)

📊 Trust Scores:
   orchestrator-001: 900 (Trusted)
   researcher-002: 810 (Standard)
   writer-003: 850 (Standard)
```

## Key Concepts

### 1. Agent Identity

Every agent has a cryptographic identity tied to a human sponsor:

```python
@dataclass
class AgentIdentity:
    agent_id: str
    public_key: str
    human_sponsor: str  # Accountable human
    organization: str
    roles: List[str]
    created_at: datetime
```

### 2. Delegation Chains

Delegations form a chain where each link can only narrow scope:

```python
@dataclass  
class Delegation:
    delegation_id: str
    parent_agent: str
    child_agent: str
    scope: DelegationScope
    signature: str  # Signed by parent
    parent_delegation: Optional[str]  # Links to parent's delegation
```

### 3. Policy Enforcement

Policies define what agents can do based on trust and role:

```python
policies:
  researcher:
    base_trust_required: 500
    allowed_actions:
      - web_search
      - read_document
      - summarize
    denied_actions:
      - execute_code
      - send_email
    resource_limits:
      max_tokens_per_hour: 100000
      max_api_calls_per_minute: 60
```

## Architecture

```
┌────────────────────────────────────────────────────┐
│                   Trust Layer                       │
├─────────────┬─────────────┬─────────────┬──────────┤
│  Identity   │  Trust      │  Delegation │  Policy  │
│  Registry   │  Scoring    │  Manager    │  Engine  │
├─────────────┴─────────────┴─────────────┴──────────┤
│                   Audit Logger                      │
└────────────────────────────────────────────────────┘
         ▲              ▲              ▲
         │              │              │
    ┌────┴────┐    ┌────┴────┐    ┌────┴────┐
    │ Agent A │    │ Agent B │    │ Agent C │
    └─────────┘    └─────────┘    └─────────┘
```

## Extending the Tutorial

- Add cryptographic signatures for delegation verification
- Implement reputation systems across organizations
- Add real-time trust score visualization
- Connect to external identity providers (OAuth, SAML)
- Implement secure communication channels (mTLS)

## Related Projects

- [LangGraph](https://github.com/langchain-ai/langgraph) - Multi-agent orchestration
- [CrewAI](https://github.com/crewAIInc/crewAI) - Multi-agent framework
- [AutoGen](https://github.com/microsoft/autogen) - Multi-agent conversations
