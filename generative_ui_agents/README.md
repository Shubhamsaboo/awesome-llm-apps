# 🖼️ Generative UI and Agentic Frontends

**Agents that render UI — not just text.**

Generative UI (Gen UI) apps let an LLM emit rich, interactive frontend components instead of (or in addition to) plain chat messages. The model decides *what to show*, the frontend renders real components, and the user can click, edit, and respond — closing the loop between reasoning and interface.

This section collects self-contained templates for building Gen UI apps across the common stacks:

- **AG-UI / CopilotKit** — streaming agent ↔ UI protocol for React apps
- **Vercel AI SDK** — `streamUI` / React Server Components generative UI
- **LangChain / LangGraph UI** — structured tool calls rendered as components
- **Custom tool-call → component renderers** — minimal DIY patterns in any framework

## What counts as a Gen UI template

A template belongs here if the agent's output drives the UI — e.g. the model calls a tool and the response renders as a form, chart, card, table, or interactive widget that the user can then act on. A chatbot that only streams markdown does **not** count; a chatbot that streams a bookable flight card, an editable plan, or a live-updating dashboard does.

## Template conventions

Each template in this directory should ship with:

- A `README.md` with a 1-paragraph description, a short demo (gif / screenshot / video), setup steps, and the model(s) it runs against
- Frontend source (typically a Next.js or Vite app) with the Gen UI components kept small and readable
- Backend / agent source (Python or TypeScript) that defines the tools and the component-rendering contract
- A working `.env.example` listing every key the template reads
- Provider-agnostic defaults where possible — Claude / Gemini / GPT / open models should all be swappable via config

## Contributing

Have a Gen UI template to add? Open a PR with a new subdirectory under `generative_ui_agents/` following the conventions above. Keep templates self-contained: no shared code across templates, and every template should run from a clean clone in three commands.
