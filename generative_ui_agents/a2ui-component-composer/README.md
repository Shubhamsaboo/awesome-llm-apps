# A2UI Component Composer

A hosted playground for [A2UI](https://github.com/google/A2UI) — Google's declarative protocol for agent-generated UI — wired up to [CopilotKit](https://github.com/CopilotKit/CopilotKit) and [AG-UI](https://github.com/ag-ui-protocol/ag-ui). Describe a widget, watch the agent emit an A2UI JSON spec, and see it render as a real, interactive component.


https://github.com/user-attachments/assets/ca6fdfd9-0216-49bc-ad03-0d671566cb4f


- **Live demo:** [a2ui-composer.ag-ui.com](https://a2ui-composer.ag-ui.com/)
- **Tutorial:** [docs.copilotkit.ai → CopilotKit + A2UI](https://docs.copilotkit.ai/a2a/generative-ui/declarative-a2ui)
- **A2UI protocol:** [`google/A2UI`](https://github.com/google/A2UI)

**Gen UI concept — declarative generative UI.** A2UI sits in the middle of the gen-UI spectrum. The agent doesn't trigger a developer-defined component (controlled), and it doesn't ship its own app (open-ended) — it emits a *structured spec*, and the frontend maps that spec onto a known widget set. Two halves of the contract:

- **Catalogue** — a basic + custom widget gallery and an icon set the agent can reference.
- **Spec** — a JSON document the agent produces; the composer renders it and supports JSON playback so you can replay any composition.

The Composer is the easiest way to *see* declarative gen UI behave: prompt → spec → live widgets, all in one screen, with the JSON visible alongside.

## What you can do

- **Compose** — prompt the agent to build a widget; iterate by refining the prompt.
- **Inspect** — open the JSON A2UI spec the agent emitted; edit it directly.
- **Replay** — play back a saved JSON spec to reproduce any composition.
- **Mix widgets** — combine entries from the basic and custom catalogues into a single layout.

## Learn more

- [A2UI protocol (Google)](https://github.com/google/A2UI)
- [Declarative A2UI tutorial (CopilotKit)](https://docs.copilotkit.ai/a2a/generative-ui/declarative-a2ui)
- [A2UI spec docs (CopilotKit)](https://docs.copilotkit.ai/learn/generative-ui/specs/a2ui)
- [AG-UI protocol](https://docs.ag-ui.com/introduction)

## License

Upstream licenses apply — see [`google/A2UI`](https://github.com/google/A2UI) for the protocol and [`CopilotKit/CopilotKit`](https://github.com/CopilotKit/CopilotKit) for the React integration.
