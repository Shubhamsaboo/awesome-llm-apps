# Generative UI Full Spectrum Demo

A hosted CopilotKit + LangGraph (Python) example that walks through every major Generative UI pattern in one app — controlled, declarative, and open-ended — over the [AG-UI](https://github.com/ag-ui-protocol/ag-ui) protocol.

- **Live demo:** [langgraph-py.examples.copilotkit.ai](https://langgraph-py.examples.copilotkit.ai/)
- **Source:** [`CopilotKit/CopilotKit` → `examples/integrations/langgraph-python`](https://github.com/CopilotKit/CopilotKit/tree/main/examples/integrations/langgraph-python)

**Gen UI concept — the full spectrum.** Generative UI is not one technique; it's a spectrum of how much control the agent has over the rendered surface:

| Pattern | Control | Protocol | What it looks like |
|---|---|---|---|
| **Controlled** | Developer-defined components, agent triggers | AG-UI tool calls | Agent calls a tool → the matching React component renders inline. |
| **Declarative** | Agent emits a UI spec, frontend renders it | A2UI / Open-JSON-UI | Agent returns a structured tree; frontend maps it to real components. |
| **Open-ended** | Agent ships its own app | MCP Apps | Agent provisions a sandboxed app and embeds it in the chat. |

This demo runs all three side by side against the same LangGraph agent so you can feel the trade-off between control, freedom, and predictability without leaving the page.

## Run it locally

The demo lives inside the CopilotKit monorepo. To run your own copy:

```bash
git clone https://github.com/CopilotKit/CopilotKit
cd CopilotKit/examples/integrations/langgraph-python
pnpm install
pnpm dev
```

See the example's [`README`](https://github.com/CopilotKit/CopilotKit/tree/main/examples/integrations/langgraph-python) for environment variables and the Python agent setup (`uv sync`).

You can also scaffold a fresh copy with the CopilotKit CLI:

```bash
npx copilotkit@latest create -f langgraph-py
```

## Learn more

- [Generative UI overview](https://www.copilotkit.ai/generative-ui)
- [Generative UI showcase repo](https://github.com/CopilotKit/CopilotKit/tree/main/examples/showcases/generative-ui) — explainer for the three patterns
- [AG-UI protocol](https://docs.ag-ui.com/introduction)
- [LangGraph](https://www.langchain.com/langgraph)

## License

Upstream license applies — see [`CopilotKit/CopilotKit`](https://github.com/CopilotKit/CopilotKit).
