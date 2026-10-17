# Contributing

Thanks for helping improve Awesome LLM Apps. Contributions can add an agent, skill, or RAG example, improve an existing example, fix a bug, or clarify its documentation.

## Before you start

- Search the [open issues](https://github.com/Shubhamsaboo/awesome-llm-apps/issues) and [pull requests](https://github.com/Shubhamsaboo/awesome-llm-apps/pulls) for related work so effort is not duplicated.
- For a larger feature or a new project, open an issue first to discuss its fit and placement.
- Browse nearby folders and follow their README, dependency, and configuration conventions. Examples are grouped by type under folders such as `starter_ai_agents/`, `advanced_ai_agents/`, `rag_tutorials/`, `voice_ai_agents/`, and `agent_skills/`.

## Make a change

1. Fork the repository and create a branch for your change.
2. Keep the change focused. For a new example, include a README with setup, required environment variables, and run instructions; keep credentials out of the repository.
3. Run the example's documented checks or, at minimum, follow its setup and run instructions to verify the change. For an agent skill, run the relevant checks in `.github/workflows/skill-evals.yml` and update the skill registry and README listing when needed.
4. If you add or rename a listed project or skill, update the corresponding entry in the root `README.md`.
5. Commit your change and open a pull request against `main`. Describe what changed, why it helps, and how you checked it. Include screenshots or sample output when they make the result easier to review.

Please keep pull requests focused and be responsive to review feedback. All contributions are covered by the repository's Apache-2.0 license.
