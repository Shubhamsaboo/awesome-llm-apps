"""Hacker News briefing pipeline for AgentScout.

The module is intentionally self-contained: it can run with deterministic sample
data for demos, or fetch the Hacker News front page directly when live mode is
enabled.
"""

from __future__ import annotations

import datetime as dt
import html
import os
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from typing import Any
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")

AGENT_KEYWORDS = {
    "agent",
    "agents",
    "agentic",
    "automation",
    "autonomous",
    "coding",
    "framework",
    "llm",
    "mcp",
    "orchestration",
    "tool",
    "workflow",
}

NOISE_WORDS = {"ask hn: who is hiring", "freelance", "hiring"}


@dataclass(frozen=True)
class Story:
    title: str
    url: str
    hn_url: str
    points: int
    comments: int
    rank: int
    summary: str


@dataclass(frozen=True)
class Brief:
    generated_at: str
    watch_mode: str
    subject: str
    text: str
    html: str
    stories: list[Story]
    next_actions: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["stories"] = [asdict(story) for story in self.stories]
        return payload


class HNFrontPageParser(HTMLParser):
    """Small parser for the stable HN table markup."""

    def __init__(self) -> None:
        super().__init__()
        self._in_title = False
        self._current_href = ""
        self._current_text: list[str] = []
        self._latest_story: dict[str, Any] | None = None
        self._current_item_id = ""
        self._in_score = False
        self._in_subtext = False
        self._subtext_link_text = ""
        self.stories: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        class_name = attributes.get("class", "")
        if tag == "tr" and "athing" in class_name.split():
            self._current_item_id = attributes.get("id") or ""
        elif tag == "span" and class_name == "titleline":
            self._in_title = True
        elif self._in_title and tag == "a" and not self._current_href:
            self._current_href = attributes.get("href") or ""
            self._current_text = []
        elif tag == "span" and class_name == "score":
            self._in_score = True
            self._current_text = []
        elif tag == "span" and class_name == "subtext":
            self._in_subtext = True
        elif self._in_subtext and tag == "a":
            self._subtext_link_text = ""

    def handle_endtag(self, tag: str) -> None:
        if self._in_title and tag == "a" and self._current_href:
            title = " ".join("".join(self._current_text).split())
            rank = len(self.stories) + 1
            item_id = self._current_item_id or f"unknown-{rank}"
            hn_url = f"https://news.ycombinator.com/item?id={item_id}"
            self._latest_story = {
                "title": title,
                "url": _absolute_hn_url(self._current_href),
                "hn_url": hn_url,
                "points": 0,
                "comments": 0,
                "rank": rank,
            }
            self.stories.append(self._latest_story)
            self._current_item_id = ""
            self._current_href = ""
            self._current_text = []
        elif tag == "span" and self._in_title:
            self._in_title = False
        elif tag == "span" and self._in_score:
            score_text = "".join(self._current_text)
            if self._latest_story is not None:
                self._latest_story["points"] = _first_int(score_text)
            self._in_score = False
            self._current_text = []
        elif self._in_subtext and tag == "a":
            if self._latest_story is not None and "comment" in self._subtext_link_text:
                self._latest_story["comments"] = _first_int(self._subtext_link_text)
        elif tag == "span" and self._in_subtext:
            self._in_subtext = False

    def handle_data(self, data: str) -> None:
        if self._current_href or self._in_score:
            self._current_text.append(data)
        if self._in_subtext:
            self._subtext_link_text += data


def _absolute_hn_url(url: str) -> str:
    if url.startswith("item?id="):
        return f"https://news.ycombinator.com/{url}"
    if url.startswith("http"):
        return url
    return f"https://news.ycombinator.com/{url.lstrip('/')}"


def _first_int(text: str) -> int:
    match = re.search(r"\d+", text)
    return int(match.group()) if match else 0


def _keyword_hits(title: str) -> set[str]:
    normalized = re.sub(r"[^a-z0-9]+", " ", title.lower())
    return {keyword for keyword in AGENT_KEYWORDS if keyword in normalized}


def _is_noise(title: str) -> bool:
    lowered = title.lower()
    return any(noise in lowered for noise in NOISE_WORDS)


def _score_story(story: Story) -> float:
    keyword_score = len(_keyword_hits(story.title)) * 16
    discussion_score = min(story.comments, 150) / 3
    points_score = min(story.points, 500) / 10
    freshness_score = max(0, 35 - story.rank)
    return keyword_score + discussion_score + points_score + freshness_score


def _summarize_story(story: Story) -> str:
    hits = sorted(_keyword_hits(story.title))
    if hits:
        signal = ", ".join(hits[:3])
        return f"Strong Hacker News signal around {signal}; review for architecture, tooling, or workflow ideas."
    return "Useful background item for agent builders; monitor discussion before promoting it to the daily brief."


def sample_stories() -> list[Story]:
    """Deterministic demo data used when live Hacker News mode is disabled."""

    return [
        Story(
            title="Show HN: An open-source framework for reliable AI agent workflows",
            url="https://example.com/reliable-agent-workflows",
            hn_url="https://news.ycombinator.com/item?id=40100001",
            points=428,
            comments=116,
            rank=1,
            summary="Framework discussion with practical tradeoffs around orchestration, retries, state, and tool execution.",
        ),
        Story(
            title="Model Context Protocol adoption in developer tools",
            url="https://example.com/mcp-developer-tools",
            hn_url="https://news.ycombinator.com/item?id=40100002",
            points=312,
            comments=84,
            rank=4,
            summary="MCP is becoming a shared integration surface for coding assistants and internal tools.",
        ),
        Story(
            title="Lessons from running coding agents on production repositories",
            url="https://example.com/coding-agents-production",
            hn_url="https://news.ycombinator.com/item?id=40100003",
            points=256,
            comments=73,
            rank=8,
            summary="Operational report on code review loops, test gates, sandboxing, and human approval boundaries.",
        ),
        Story(
            title="Why long-running automation needs better human handoff states",
            url="https://example.com/automation-handoff-states",
            hn_url="https://news.ycombinator.com/item?id=40100004",
            points=184,
            comments=41,
            rank=12,
            summary="Product and systems perspective on when always-on agents should pause, escalate, or summarize.",
        ),
        Story(
            title="A lightweight eval harness for tool-using LLM applications",
            url="https://example.com/tool-using-evals",
            hn_url="https://news.ycombinator.com/item?id=40100005",
            points=141,
            comments=29,
            rank=17,
            summary="Practical eval design for agents that call tools and produce user-facing artifacts.",
        ),
    ]


def fetch_hn_front_page(timeout_seconds: int = 15) -> list[Story]:
    """Fetch and parse current Hacker News front-page stories."""

    request = urllib.request.Request(
        "https://news.ycombinator.com/news",
        headers={"User-Agent": "AgentScout ambient demo"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            markup = response.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not fetch Hacker News: {exc}") from exc

    parser = HNFrontPageParser()
    parser.feed(markup)
    stories: list[Story] = []
    for raw_story in parser.stories:
        story = Story(
            title=str(raw_story["title"]),
            url=str(raw_story["url"]),
            hn_url=str(raw_story["hn_url"]),
            points=int(raw_story["points"]),
            comments=int(raw_story["comments"]),
            rank=int(raw_story["rank"]),
            summary="",
        )
        stories.append(
            Story(
                title=story.title,
                url=story.url,
                hn_url=story.hn_url,
                points=story.points,
                comments=story.comments,
                rank=story.rank,
                summary=_summarize_story(story),
            )
        )
    return stories


def curate_stories(
    *,
    live: bool | None = None,
    top_n: int = 5,
) -> list[Story]:
    """Select the highest-signal agent-building stories."""

    if live is None:
        live = os.environ.get("AGENTSCOUT_LIVE_HN", "").lower() in {"1", "true", "yes"}

    stories = fetch_hn_front_page() if live else sample_stories()
    candidates = [
        story
        for story in stories
        if not _is_noise(story.title)
        and (_keyword_hits(story.title) or "agent" in story.summary.lower())
    ]
    return sorted(candidates, key=_score_story, reverse=True)[:top_n]


def render_brief(
    stories: list[Story],
    *,
    watch_mode: str = "sample",
    now: dt.datetime | None = None,
) -> Brief:
    """Render a Hacker News daily brief in text and HTML."""

    now = now or dt.datetime.now(PACIFIC)
    date_label = now.strftime("%Y-%m-%d")
    subject = f"AgentScout Hacker News brief - {date_label}"
    next_actions = [
        "Open the highest-comment thread and extract objections or implementation patterns.",
        "Promote only stories with clear engineering signal to the team digest.",
        "If this is running on a schedule, send the brief after human-readable rendering succeeds.",
    ]

    text_lines = [
        "AgentScout Hacker News Engineering Brief",
        f"Generated: {now.isoformat(timespec='seconds')}",
        f"Watch mode: {watch_mode}",
        "",
        "Highest-signal agent-building stories:",
    ]
    html_lines = [
        "<h2>AgentScout Hacker News Engineering Brief</h2>",
        f"<p><strong>Generated:</strong> {html.escape(now.isoformat(timespec='seconds'))}<br>",
        f"<strong>Watch mode:</strong> {html.escape(watch_mode)}</p>",
        "<ol>",
    ]

    for index, story in enumerate(stories, start=1):
        signal = f"{story.points} points, {story.comments} comments, front-page rank {story.rank}"
        text_lines.extend(
            [
                f"{index}. {story.title}",
                f"   Why it matters: {story.summary}",
                f"   Signal: {signal}",
                f"   Link: {story.url}",
                f"   HN: {story.hn_url}",
                "",
            ]
        )
        html_lines.extend(
            [
                "<li>",
                f"<strong>{html.escape(story.title)}</strong>",
                f"<p>{html.escape(story.summary)}</p>",
                f"<p><strong>Signal:</strong> {html.escape(signal)}<br>",
                f'<a href="{html.escape(story.url)}">source</a> | ',
                f'<a href="{html.escape(story.hn_url)}">HN discussion</a></p>',
                "</li>",
            ]
        )

    if not stories:
        text_lines.append("No high-signal agent-building stories found.")
        html_lines.append("<li>No high-signal agent-building stories found.</li>")

    text_lines.extend(["Next actions:", *[f"- {action}" for action in next_actions]])
    html_lines.extend(
        [
            "</ol>",
            "<h3>Next actions</h3>",
            "<ul>",
            *[f"<li>{html.escape(action)}</li>" for action in next_actions],
            "</ul>",
        ]
    )
    return Brief(
        generated_at=now.isoformat(timespec="seconds"),
        watch_mode=watch_mode,
        subject=subject,
        text="\n".join(text_lines),
        html="\n".join(html_lines),
        stories=stories,
        next_actions=next_actions,
    )


def run_ambient_scout(*, live: bool | None = None, top_n: int = 5) -> dict[str, Any]:
    """Run the complete Hacker News briefing pipeline."""

    stories = curate_stories(live=live, top_n=top_n)
    inferred_live = live
    if inferred_live is None:
        inferred_live = os.environ.get("AGENTSCOUT_LIVE_HN", "").lower() in {
            "1",
            "true",
            "yes",
        }
    brief = render_brief(stories, watch_mode="live_hn" if inferred_live else "sample")
    payload = brief.to_dict()
    payload["delivery_note"] = (
        "This demo renders the Hacker News digest and handoff text. Wire the "
        "returned text/html to your email, Slack, or ticketing sender when you deploy it."
    )
    return payload
