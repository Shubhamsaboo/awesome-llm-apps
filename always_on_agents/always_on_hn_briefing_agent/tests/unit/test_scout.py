import datetime as dt

from always_on_hn_briefing_agent.scout import (
    AGENT_KEYWORDS,
    PACIFIC,
    HNFrontPageParser,
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


def _hn_row(item_id, rank, href, title, site, points, comments):
    return (
        f'<tr class="athing submission" id="{item_id}">'
        f'<td align="right" valign="top" class="title"><span class="rank">{rank}.</span></td>'
        f'<td class="title"><span class="titleline"><a href="{href}">{title}</a>'
        f'<span class="sitebit comhead"> (<a href="from?site={site}">'
        f'<span class="sitestr">{site}</span></a>)</span></span></td></tr>'
        f'<tr><td colspan="2"></td><td class="subtext"><span class="subline">'
        f'<span class="score" id="score_{item_id}">{points} points</span> by '
        f'<a href="user?id=someone">someone</a> '
        f'<span class="age" title="2026-06-08T09:00:00"><a href="item?id={item_id}">1 hour ago</a></span> '
        f'<span id="unv_{item_id}"></span> | <a href="hide?id={item_id}&amp;goto=news">hide</a> | '
        f'<a href="item?id={item_id}">{comments}&nbsp;comments</a></span></td></tr>'
    )


def test_front_page_parser_reads_every_story_from_hn_markup():
    markup = "<table>" + "".join(
        [
            _hn_row(1, 1, "https://example.com/agents", "Agent workflows", "example.com", 120, 45),
            _hn_row(2, 2, "https://example.org/mcp", "MCP servers", "example.org", 80, 12),
        ]
    ) + "</table>"

    parser = HNFrontPageParser()
    parser.feed(markup)

    assert [(s["title"], s["url"], s["points"], s["comments"]) for s in parser.stories] == [
        ("Agent workflows", "https://example.com/agents", 120, 45),
        ("MCP servers", "https://example.org/mcp", 80, 12),
    ]
