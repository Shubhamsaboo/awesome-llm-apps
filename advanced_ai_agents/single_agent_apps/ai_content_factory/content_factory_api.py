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

app = FastAPI(
    title="AgroDrone Europe - Content Factory API",
    description="API for generating SEO-optimized content for agrodroneeurope.com. Designed for n8n integration.",
    version="1.0.0",
)


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
    target_keywords: Optional[str] = Field(
        None, description="Comma-separated SEO keywords"
    )
    openai_api_key: Optional[str] = Field(
        None, description="OpenAI API key. Falls back to OPENAI_API_KEY env var."
    )
    serp_api_key: Optional[str] = Field(
        None, description="SerpAPI key. Falls back to SERP_API_KEY env var."
    )


class ContentResponse(BaseModel):
    content: str
    content_type: str
    service_focus: str
    language: str
    topic: str


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


@app.post("/generate", response_model=ContentResponse)
def generate_content(req: ContentRequest):
    """Generate SEO-optimized content for agrodroneeurope.com.

    Use this endpoint from n8n HTTP Request node.
    API keys can be passed in the request body or set as environment variables
    (OPENAI_API_KEY, SERP_API_KEY).
    """
    openai_key = req.openai_api_key or os.getenv("OPENAI_API_KEY")
    serp_key = req.serp_api_key or os.getenv("SERP_API_KEY")

    if not openai_key:
        raise HTTPException(status_code=400, detail="OpenAI API key is required (body or OPENAI_API_KEY env var)")
    if not serp_key:
        raise HTTPException(status_code=400, detail="SerpAPI key is required (body or SERP_API_KEY env var)")

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

    editor = _build_agents(openai_key, serp_key, req.content_type.value, req.service_focus.value, req.language.value)
    response: RunOutput = editor.run(prompt, stream=False)

    return ContentResponse(
        content=response.content,
        content_type=req.content_type.value,
        service_focus=req.service_focus.value,
        language=req.language.value,
        topic=req.topic,
    )


@app.get("/content-types")
def list_content_types():
    """List all available content types. Useful for n8n dropdowns."""
    return [e.value for e in ContentType]


@app.get("/services")
def list_services():
    """List all available service focus areas."""
    return [e.value for e in ServiceFocus]


@app.get("/health")
def health():
    return {"status": "ok"}
