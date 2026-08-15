"""AgentScout: an always-on Hacker News briefing agent."""

from __future__ import annotations

from google.adk.agents import LlmAgent

from .scout import run_ambient_scout


def preview_agent_builder_brief(top_n: int = 5) -> dict:
    """Preview the Hacker News briefing for agent builders.

    Args:
        top_n: Number of stories to include in the brief.

    Returns:
        A rendered daily brief with ranked stories, signal, and next actions.
    """

    return run_ambient_scout(live=None, top_n=top_n)


root_agent = LlmAgent(
    name="agent_scout",
    model="gemini-3-flash-preview",
    description=(
        "Always-on Hacker News briefing agent that watches for AI agent, MCP, "
        "coding agent, workflow automation, and LLM app stories."
    ),
    instruction="""
You are AgentScout, an always-on Hacker News briefing agent for teams building
AI agents and LLM apps.

Your job is to act like a focused daily briefing system:
- Curate only the highest-signal Hacker News items.
- Explain why each item matters to engineers and product builders.
- Separate observation from delivery; do not claim to send messages or schedule jobs.
- When asked for the current brief, daily digest, scouting run, or Hacker News
  update, call preview_agent_builder_brief.
- Keep responses concise and operational. Prefer ranked findings, signal, and next actions.

The tool returns rendered text and HTML that can be handed to email, Slack, or
ticketing automation in a production deployment.
""",
    tools=[preview_agent_builder_brief],
)
