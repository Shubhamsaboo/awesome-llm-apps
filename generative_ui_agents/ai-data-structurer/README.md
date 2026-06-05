# AI Data Structurer

Paste messy data -- CSV, JSON, plain text, a markdown table -- and an AI agent figures out the structure, renders it as interactive UI, and lets you reshape it through conversation.

"Group by region." "Show me which are declining." "Summarize." Each request produces a different visualization, chosen by the agent at runtime.

Built with [CopilotKit](https://github.com/CopilotKit/CopilotKit), [AG-UI](https://github.com/ag-ui-protocol/ag-ui), [A2UI](https://a2ui.org/specification/), and [LangGraph](https://www.langchain.com/langgraph).

## What it teaches

**Dynamic A2UI component selection.** Every other demo in this repo maps agent output to a fixed component. This one lets the agent choose: DataTable, CardGrid, ComparisonView, Timeline, SummaryCard, or a composed dashboard -- based on the data shape AND what you asked for. Same data, different components, steered by conversation.

## Demo flow

```
1. Paste CSV data
   -> Agent detects structure, renders a DataTable

2. "Group by region"
   -> Agent switches to CardGrid with per-group totals

3. "Show me which regions are declining"
   -> Agent switches to ComparisonView with trend arrows

4. "Summarize"
   -> Agent switches to SummaryCard with key stats

5. Paste more data: "Here's Q2, add it"
   -> Agent merges and re-renders
```

## Quick start

```bash
npm install
cp .env.example .env
# Add your OPENAI_API_KEY to .env
npm run dev
```

Opens at http://localhost:3000. Agent runs on port 8123.

## How it works

### Agent tools (Python)

| Tool | What it does |
|------|-------------|
| `detect_schema` | Parses CSV/JSON/markdown/text. Returns columns with types (string, number, currency, date), rows, row count. |
| `transform_data` | Groups, sorts, filters, aggregates, calculates trends. |
| `pick_component` | Chooses the best A2UI component based on data shape + user intent. |
| `generate_a2ui` | Secondary LLM generates the A2UI component tree with real data. |

### A2UI components (React)

| Component | When the agent picks it |
|-----------|------------------------|
| DataTable | Default first render, tabular data |
| CardGrid | "Group by X" -- colored cards with per-group totals |
| ComparisonView | "Show trends" / "compare" -- side-by-side with directional arrows |
| SummaryCard | "Summarize" -- key aggregate stats |
| Timeline | Date-based data + "show timeline" |
| DashboardCard + Metric + charts | Composed dashboards with KPIs |

### The selection logic

```
User pastes data
  -> detect_schema (parse + type columns)
  -> pick_component (data shape + intent -> component name)
  -> generate_a2ui (render with real data)

User asks to transform
  -> transform_data (group/sort/filter/aggregate/trend)
  -> pick_component (new shape + new intent -> DIFFERENT component)
  -> generate_a2ui (re-render)
```

The agent picks a different component each time. The frontend has all components registered. The agent decides which one fits. That's the pattern.

## Project structure

```
ai-data-structurer/
  agent/                         # Python + LangGraph backend
    main.py                      # Agent entry point
    src/
      tools.py                   # detect_schema, transform_data, pick_component
      a2ui_dynamic_schema.py     # Dynamic A2UI generation

  src/                           # Next.js + CopilotKit frontend
    app/
      page.tsx                   # Main page: chat + paste area
      declarative-generative-ui/
        definitions.ts           # A2UI component schemas (Zod)
        renderers.tsx            # A2UI React renderers
    components/
      paste-area/                # Data input textarea
      example-layout/            # Chat + data panel layout

  package.json
  .env.example
```

## Sample data to paste

**CSV:**
```
Name,Region,Q1 Sales,Q2 Sales
Acme Corp,West,45000,52000
Beta Inc,East,38000,41000
Gamma Ltd,West,62000,58000
Delta Co,East,29000,35000
```

**JSON:**
```json
[{"name": "Acme", "region": "West", "revenue": 45000, "employees": 120}]
```

**Markdown table:**
```
| Product | Category | Price | Stock |
|---------|----------|-------|-------|
| Widget A | Hardware | $29.99 | 150 |
| Widget B | Software | $9.99 | unlimited |
```

## Stack

- **Frontend**: Next.js 16 + React 19 + Tailwind 4
- **Agent**: Python + LangGraph + OpenAI
- **Protocol**: AG-UI events + A2UI component schemas
- **UI toolkit**: CopilotKit v2 + Recharts

## Troubleshooting

**Agent won't connect:** Make sure port 8123 is free and OPENAI_API_KEY is set in `.env`.

**Python errors:** Run `npm run install:agent` to reinstall agent dependencies.

## License

Apache-2.0
