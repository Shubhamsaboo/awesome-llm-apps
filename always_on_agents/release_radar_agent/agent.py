"""Release Radar: an always-on dependency release briefing agent."""

from __future__ import annotations

from google.adk.agents import LlmAgent

from .radar import run_release_radar


def preview_dependency_brief(manifest_path: str = "", top_n: int = 10) -> dict:
    """Build today's dependency release brief.

    Args:
        manifest_path: Optional path to requirements.txt or package.json.
        top_n: Maximum number of important releases to include.

    Returns:
        A rendered text and HTML brief with ranked dependency changes.
    """

    return run_release_radar(
        manifest_path=manifest_path or None,
        live=None,
        top_n=top_n,
    )


root_agent = LlmAgent(
    name="release_radar",
    model="gemini-3-flash-preview",
    description=(
        "Always-on dependency release agent that finds breaking changes, "
        "deprecations, security fixes, and major-version upgrades."
    ),
    instruction="""
You are Release Radar, an always-on dependency change briefing agent for
software teams.

Your job is to produce a short daily brief from the user's dependency manifest:
- Surface breaking changes, deprecations, security fixes, and major versions.
- Skip routine patch noise.
- Explain why each release matters to this project in one line.
- Include the release-notes link for every finding.
- When asked for today's brief or a dependency update, call
  preview_dependency_brief.
- Separate rendering from delivery. Never claim that email or a webhook was sent.

The tool returns handoff-ready text and HTML. Scheduled delivery is a separate,
opt-in API path that defaults to dry-run.
""",
    tools=[preview_dependency_brief],
)

