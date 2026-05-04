# Open Generative UI Demo

A minimal CopilotKit + LangGraph (Python) starter focused on a single Generative UI pattern: **open-ended generation**. The agent generates complete HTML / CSS / JavaScript on demand and streams it live into a sandboxed iframe inside the chat — no predefined components, no schema, just describe what you want.

- **Live demo (hosted gallery):** [opengenerativeui.copilotkit.ai](https://opengenerativeui.copilotkit.ai/)
- **Docs:** [Open Generative UI](https://docs.copilotkit.ai/generative-ui/open-generative-ui)

**What "open-ended" means here.** The runtime injects a `generateSandboxedUi` tool into the model's tool list. When the model calls it, the runtime streams the generated markup as `open-generative-ui` activity events into the chat, where CopilotKit's built-in `OpenGenerativeUIRenderer` mounts it inside a sandboxed iframe (no same-origin access, can load CDN libraries like Chart.js / D3 / Three.js via `<script>` tags).

**Try one of these prompts:**

- *Build me a modern calculator with clickable buttons.*
- *Build a pomodoro timer with a circular progress ring.*
- *Render a KPI dashboard from the company financials.* (calls `query_data` first, then renders with Chart.js)
- *Build an animated solar system with eight planets orbiting at different speeds.*
- *Build a step-through binary search visualizer on a sorted array of 16 numbers.*

The full set of seeded prompts lives in [`src/hooks/use-example-suggestions.tsx`](src/hooks/use-example-suggestions.tsx).

## Run it locally

The code in this folder was scaffolded with the CopilotKit CLI (`npx copilotkit@latest create -f langgraph-py`) and then trimmed to the Open Generative UI surface only — A2UI catalog, MCP Apps, kanban canvas, and chart components were removed. Prerequisites: Node.js 18+, Python 3.12+, [uv](https://docs.astral.sh/uv/), and an OpenAI API key.

```bash
cd generative_ui_agents/open-generative-ui-demo
npm install              # also installs the Python agent via `uv sync`
cp .env.example .env     # then set OPENAI_API_KEY
npm run dev              # boots the Next.js UI (:3000) and the LangGraph agent (:8123)
```

## How it's wired

Open Generative UI is enabled with **one flag** on the runtime side and **one flag** on the React provider — the rest of the stack is plain CopilotKit + LangGraph.

**Next.js runtime** ([`src/app/api/copilotkit/[[...slug]]/route.ts`](src/app/api/copilotkit/%5B%5B...slug%5D%5D/route.ts)):

```ts
const runtime = new CopilotRuntime({
  agents: { default: defaultAgent },
  runner: new InMemoryAgentRunner(),
  openGenerativeUI: true,   // ← injects the generateSandboxedUi tool
});
```

**React provider** ([`src/app/layout.tsx`](src/app/layout.tsx)):

```tsx
<CopilotKit
  runtimeUrl="/api/copilotkit"
  openGenerativeUI={{}}      // ← auto-registers OpenGenerativeUIRenderer
>
  {children}
</CopilotKit>
```

**LangGraph agent** ([`agent/main.py`](agent/main.py)) stays plain — no special middleware. The agent gets the `generateSandboxedUi` tool injected by the runtime and decides when to call it based on the system prompt:

```python
agent = create_agent(
    model=ChatOpenAI(model="gpt-5.4-mini"),
    tools=[query_data],                        # plus generateSandboxedUi from runtime
    middleware=[CopilotKitMiddleware()],
    system_prompt="...call generateSandboxedUi when the user asks for a visual...",
)
```

## What got trimmed vs. the langgraph-py scaffold

The CopilotKit `langgraph-py` scaffold ships a kitchen-sink demo (controlled gen UI, A2UI declarative, MCP Apps, todos shared state, charts). This starter trims it to a single concern. Removed:

- `agent/src/a2ui_*.py` and `agent/src/a2ui/` — A2UI tools and schemas
- `agent/src/todos.py` — kanban shared-state tools
- `src/app/declarative-generative-ui/` — A2UI catalog (definitions + renderers)
- `src/components/example-canvas/` — todo kanban canvas
- `src/components/generative-ui/` — chart components for tool-call rendering
- `src/components/example-layout/` — chat / app split layout (replaced with a centered chat)
- Runtime config: removed `a2ui` and `mcpApps` blocks; kept only `openGenerativeUI: true`

If you want any of those patterns back, scaffold a fresh full-spectrum copy with `npx copilotkit@latest create -f langgraph-py` and copy the relevant pieces over.

## Learn more

- [Open Generative UI docs](https://docs.copilotkit.ai/generative-ui/open-generative-ui)
- [OpenGenerativeUI hosted gallery source](https://github.com/CopilotKit/OpenGenerativeUI) — the production version of this pattern
- [Generative UI overview](https://www.copilotkit.ai/generative-ui)
- [AG-UI protocol](https://docs.ag-ui.com/introduction)
- [LangGraph](https://www.langchain.com/langgraph)

## License

MIT — upstream license from the CopilotKit `langgraph-py` scaffold applies; see [`LICENSE`](LICENSE).
