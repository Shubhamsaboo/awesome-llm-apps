# Open Generative UI Demo

A hosted gallery of AI-generated visualizations — describe what you want in plain English, watch the agent compose a live, interactive component for you. Powered by the [Open Generative UI](https://github.com/CopilotKit/OpenGenerativeUI) framework, [CopilotKit](https://github.com/CopilotKit/CopilotKit), and [AG-UI](https://github.com/ag-ui-protocol/ag-ui).

- **Live demo:** [opengenerativeui.copilotkit.ai](https://opengenerativeui.copilotkit.ai/)
- **Source:** [`CopilotKit/OpenGenerativeUI`](https://github.com/CopilotKit/OpenGenerativeUI)

https://github.com/user-attachments/assets/ed28c734-e54e-4412-873f-4801da544a7f

https://github.com/user-attachments/assets/ba7db70d-07c0-49af-b221-f962f30245e2

**Gen UI concept — open-ended generation from a prompt.** The agent isn't picking from a fixed catalogue of components; it's composing a fresh visualization on demand and streaming it into the page. The hosted gallery samples what's possible:

- **3D / animation** — an interactive airplane with pitch/roll/yaw, a solar system, an audio equalizer
- **Data viz** — KPI dashboards with charts, trend lines, and filters
- **Diagrams** — binary search step-throughs, neural-net architectures, sorting visualizers
- **UI components** — weather cards, invoice cards, pomodoro timers

Every result is editable — the same prompt can be re-run, refined, or branched into a variation. The gallery is the agent's "what if?" space.

## How it relates to the rest of this section

- **Generative UI Starter Project** (in this repo) → a CopilotKit + LangGraph starter showing the shared-state pattern (and A2UI declarative gen UI) on a kanban surface.
- **Open Generative UI Demo** (this entry) → the hosted gallery showing the open-ended generation framework's range.

If you want to ship something on the shared-state / declarative side, start with the Generative UI Starter Project. If you want to feel what open-ended generation can produce, start here.

## Run it locally

```bash
git clone https://github.com/CopilotKit/OpenGenerativeUI
cd OpenGenerativeUI
pnpm install
pnpm dev
```

See the upstream [`README`](https://github.com/CopilotKit/OpenGenerativeUI) for the full setup, including agent configuration and required API keys.

## Learn more

- [Open Generative UI on GitHub](https://github.com/CopilotKit/OpenGenerativeUI)
- [CopilotKit Generative UI docs](https://docs.copilotkit.ai/generative-ui)
- [AG-UI protocol](https://docs.ag-ui.com/introduction)

## License

Upstream license applies — see [`CopilotKit/OpenGenerativeUI`](https://github.com/CopilotKit/OpenGenerativeUI).
