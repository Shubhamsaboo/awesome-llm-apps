# AG-UI Agent Framework Integration Dojo

A live, interactive showcase of [AG-UI](https://github.com/ag-ui-protocol/ag-ui) — the open protocol that connects AI agents to user-facing applications — running across every major agent framework side by side.

- **Live demo:** [dojo.ag-ui.com](https://dojo.ag-ui.com/langgraph/feature/tool_based_generative_ui)
- **Source:** [`ag-ui-protocol/ag-ui` → `apps/dojo`](https://github.com/ag-ui-protocol/ag-ui/tree/main/apps/dojo)

**Gen UI concept — protocol-level interop.** Each "feature" in the Dojo (tool-based generative UI, shared state, human-in-the-loop, agentic chat, predictive state updates, etc.) is implemented once in the frontend and wired to multiple agent backends — LangGraph, Mastra, CrewAI, Agno, Pydantic AI, LlamaIndex, ADK, and more. Same UI, same protocol, different agents. The Dojo is how you see *which* generative UI patterns AG-UI supports, *how* they look in practice, and *which* frameworks have shipped support for each.

## What you can explore

| Pattern | What it shows |
|---|---|
| **Tool-Based Generative UI** | Agents emit tool calls that map directly to React components rendered inline. |
| **Shared State** | Bidirectional state sync between the agent and the frontend — both can read and update. |
| **Human-in-the-Loop** | The agent pauses mid-run to ask the user for input or approval. |
| **Agentic Chat** | A baseline chat experience with full AG-UI event streaming. |
| **Predictive State Updates** | Optimistic UI updates streamed from the agent before tools complete. |

Each pattern is implemented per framework so you can compare behavior, latency, and ergonomics across agent stacks without leaving the page.

## Run it locally

The Dojo lives in the AG-UI monorepo. To run it yourself:

```bash
git clone https://github.com/ag-ui-protocol/ag-ui
cd ag-ui
pnpm install
pnpm --filter dojo dev
```

See [`apps/dojo/README.md`](https://github.com/ag-ui-protocol/ag-ui/blob/main/apps/dojo/README.md) in the AG-UI repo for the full setup, including running the framework-specific agent backends.

## Learn more

- [AG-UI protocol docs](https://docs.ag-ui.com/introduction)
- [AG-UI on GitHub](https://github.com/ag-ui-protocol/ag-ui)
- [CopilotKit](https://github.com/CopilotKit/CopilotKit) — the React SDK most Dojo features are built on top of

## License

The upstream Dojo is licensed under the AG-UI repo's license — see [`ag-ui-protocol/ag-ui`](https://github.com/ag-ui-protocol/ag-ui) for details.
