# 🖼️ Generative UI and Agentic Frontends

**Agents that render UI — not just text.**

Generative UI (Gen UI) apps let an LLM emit rich, interactive frontend components instead of (or in addition to) plain chat messages. The model decides *what to show*, the frontend renders real components, and the user can click, edit, and respond — closing the loop between reasoning and interface.

This section collects self-contained templates for building Gen UI apps across the common stacks:

- **AG-UI / CopilotKit** — streaming agent ↔ UI protocol for React apps
- **Vercel AI SDK** — `streamUI` / React Server Components generative UI
- **LangChain / LangGraph UI** — structured tool calls rendered as components
- **Custom tool-call → component renderers** — minimal DIY patterns in any framework
