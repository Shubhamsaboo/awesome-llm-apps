## 🛡️ AI Agent Governance with Aegis

Add policy-based governance to AI agent tool calls using [Aegis](https://github.com/Acacian/aegis). Define YAML policies that control what actions agents can take, with automatic approval gates and full audit logging. Works with LangChain, CrewAI, OpenAI Agents SDK, Anthropic, and MCP.

### Features

- YAML-defined governance policies — no infrastructure required
- Risk-level classification (low → critical) for every agent action
- Approval gates: auto-approve safe reads, require confirmation for writes, block destructive operations
- Full audit trail with timestamps for every decision
- Interactive Streamlit dashboard to experiment with policies in real time

### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/single_agent_apps/ai_agent_governance_aegis
```

2. Install the required dependencies

```bash
pip install -r requirements.txt
```

3. Run the Streamlit App

```bash
streamlit run aegis_governance_app.py
```

No API keys needed — the demo uses a simulated agent executor so you can focus on how governance policies work.

### How it Works?

The app demonstrates Aegis governance through three agent scenarios:

- **CRM Agent** — Searches contacts, reads data, and updates a record. Read operations auto-approve; writes require confirmation.

- **Email Agent** — Reads a contact list and sends emails. Sending to individual recipients is medium risk; bulk sends are flagged for review.

- **Data Agent** — Searches, exports, bulk-updates, and attempts a delete. The delete action is blocked by policy before it ever reaches the executor.

Each scenario runs through the Aegis policy engine:

1. **Policy matching** — Each action type is matched against YAML rules using glob patterns (`search*`, `bulk_*`, etc.)
2. **Risk assessment** — Matched rules assign a risk level that determines the approval gate
3. **Approval gate** — `auto` proceeds immediately, `approve` requires confirmation, `block` denies execution
4. **Audit logging** — Every decision (including blocked actions) is logged with full context

Edit the YAML policy in the left panel to see how changing rules affects agent behavior in real time.

### Learn More

- **GitHub**: [github.com/Acacian/aegis](https://github.com/Acacian/aegis)
- **PyPI**: `pip install agent-aegis`
- **Integrations**: LangChain, CrewAI, OpenAI Agents SDK, Anthropic, MCP
