# Repository Guidelines

## Project Structure & Module Organization

- Frontend (Next.js + TypeScript): `src/app/**` (pages: `page.tsx`, `layout.tsx`, styles: `globals.css`). API route for CopilotKit: `src/app/api/copilotkit/route.ts`.
- Agent (ADK/Python): `agent/agent.py`, virtual env in `agent/.venv`, deps in `agent/requirements.txt`.
- Public assets: `public/`. Config: `next.config.ts`, `tsconfig.json`, `eslint.config.mjs`.
- Scripts: `scripts/run-agent.sh`, `scripts/setup-agent.sh`.

## Build, Test, and Development

- `npm run dev` — runs UI (`next dev --turbopack`) and the Python agent concurrently.
- `npm run dev:ui` — frontend only; useful for UI iteration.
- `npm run dev:agent` — agent only; activates `.venv` and runs `agent.py`.
- `npm run build` — production build for the Next.js app.
- `npm start` — serve the built app.
- `npm run lint` — lint the frontend with Next/ESLint.
- First-time setup installs the agent via `postinstall` (creates `.venv` and installs Python deps).

## Coding Style & Naming Conventions

- TypeScript/React: 2-space indent, PascalCase components, camelCase variables, file-based routing under `src/app/**`.
- Python agent: follow PEP 8; keep modules small and composable.
- Linting: Next.js ESLint config (`npm run lint`). Prefer explicit types in exported APIs.
- Components: colocate with usage; export from an `index.ts` when creating reusable modules.

## Testing Guidelines

- Currently no test harness. When adding tests:
  - Frontend: Jest/Vitest in `src/__tests__/` with `*.test.ts(x)`.
  - Agent: `pytest` in `agent/tests/` with `test_*.py`.
  - Aim for high coverage on data shaping (dashboard spec generation, adapters).

## Commit & Pull Request Guidelines

- Conventional Commits: `type(scope): message`.
  - Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`.
  - Example: `feat(charts): support pie charts`.
- PRs: clear description, linked issue, before/after screenshots or JSON spec samples, and testing notes.
- Keep PRs focused; call out env/config changes explicitly.

## Environment, Security & Config

- Place secrets in `.env.local` (frontend) and `agent/.env` (agent). Never commit secrets.
- Example keys (adjust to your provider):
  - Frontend: `NEXT_PUBLIC_CPK_ENDPOINT=/api/copilotkit`.
  - Agent: `GOOGLE_API_KEY=...` (Gemini), or `OPENAI_API_KEY=...` if applicable.
- Validate/sanitize prompts; avoid logging PII. Prefer `INFO` logs with redaction.

## Charts & CopilotKit Tips

- Dashboard spec (example): `{ "type": "line", "title": "Revenue", "x": "date", "y": "revenue" }`.
- Supported types to target in UI: `line`, `bar`, `pie`
- Naming: use singular `x`/`y` for series
- Recharts via CPK: map spec→props; e.g., `LineChart` with `dataKey={spec.y}` and `XAxis dataKey={spec.x}`;

## Architecture Overview

- Next.js app hosts CopilotKit UI and API route; Python agent performs ADK/Gemini orchestration. `npm run dev` runs both together.
