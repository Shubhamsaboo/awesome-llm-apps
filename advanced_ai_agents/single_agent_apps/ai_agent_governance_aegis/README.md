## 🛡️ AI CRM Agent with YAML Policy Governance

An OpenAI-powered CRM agent where GPT-4o-mini autonomously selects and calls tools via function calling, while every tool call is evaluated against editable YAML policy rules before execution — auto-approving safe reads and blocking destructive operations like bulk deletes.

### Features

- **Real OpenAI function calling** — GPT-4o-mini autonomously decides which CRM tools to call each turn
- **YAML governance policies** — define risk levels and approval gates for each action type, editable in the sidebar
- **Blocked action feedback loop** — when a tool call is blocked by policy, the LLM receives the reason and suggests a safer alternative
- **Full audit trail** — every governance decision is logged with risk level and result
- **Multi-turn chat** — persistent conversation with session state

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

3. Get your OpenAI API Key

   - Sign up at [platform.openai.com](https://platform.openai.com/)
   - Create an API key under API Keys settings
   - You'll enter it in the app's sidebar when running

4. Run the Streamlit App

```bash
streamlit run aegis_governance_app.py
```

### How it Works?

The app runs a GPT-4o-mini agent with six CRM tools: `search_contacts`, `read_record`, `update_record`, `send_email`, `export_data`, and `delete_records`. Each tool call goes through a governance pipeline using the [agent-aegis](https://github.com/Acacian/aegis) library:

1. **User sends a natural language request** — e.g., "Delete all inactive customers"
2. **GPT-4o-mini decides which tools to call** — via OpenAI function calling (real API calls every turn)
3. **Each tool call is evaluated against YAML policy** — glob pattern matching determines risk level and approval gate
4. **Allowed actions execute** — results are fed back to the LLM for the next step
5. **Blocked actions return governance feedback** — the LLM receives the block reason and suggests a safer alternative
6. **Full audit trail** — every decision is logged and displayed in a side panel

**Default policy rules:**

| Tool | Risk Level | Policy |
|------|-----------|--------|
| `search_contacts` | 🟢 low | Auto-approve |
| `read_record` | 🟢 low | Auto-approve |
| `update_record` | 🟡 medium | Require approval |
| `send_email` | 🟡 medium | Require approval |
| `export_data` | 🟠 high | Require approval |
| `delete_records` | 🔴 critical | Block |

Try asking the agent to "delete all customer records" — the policy will block the delete, and the LLM will suggest archiving instead. Then edit the YAML policy in the sidebar to allow deletes and try again.

### Example Output (actual GPT-4o-mini responses)

**"Search for our enterprise customers"**
```
✅ 🟢 search_contacts({"query": "enterprise"}) → low → executed

Agent: I found one enterprise customer:
1. Alice Kim — alice@example.com (Enterprise tier)
```

**"Look up customer C-001 and update their plan to premium"**
```
✅ 🟢 read_record({"record_id": "C-001"}) → low → executed
✅ 🟡 update_record({"record_id": "C-001", "field": "plan", "value": "premium"}) → medium → executed

Agent: I found customer Alice Kim (ID: C-001) and successfully updated her plan
from enterprise to premium.
```

**"Delete all inactive customer records"**
```
🚫 🔴 delete_records({"target": "inactive customers"}) → critical → BLOCKED

Agent: The request to delete all inactive customer records was blocked due to
critical risk policy. I recommend reviewing the inactive records first — would
you like me to search for or export them instead?
```
