import os
from textwrap import dedent
from typing import Optional
from enum import Enum

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.tools.serpapi import SerpApiTools
from agno.tools.newspaper4k import Newspaper4kTools
from agno.models.openai import OpenAIChat

from news_fetcher import fetch_news, suggest_topics, fetch_and_suggest, NewsItem
from rss_feeds import RSS_FEEDS, AGRODRONE_CATEGORIES
from review_queue import (
    ReviewDecision, ReviewStatus,
    add_news_to_queue, get_news_queue, review_news,
    add_content_to_queue, get_content_queue, review_content, mark_content_published,
    add_social_media_to_queue, get_social_media_queue, review_social_media, mark_social_media_published,
)
from media_generator import (
    generate_content_image, generate_voiceover,
    generate_social_media_pack, assemble_vertical_video,
)

app = FastAPI(
    title="AgroDrone Europe - Content Factory API",
    description=(
        "Content factory for agrodroneeurope.com with human-in-the-loop review. "
        "RSS news → AI topics → human approval → content generation → image/video → social media."
    ),
    version="2.0.0",
)


# ── Enums & Models ──────────────────────────────────────────────────────


class ContentType(str, Enum):
    blog_post = "Blog Post (SEO-optimized)"
    landing_page = "Landing Page Copy"
    service_description = "Service Description"
    social_media = "Social Media Post Pack"
    case_study = "Case Study"
    faq = "FAQ Section"


class ServiceFocus(str, Enum):
    pflanzenschutz = "Pflanzenschutz (Crop Protection)"
    aussaat = "Aussaat (Seeding/Sowing)"
    ndvi = "NDVI Monitoring"
    dachreinigung = "Dachreinigung (Roof Cleaning)"
    general = "General / Company Overview"


class Language(str, Enum):
    german = "German"
    english = "English"


class ContentRequest(BaseModel):
    topic: str = Field(..., description="The content topic to write about")
    content_type: ContentType = ContentType.blog_post
    service_focus: ServiceFocus = ServiceFocus.general
    language: Language = Language.german
    target_keywords: Optional[str] = Field(None, description="Comma-separated SEO keywords")
    news_id: Optional[int] = Field(None, description="ID of approved news item (links content to news)")
    generate_image: bool = Field(True, description="Auto-generate a DALL-E banner image")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key. Falls back to env var.")
    serp_api_key: Optional[str] = Field(None, description="SerpAPI key. Falls back to env var.")


class ContentResponse(BaseModel):
    content_id: int
    content: str
    content_type: str
    service_focus: str
    language: str
    topic: str
    image_url: str = ""
    image_prompt: str = ""
    status: str = "pending"


class NewsRequest(BaseModel):
    category: Optional[str] = Field(
        None,
        description="Filter: crop_protection, seeding, ndvi_monitoring, drone_regulation, drones_general, policy.",
    )
    max_age_days: int = Field(7, description="Only return articles from the last N days")
    max_items_per_feed: int = Field(10, description="Max articles per RSS feed")
    auto_queue: bool = Field(True, description="Automatically add fetched news to the review queue")


class TopicRequest(BaseModel):
    category: Optional[str] = Field(None, description="RSS category filter")
    max_age_days: int = Field(7, description="News recency window in days")
    num_suggestions: int = Field(5, description="Number of topic suggestions")
    language: Language = Language.german
    openai_api_key: Optional[str] = Field(None, description="Falls back to env var.")


class ImageRequest(BaseModel):
    topic: str
    content_type: ContentType = ContentType.blog_post
    service_focus: ServiceFocus = ServiceFocus.general
    size: str = Field("1792x1024", description="1792x1024 for website, 1024x1792 for vertical/social")
    openai_api_key: Optional[str] = None


class VoiceoverRequest(BaseModel):
    text: str = Field(..., description="Text to convert to speech")
    voice: str = Field("nova", description="Voice: alloy, echo, fable, onyx, nova, shimmer")
    model: str = Field("tts-1", description="tts-1 (fast) or tts-1-hd (high quality)")
    openai_api_key: Optional[str] = None


class SocialMediaRequest(BaseModel):
    content_id: int = Field(..., description="ID of approved content to create social posts for")
    generate_image: bool = Field(True, description="Generate vertical image for social media")
    generate_voiceover: bool = Field(True, description="Generate TTS voiceover for video")
    generate_video: bool = Field(False, description="Assemble vertical video (requires ffmpeg)")
    voice: str = Field("nova", description="TTS voice choice")
    language: Language = Language.german
    openai_api_key: Optional[str] = None


def _get_keys(req) -> tuple[str, str]:
    openai_key = getattr(req, "openai_api_key", None) or os.getenv("OPENAI_API_KEY")
    serp_key = getattr(req, "serp_api_key", None) or os.getenv("SERP_API_KEY")
    return openai_key, serp_key


def _require_openai(req) -> str:
    key = getattr(req, "openai_api_key", None) or os.getenv("OPENAI_API_KEY")
    if not key:
        raise HTTPException(status_code=400, detail="OpenAI API key is required")
    return key


# ── Content Generation Agents ───────────────────────────────────────────


def _build_agents(openai_key: str, serp_key: str, content_type: str, service_focus: str, language: str):
    researcher = Agent(
        name="Researcher",
        role="Researches agricultural drone industry trends and competitors",
        model=OpenAIChat(id="gpt-4o", api_key=openai_key),
        description=dedent("""\
            You are a senior market researcher specializing in agricultural technology,
            precision farming, and drone services in Europe (especially Germany).
            Given a topic, generate targeted search queries, find the most relevant
            sources, and compile key facts, statistics, and insights."""),
        instructions=[
            "Generate 3-5 search queries related to the given topic, focusing on the German/European agricultural drone market.",
            "Search for each query and analyze the results.",
            "Return the 10 most relevant URLs with a brief summary of key findings from each.",
            "Focus on: industry statistics, regulations, benefits, case studies, and trends.",
            "Include German-language sources when available.",
        ],
        tools=[SerpApiTools(api_key=serp_key)],
        add_datetime_to_context=True,
    )

    seo_writer = Agent(
        name="SEO Content Writer",
        role="Writes SEO-optimized content for agricultural drone services",
        model=OpenAIChat(id="gpt-4o", api_key=openai_key),
        description=dedent("""\
            You are a professional SEO content writer specializing in B2B agricultural
            technology content. You write for AgroDrone Europe (agrodroneeurope.com),
            a German company offering professional drone services for agriculture
            (crop protection, seeding, NDVI monitoring) and building maintenance
            (roof cleaning)."""),
        instructions=[
            "Write content based on the research provided and the specified content type.",
            "Naturally incorporate the target SEO keywords without keyword stuffing.",
            "Use proper heading hierarchy (H1, H2, H3) for SEO.",
            "Include a compelling meta title (max 60 chars) and meta description (max 155 chars).",
            "Write in the specified language with a professional but approachable tone.",
            "For blog posts: include introduction, 3-5 main sections, conclusion, and a call-to-action.",
            "For landing pages: focus on benefits, social proof, and clear CTAs.",
            "For social media packs: create 5 posts for different platforms (LinkedIn, Instagram, Facebook).",
            "For case studies: use the Problem-Solution-Result framework.",
            "For FAQ sections: create 8-10 relevant Q&A pairs with schema-friendly formatting.",
            "Always reference agrodroneeurope.com services where appropriate.",
            "Include internal linking suggestions to relevant service pages.",
        ],
        tools=[Newspaper4kTools()],
        add_datetime_to_context=True,
        markdown=True,
    )

    editor = Agent(
        name="Content Editor",
        model=OpenAIChat(id="gpt-4o", api_key=openai_key),
        team=[researcher, seo_writer],
        description=dedent("""\
            You are the head of content at AgroDrone Europe. You coordinate research
            and writing to produce high-quality, SEO-optimized content that drives
            organic traffic and converts visitors into leads for drone services."""),
        instructions=[
            "First, ask the Researcher to gather relevant data and sources on the topic.",
            "Then, pass the research findings, content type, target keywords, and language to the SEO Content Writer.",
            f"The content must be written in {language}.",
            f"Content type requested: {content_type}.",
            f"Service focus: {service_focus}.",
            "Review the draft for: SEO optimization, factual accuracy, brand voice consistency, and conversion potential.",
            "Ensure the content includes meta title, meta description, and heading structure.",
            "Add a section at the end with: suggested internal links, target keywords used, and content score notes.",
            "The final content must be publication-ready for agrodroneeurope.com.",
        ],
        add_datetime_to_context=True,
        markdown=True,
    )

    return editor


# ═══════════════════════════════════════════════════════════════════════
# STEP 1: RSS News Fetching
# ═══════════════════════════════════════════════════════════════════════


@app.post("/news/fetch", tags=["1. News"])
def fetch_rss_news(req: NewsRequest):
    """Fetch news from RSS feeds and optionally add to the review queue.

    n8n: Use this as the first step. News goes to the queue for human review.
    """
    items = fetch_news(
        category=req.category,
        max_age_days=req.max_age_days,
        max_items_per_feed=req.max_items_per_feed,
    )

    queued_ids = []
    if req.auto_queue and items:
        queued_ids = add_news_to_queue([item.model_dump() for item in items])

    return {
        "count": len(items),
        "queued": len(queued_ids),
        "queued_ids": queued_ids,
        "articles": [item.model_dump() for item in items],
    }


@app.post("/suggest-topics", tags=["1. News"])
def get_topic_suggestions(req: TopicRequest):
    """AI-powered topic suggestions based on current news."""
    openai_key = _require_openai(req)

    news, plan = fetch_and_suggest(
        openai_api_key=openai_key,
        category=req.category,
        max_age_days=req.max_age_days,
        num_suggestions=req.num_suggestions,
        language=req.language.value,
    )

    return {
        "news_count": len(news),
        "suggestions": plan.suggestions if hasattr(plan, "suggestions") else plan,
    }


# ═══════════════════════════════════════════════════════════════════════
# STEP 2: Human Review — News Queue
# ═══════════════════════════════════════════════════════════════════════


@app.get("/queue/news", tags=["2. Review Queue"])
def list_news_queue(status: Optional[str] = None, limit: int = 50):
    """Get news items awaiting review.

    n8n: Poll this endpoint to show pending news in a review form/webhook.
    """
    return get_news_queue(status=status, limit=limit)


@app.post("/queue/news/{news_id}/review", tags=["2. Review Queue"])
def review_news_item(news_id: int, decision: ReviewDecision):
    """Approve or reject a news item.

    n8n: Call this after human reviews the news item.
    Only approved news items proceed to content generation.
    """
    result = review_news(news_id, decision)
    if not result:
        raise HTTPException(status_code=404, detail="News item not found")
    return result


# ═══════════════════════════════════════════════════════════════════════
# STEP 3: Content Generation (only for approved news)
# ═══════════════════════════════════════════════════════════════════════


@app.post("/generate", response_model=ContentResponse, tags=["3. Generate Content"])
def generate_content(req: ContentRequest):
    """Generate content and add to review queue.

    Generates SEO article + optional DALL-E image.
    The result goes to the content review queue (pending) for human approval.
    """
    openai_key, serp_key = _get_keys(req)
    if not openai_key:
        raise HTTPException(status_code=400, detail="OpenAI API key is required")
    if not serp_key:
        raise HTTPException(status_code=400, detail="SerpAPI key is required")

    keywords_text = req.target_keywords or "determine the best keywords based on the topic"

    prompt = dedent(f"""\
        Create {req.content_type.value} content for agrodroneeurope.com.

        Topic: {req.topic}
        Service Focus: {req.service_focus.value}
        Target Keywords: {keywords_text}
        Language: {req.language.value}

        The company AgroDrone Europe offers professional drone services in Germany:
        - Pflanzenschutz (Crop Protection) - precision spraying with agricultural drones
        - Aussaat (Seeding/Sowing) - drone-based seeding for hard-to-reach areas
        - NDVI Monitoring - crop health analysis using multispectral drone imaging
        - Dachreinigung (Roof Cleaning) - professional drone-assisted roof cleaning

        Website: agrodroneeurope.com""")

    editor = _build_agents(
        openai_key, serp_key, req.content_type.value, req.service_focus.value, req.language.value
    )
    response: RunOutput = editor.run(prompt, stream=False)

    # Generate image if requested
    image_url = ""
    image_prompt = ""
    if req.generate_image:
        try:
            img_result = generate_content_image(
                topic=req.topic,
                content_type=req.content_type.value,
                service_focus=req.service_focus.value,
                openai_api_key=openai_key,
            )
            image_url = img_result.get("url", "")
            image_prompt = img_result.get("original_prompt", "")
        except Exception:
            pass  # Image generation is optional, don't fail the whole request

    # Add to content review queue
    content_id = add_content_to_queue({
        "news_id": req.news_id,
        "topic": req.topic,
        "content_type": req.content_type.value,
        "service_focus": req.service_focus.value,
        "language": req.language.value,
        "target_keywords": req.target_keywords or "",
        "content_markdown": response.content,
        "image_url": image_url,
        "image_prompt": image_prompt,
    })

    return ContentResponse(
        content_id=content_id,
        content=response.content,
        content_type=req.content_type.value,
        service_focus=req.service_focus.value,
        language=req.language.value,
        topic=req.topic,
        image_url=image_url,
        image_prompt=image_prompt,
        status="pending",
    )


# ═══════════════════════════════════════════════════════════════════════
# STEP 4: Human Review — Content Queue
# ═══════════════════════════════════════════════════════════════════════


@app.get("/queue/content", tags=["4. Review Content"])
def list_content_queue(status: Optional[str] = None, limit: int = 50):
    """Get generated content awaiting review."""
    return get_content_queue(status=status, limit=limit)


@app.post("/queue/content/{content_id}/review", tags=["4. Review Content"])
def review_content_item(content_id: int, decision: ReviewDecision):
    """Approve or reject generated content.

    Only approved content can be published or sent to social media pipeline.
    """
    result = review_content(content_id, decision)
    if not result:
        raise HTTPException(status_code=404, detail="Content item not found")
    return result


@app.post("/queue/content/{content_id}/publish", tags=["4. Review Content"])
def publish_content(content_id: int):
    """Mark content as published (after it's been deployed to the website)."""
    result = mark_content_published(content_id)
    if not result:
        raise HTTPException(status_code=404, detail="Content item not found")
    return result


# ═══════════════════════════════════════════════════════════════════════
# STEP 5: Image Generation
# ═══════════════════════════════════════════════════════════════════════


@app.post("/media/image", tags=["5. Media"])
def create_image(req: ImageRequest):
    """Generate an image using DALL-E 3.

    Use size '1792x1024' for website banners, '1024x1792' for vertical social media.
    """
    openai_key = _require_openai(req)

    result = generate_content_image(
        topic=req.topic,
        content_type=req.content_type.value,
        service_focus=req.service_focus.value,
        openai_api_key=openai_key,
        size=req.size,
    )
    return result


# ═══════════════════════════════════════════════════════════════════════
# STEP 6: Social Media Pipeline
# ═══════════════════════════════════════════════════════════════════════


@app.post("/social/generate", tags=["6. Social Media"])
def create_social_media(req: SocialMediaRequest):
    """Generate social media pack from approved content.

    Creates posts for LinkedIn, Instagram, Facebook, TikTok/Reels.
    Optionally generates vertical image, voiceover, and video.
    Results go to the social media review queue.
    """
    openai_key = _require_openai(req)

    # Get the approved content
    content_items = get_content_queue(status="approved")
    content = next((c for c in content_items if c["id"] == req.content_id), None)
    if not content:
        # Also check published content
        content_items = get_content_queue(status="published")
        content = next((c for c in content_items if c["id"] == req.content_id), None)
    if not content:
        raise HTTPException(
            status_code=404,
            detail="Content not found or not approved. Approve the content first via /queue/content/{id}/review",
        )

    # Generate social media text content
    sm_result = generate_social_media_pack(
        topic=content["topic"],
        content_markdown=content["content_markdown"],
        service_focus=content["service_focus"],
        openai_api_key=openai_key,
        language=req.language.value,
    )

    # Generate vertical image for social media
    social_image_url = ""
    if req.generate_image:
        try:
            img_result = generate_content_image(
                topic=content["topic"],
                content_type="Social Media Post",
                service_focus=content["service_focus"],
                openai_api_key=openai_key,
                size="1024x1792",
            )
            social_image_url = img_result.get("url", "")
        except Exception:
            pass

    # Generate voiceover
    voiceover_result = {}
    if req.generate_voiceover and sm_result.get("voiceover_text"):
        try:
            voiceover_result = generate_voiceover(
                text=sm_result["voiceover_text"],
                openai_api_key=openai_key,
                voice=req.voice,
            )
        except Exception:
            pass

    # Assemble video (if both image and voiceover exist)
    video_result = {}
    if req.generate_video and voiceover_result.get("local_path") and social_image_url:
        try:
            # For video assembly we need a local image file — download it
            import urllib.request
            from media_generator import MEDIA_DIR
            import uuid
            img_local = str(MEDIA_DIR / f"social_{uuid.uuid4().hex[:8]}.png")
            urllib.request.urlretrieve(social_image_url, img_local)
            video_result = assemble_vertical_video(
                image_path=img_local,
                audio_path=voiceover_result["local_path"],
            )
        except Exception:
            pass

    # Add to social media review queue
    sm_queue_items = []
    for platform in sm_result.get("platforms", []):
        sm_queue_items.append({
            "content_id": req.content_id,
            "platform": platform,
            "post_text": sm_result.get("social_media_content", ""),
            "image_url": social_image_url,
            "video_url": video_result.get("local_path", ""),
            "voiceover_url": voiceover_result.get("local_path", ""),
            "voiceover_text": sm_result.get("voiceover_text", ""),
        })
    sm_ids = add_social_media_to_queue(sm_queue_items)

    return {
        "content_id": req.content_id,
        "social_media_content": sm_result.get("social_media_content", ""),
        "voiceover_text": sm_result.get("voiceover_text", ""),
        "social_image_url": social_image_url,
        "voiceover_file": voiceover_result.get("local_path", ""),
        "video_file": video_result.get("local_path", ""),
        "queue_ids": sm_ids,
        "platforms": sm_result.get("platforms", []),
    }


@app.post("/media/voiceover", tags=["6. Social Media"])
def create_voiceover(req: VoiceoverRequest):
    """Generate voiceover audio using OpenAI TTS."""
    openai_key = _require_openai(req)
    result = generate_voiceover(
        text=req.text,
        openai_api_key=openai_key,
        voice=req.voice,
        model=req.model,
    )
    return result


# ═══════════════════════════════════════════════════════════════════════
# STEP 7: Human Review — Social Media Queue
# ═══════════════════════════════════════════════════════════════════════


@app.get("/queue/social", tags=["7. Review Social Media"])
def list_social_media_queue(
    status: Optional[str] = None,
    content_id: Optional[int] = None,
    limit: int = 50,
):
    """Get social media posts awaiting review."""
    return get_social_media_queue(status=status, content_id=content_id, limit=limit)


@app.post("/queue/social/{sm_id}/review", tags=["7. Review Social Media"])
def review_social_media_item(sm_id: int, decision: ReviewDecision):
    """Approve or reject a social media post."""
    result = review_social_media(sm_id, decision)
    if not result:
        raise HTTPException(status_code=404, detail="Social media item not found")
    return result


@app.post("/queue/social/{sm_id}/publish", tags=["7. Review Social Media"])
def publish_social_media(sm_id: int):
    """Mark social media post as published."""
    result = mark_social_media_published(sm_id)
    if not result:
        raise HTTPException(status_code=404, detail="Social media item not found")
    return result


# ═══════════════════════════════════════════════════════════════════════
# Reference Endpoints
# ═══════════════════════════════════════════════════════════════════════


@app.get("/content-types", tags=["Reference"])
def list_content_types():
    return [e.value for e in ContentType]


@app.get("/services", tags=["Reference"])
def list_services():
    return [e.value for e in ServiceFocus]


@app.get("/feeds", tags=["Reference"])
def list_feeds():
    return RSS_FEEDS


@app.get("/feed-categories", tags=["Reference"])
def list_feed_categories():
    return AGRODRONE_CATEGORIES


@app.get("/health", tags=["Reference"])
def health():
    return {"status": "ok", "version": "2.0.0"}
