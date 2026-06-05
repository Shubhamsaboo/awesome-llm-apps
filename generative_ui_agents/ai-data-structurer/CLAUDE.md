# AI Data Structurer

## Purpose

Demo showing dynamic A2UI component selection. The agent chooses which component to render based on data shape + user intent. No other demo in this repo does this.

## Architecture

Flat npm project. Next.js frontend at root, Python agent in `agent/`.

### Key files

| File | What it does |
|------|-------------|
| `agent/main.py` | Agent entry point. Tools: detect_schema, transform_data, pick_component, generate_a2ui |
| `agent/src/tools.py` | Data parsing (CSV/JSON/markdown/text), transforms (group/sort/filter/aggregate/trend), component selection |
| `agent/src/a2ui_dynamic_schema.py` | Secondary LLM generates A2UI component tree |
| `src/app/declarative-generative-ui/definitions.ts` | A2UI component schemas (Zod) |
| `src/app/declarative-generative-ui/renderers.tsx` | A2UI React renderers |
| `src/components/paste-area/index.tsx` | Data input textarea |
| `src/app/page.tsx` | Main page wiring |

### Components in the catalog

DataTable, CardGrid, ComparisonView, SummaryCard, Timeline, DashboardCard, Metric, BarChart, PieChart, Badge, Title, Row, Column, Button.

### Agent tools

- `detect_schema(raw_input)` -> parsed rows + column types
- `transform_data(data, operation, params)` -> transformed result
- `pick_component(data_shape, user_intent)` -> component name
- `generate_a2ui()` -> renders via secondary LLM

### Config invariants

- `agent/langgraph.json` graphs key (`sample_agent`) must match `route.ts` graphId
- `.env` needs `OPENAI_API_KEY`

## Development

```bash
npm install && npm run dev
```

Frontend: port 3000. Agent: port 8123.
