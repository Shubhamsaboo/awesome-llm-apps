# 🔍 AI SEO Audit Team

The **AI SEO Audit Team** is an autonomous, multi-agent workflow built with Google ADK. It takes a webpage URL, crawls the live page, researches real-time SERP competition, and produces a polished, prioritized SEO optimization report. The app uses **Firecrawl via MCP (Model Context Protocol)** for accurate page scraping and Google's Gemini 2.5 Flash for analysis and reporting.

## Features

- **End-to-End On-Page SEO Evaluation**
  - Automated crawl of any public URL (Firecrawl MCP)
  - Structured audit of titles, headings, content depth, internal/external links, and technical signals
- **Competitive SERP Intelligence**
  - Google Search research for the inferred primary keyword
  - Analysis of top competitors, content formats, title patterns, and common questions
- **Actionable Recommendations**
  - Prioritized optimization roadmap with rationale and expected impact
  - Keyword strategy, schema opportunities, internal linking ideas, and measurement plan
  - Clean Markdown report ready for stakeholders or ticket creation
- **ADK Dev UI Integration**
  - Trace view of each agent step (crawl → SERP → report)
  - Easy environment variable management through `.env`

## Agent Workflow

| Step | Agent | Responsibilities |
| --- | --- | --- |
| 1 | **Page Auditor Agent** | Calls `firecrawl_scrape`, inspects page structure, summarizes technical/content signals, and infers target keywords. |
| 2 | **Serp Analyst Agent** | Consumes the SERP data, extracts patterns, opportunities, PAA questions, and differentiation angles. |
| 3 | **Optimization Advisor Agent** | Combines audit + SERP insights into a Markdown report with clear priorities and next steps. |

All agents run sequentially using ADK’s `SequentialAgent`, passing state between stages via the shared session.

## Requirements

### System Requirements
- **Python 3.10+** for Google ADK
- **Node.js** (for Firecrawl MCP server via npx)

### Python Dependencies

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

### API Keys

You will need valid API keys:

- `GOOGLE_API_KEY` – Gemini (Google AI Studio) for LLM + Google Search
- `FIRECRAWL_API_KEY` – Firecrawl MCP server ([get one here](https://firecrawl.dev/app/api-keys))

Set your environment variables (e.g., add to your shell profile or `export` in your terminal):

```bash
export GOOGLE_API_KEY=your_gemini_key
export FIRECRAWL_API_KEY=your_firecrawl_key
```

Alternatively, you can put these in a `.env` file if you prefer.

## Running the App with ADK Dev UI

1. **Activate your environment** (optional but recommended):
   ```bash
   cd advanced_ai_agents/multi_agent_apps/agent_teams/ai_seo_audit_team
   ```

2. **Install dependencies** (if not already):
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the ADK web UI** from the project root:
   ```bash
   adk web
   ```

4. In the UI:
   - Select the `ai_seo_audit_team` app.
   - Provide the target URL when prompted.
   - Watch the agents execute in the **Trace** panel (Firecrawl → Google Search → Report).

## Usage Tips

- Ensure the target URL is publicly accessible without auth requirements.
- The workflow is optimized for a single URL per run; start a new session for each distinct audit.
- The final report can be copied directly into docs, tickets, or shared with stakeholders.

## Folder Structure

```
ai_seo_audit_team/
├── agent.py          # Multi-agent workflow definitions
├── requirements.txt  # Minimal dependencies
├── __init__.py       # Module initialization
└── README.md         # You are here
```

## Next Steps & Extensibility

- Add automated evaluations via ADK Eval Sets for regression testing.
- Hook the Markdown report into Slack/email connectors or ticketing systems.
- Swap in alternative SERP providers (Serper, Tavily) if you prefer non-Google search APIs.
- Extend the workflow with additional agents (e.g., content brief generator, schema builder) using the shared session state.

Happy auditing! 🚀
