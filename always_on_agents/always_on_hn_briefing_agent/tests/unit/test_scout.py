import datetime as dt

from always_on_hn_briefing_agent.scout import (
    AGENT_KEYWORDS,
    PACIFIC,
    curate_stories,
    render_brief,
    run_ambient_scout,
)


def test_curate_stories_returns_ranked_agent_signals():
    stories = curate_stories(live=False, top_n=3)

    assert len(stories) == 3
    assert stories[0].points >= stories[-1].points
    assert all(
        any(keyword in f"{story.title} {story.summary}".lower() for keyword in AGENT_KEYWORDS)
        for story in stories
    )


def test_render_brief_includes_text_html_and_next_actions():
    stories = curate_stories(live=False, top_n=2)
    now = dt.datetime(2026, 6, 8, 9, 0, tzinfo=PACIFIC)

    brief = render_brief(stories, watch_mode="sample", now=now)

    assert brief.subject == "AgentScout Hacker News brief - 2026-06-08"
    assert "AgentScout Hacker News Engineering Brief" in brief.text
    assert "<ol>" in brief.html
    assert len(brief.next_actions) == 3


def test_run_ambient_scout_returns_delivery_handoff_payload():
    payload = run_ambient_scout(live=False, top_n=1)

    assert payload["watch_mode"] == "sample"
    assert payload["stories"]
    assert "text" in payload
    assert "html" in payload
    assert "delivery_note" in payload
