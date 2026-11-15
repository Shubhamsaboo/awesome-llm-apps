"""Page Watch: an always-on agent that briefs you when watched pages change."""

from __future__ import annotations

from google.adk.agents import LlmAgent

from .watch import run_page_watch


def preview_page_watch_brief(page_name: str = "", live: bool = False) -> dict:
    """Build a brief of material changes on watched web pages.

    Args:
        page_name: Optional page name filter, for example "pricing" or "terms".
        live: When true, fetch the configured watch list. Default is sample mode.

    Returns:
        A rendered text and HTML brief with before/after quotes and pre-filter verdicts.
    """

    return run_page_watch(
        live=live,
        live_model=False if not live else None,
        page_name=page_name,
    )


root_agent = LlmAgent(
    name="page_watch",
    model="gemini-3-flash-preview",
    description=(
        "Always-on page watcher that briefs you when pricing, limits, terms, "
        "or docs change in ways that matter."
    ),
    instruction="""
You are Page Watch, an always-on briefing agent for pages a team depends on:
vendor pricing, API rate limits, terms of service, status, and changelog pages.

Your job is to produce a short brief from the watch list:
- Report only material changes. Skip cosmetic chrome, timestamps, and banners.
- Quote the exact before and after text for every finding.
- Show the deterministic pre-filter verdict next to the model classification.
- If a hunk is marked source=prefilter_fallback, say that Gemini did not judge it.
- Tag impact as pricing, limits, legal, deprecation, availability, or other.
- When asked what changed, including a named page such as the pricing page,
  call preview_page_watch_brief.
- Separate rendering from delivery. Never claim that email or a webhook was sent.

The tool returns handoff-ready text and HTML. Scheduled delivery is a separate,
opt-in API path that defaults to dry-run.
""",
    tools=[preview_page_watch_brief],
)
