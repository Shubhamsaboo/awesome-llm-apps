# 🛡️ Aegis DQ MCP Agent

A Streamlit app that uses [Aegis DQ](https://github.com/aegis-dq/aegis-dq) as an MCP server to run agentic data quality validation — diagnosing failures, tracing root causes, and proposing SQL fixes through natural language.

## Features

- **Natural language interface** — ask the agent to validate data, search past runs, or compare results
- **LLM-powered diagnosis** — Aegis DQ explains *why* a check failed, not just *that* it failed
- **Full audit trail** — every validation run is logged to SQLite with FTS5 search
- **Demo dataset** — pre-loaded `orders` table with intentional data quality issues to explore
- **5 rule types** — null checks, range validation, accepted values, uniqueness, custom SQL

## Demo Dataset

The app seeds a local DuckDB database with an `orders` table containing **5 intentional data quality issues**:

| Issue | Rule | Severity |
|---|---|---|
| Negative `amount` (-50.00) | range check | HIGH |
| NULL `customer_id` | not_null | CRITICAL |
| Invalid `status` ("refunded") | accepted_values | HIGH |
| Duplicate `order_id` (ORD-001) | unique | HIGH |
| NULL `amount` | not_null | MEDIUM |

## Setup

### Prerequisites

- Python 3.10+
- OpenAI API key

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/mcp_ai_agents/aegis_dq_mcp_agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=your-openai-api-key
   ```
   Or copy the secrets example:
   ```bash
   cp mcp_agent.secrets.yaml.example mcp_agent.secrets.yaml
   # edit mcp_agent.secrets.yaml and add your key
   ```

4. Run the app:
   ```bash
   streamlit run main.py
   ```

## Example Prompts

**Run validation (fast, no LLM):**
```
Run the rules at /path/to/sample_rules.yaml against DuckDB with no_llm=true and tell me what failed.
```

**Check audit trail:**
```
Show me the last 5 validation runs.
```

**Search decisions:**
```
Search the audit trail for anything about null customer IDs.
```

**Compare runs:**
```
Compare the last two runs — what newly failed?
```

## How It Works

1. The app seeds a DuckDB database with sample orders data containing data quality issues
2. The MCP-Agent framework connects to the Aegis DQ MCP server (`aegis mcp`)
3. You ask questions in natural language
4. The agent calls Aegis DQ tools (`run_validation`, `list_runs`, `search_decisions`, etc.)
5. Results are displayed as structured markdown with severity grouping

## Aegis DQ MCP Tools Used

| Tool | What it does |
|---|---|
| `run_validation` | Run rules YAML against a warehouse |
| `list_runs` | List recent run IDs from the audit trail |
| `get_run_report` | Get the full report for a past run |
| `search_decisions` | Full-text search across all LLM decisions |
| `compare_reports` | Diff two runs — regressions and fixes |

## Links

- [Aegis DQ GitHub](https://github.com/aegis-dq/aegis-dq)
- [Aegis DQ Docs](https://aegis-dq.dev)
- [MCP-Agent Framework](https://github.com/lastmile-ai/mcp-agent)
