"""Fetches news from RSS feeds and uses an AI agent to suggest content topics."""

from datetime import datetime, timedelta
from textwrap import dedent
from typing import Optional

import feedparser
from pydantic import BaseModel, Field

from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.models.openai import OpenAIChat

from rss_feeds import RSS_FEEDS, AGRODRONE_CATEGORIES, get_feeds_by_category


class NewsItem(BaseModel):
    title: str
    link: str
    summary: str = ""
    published: str = ""
    source: str = ""
    category: str = ""
    language: str = ""


class TopicSuggestion(BaseModel):
    topic: str = Field(description="Suggested content topic")
    content_type: str = Field(description="Recommended content type")
    service_focus: str = Field(description="Which AgroDrone service this relates to")
    target_keywords: str = Field(description="Suggested SEO keywords")
    reasoning: str = Field(description="Why this topic is relevant now")
    source_articles: list[str] = Field(description="Source article titles that inspired this topic")


class TopicPlan(BaseModel):
    suggestions: list[TopicSuggestion]


def fetch_news(
    category: Optional[str] = None,
    max_age_days: int = 7,
    max_items_per_feed: int = 10,
) -> list[NewsItem]:
    """Fetch recent news from RSS feeds.

    Args:
        category: Filter by AGRODRONE_CATEGORIES key (e.g. 'crop_protection', 'drone_regulation').
                  None = all feeds.
        max_age_days: Only return articles published within this many days.
        max_items_per_feed: Max articles per feed to avoid flooding.

    Returns:
        List of NewsItem sorted by publish date (newest first).
    """
    feeds = get_feeds_by_category(category)
    cutoff = datetime.now() - timedelta(days=max_age_days)
    all_items: list[NewsItem] = []

    for feed_cfg in feeds:
        try:
            parsed = feedparser.parse(feed_cfg["rss_url"])
        except Exception:
            continue

        for entry in parsed.entries[:max_items_per_feed]:
            published_str = entry.get("published", entry.get("updated", ""))
            published_dt = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_dt = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published_dt = datetime(*entry.updated_parsed[:6])

            if published_dt and published_dt < cutoff:
                continue

            item = NewsItem(
                title=entry.get("title", ""),
                link=entry.get("link", ""),
                summary=entry.get("summary", entry.get("description", ""))[:500],
                published=published_str,
                source=feed_cfg["name"],
                category=feed_cfg["category"],
                language=feed_cfg["language"],
            )
            all_items.append(item)

    all_items.sort(key=lambda x: x.published, reverse=True)
    return all_items


def suggest_topics(
    news_items: list[NewsItem],
    openai_api_key: str,
    num_suggestions: int = 5,
    language: str = "German",
) -> TopicPlan:
    """Use an AI agent to analyze news and suggest content topics for AgroDrone Europe.

    Args:
        news_items: List of recent news articles.
        openai_api_key: OpenAI API key.
        num_suggestions: How many topic suggestions to generate.
        language: Target language for content.

    Returns:
        TopicPlan with suggested topics.
    """
    news_digest = "\n".join(
        f"- [{item.source} / {item.category}] {item.title}: {item.summary[:200]}"
        for item in news_items[:50]
    )

    topic_planner = Agent(
        name="Topic Planner",
        role="Analyzes agricultural and drone industry news to suggest content topics",
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        description=dedent("""\
            You are the content strategist at AgroDrone Europe (agrodroneeurope.com).
            You analyze industry news and trends to plan content that drives organic
            traffic and establishes AgroDrone Europe as a thought leader in agricultural
            drone services in Germany."""),
        instructions=[
            f"Analyze the provided news digest and suggest exactly {num_suggestions} content topics.",
            "Each topic must be directly relevant to AgroDrone Europe's services:",
            "  - Pflanzenschutz (Crop Protection) - precision spraying",
            "  - Aussaat (Seeding/Sowing) - drone-based seeding",
            "  - NDVI Monitoring - crop health analysis",
            "  - Dachreinigung (Roof Cleaning) - drone-assisted roof cleaning",
            "  - General company positioning and drone regulations",
            "Prioritize topics that are: timely (based on current news), have SEO potential, "
            "and position AgroDrone Europe as an expert.",
            "For each suggestion provide: topic title, best content type, service focus, "
            "target SEO keywords, reasoning, and which source articles inspired it.",
            f"All topic titles and keywords should be in {language}.",
            "Content types to choose from: Blog Post (SEO-optimized), Landing Page Copy, "
            "Service Description, Social Media Post Pack, Case Study, FAQ Section.",
            "Service focus options: Pflanzenschutz (Crop Protection), Aussaat (Seeding/Sowing), "
            "NDVI Monitoring, Dachreinigung (Roof Cleaning), General / Company Overview.",
        ],
        response_model=TopicPlan,
        add_datetime_to_context=True,
    )

    prompt = dedent(f"""\
        Analyze the following news digest from agricultural and drone industry sources
        and suggest {num_suggestions} content topics for agrodroneeurope.com:

        --- NEWS DIGEST ---
        {news_digest}
        --- END DIGEST ---

        Suggest {num_suggestions} topics that AgroDrone Europe should write about now,
        based on these current news trends.""")

    response: RunOutput = topic_planner.run(prompt, stream=False)
    return response.content


def fetch_and_suggest(
    openai_api_key: str,
    category: Optional[str] = None,
    max_age_days: int = 7,
    num_suggestions: int = 5,
    language: str = "German",
) -> tuple[list[NewsItem], TopicPlan]:
    """Convenience function: fetch news and suggest topics in one call.

    Returns:
        Tuple of (news_items, topic_plan).
    """
    news = fetch_news(category=category, max_age_days=max_age_days)
    if not news:
        return news, TopicPlan(suggestions=[])
    plan = suggest_topics(news, openai_api_key, num_suggestions, language)
    return news, plan
