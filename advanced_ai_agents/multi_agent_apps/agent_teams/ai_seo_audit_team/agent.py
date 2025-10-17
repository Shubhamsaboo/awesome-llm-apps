"""
On-Page SEO Audit & Optimization Team built with Google ADK.

The workflow runs three specialized agents in sequence:
1. Page Auditor → scrapes the target URL with Firecrawl and extracts the structural audit + keyword focus.
2. SERP Analyst → performs competitive analysis with Google Search using the discovered primary keyword.
3. Optimization Advisor → synthesizes the audit and SERP insights into a prioritized optimization report.
"""

from __future__ import annotations
import os
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import FunctionTool, google_search
from google.adk.tools.agent_tool import AgentTool
from firecrawl import FirecrawlApp


# =============================================================================
# Output Schemas
# =============================================================================


class HeadingItem(BaseModel):
    tag: str = Field(..., description="Heading tag such as h1, h2, h3.")
    text: str = Field(..., description="Text content of the heading.")


class LinkCounts(BaseModel):
    internal: Optional[int] = Field(None, description="Number of internal links on the page.")
    external: Optional[int] = Field(None, description="Number of external links on the page.")
    broken: Optional[int] = Field(None, description="Number of broken links detected.")
    notes: Optional[str] = Field(
        None, description="Additional qualitative observations about linking."
    )


class AuditResults(BaseModel):
    title_tag: str = Field(..., description="Full title tag text.")
    meta_description: str = Field(..., description="Meta description text.")
    primary_heading: str = Field(..., description="Primary H1 heading on the page.")
    secondary_headings: List[HeadingItem] = Field(
        default_factory=list, description="Secondary headings (H2-H4) in reading order."
    )
    word_count: Optional[int] = Field(
        None, description="Approximate number of words in the main content."
    )
    content_summary: str = Field(
        ..., description="Summary of the main topics and structure of the content."
    )
    link_counts: LinkCounts = Field(
        ...,
        description="Quantitative snapshot of internal/external/broken links.",
    )
    technical_findings: List[str] = Field(
        default_factory=list,
        description="List of notable technical SEO issues (e.g., missing alt text, slow LCP).",
    )
    content_opportunities: List[str] = Field(
        default_factory=list,
        description="Observed content gaps or opportunities for improvement.",
    )


class TargetKeywords(BaseModel):
    primary_keyword: str = Field(..., description="Most likely primary keyword target.")
    secondary_keywords: List[str] = Field(
        default_factory=list, description="Related secondary or supporting keywords."
    )
    search_intent: str = Field(
        ...,
        description="Dominant search intent inferred from the page (informational, transactional, etc.).",
    )
    supporting_topics: List[str] = Field(
        default_factory=list,
        description="Cluster of supporting topics or entities that reinforce the keyword strategy.",
    )


class PageAuditOutput(BaseModel):
    audit_results: AuditResults = Field(..., description="Structured on-page audit findings.")
    target_keywords: TargetKeywords = Field(
        ..., description="Keyword focus derived from page content."
    )


class SerpResult(BaseModel):
    rank: int = Field(..., description="Organic ranking position.")
    title: str = Field(..., description="Title of the search result.")
    url: str = Field(..., description="Landing page URL.")
    snippet: str = Field(..., description="SERP snippet or summary.")
    content_type: str = Field(
        ..., description="Content format (blog post, landing page, tool, video, etc.)."
    )


class SerpAnalysis(BaseModel):
    primary_keyword: str = Field(..., description="Keyword used for SERP research.")
    top_10_results: List[SerpResult] = Field(
        ..., description="Top organic competitors for the keyword."
    )
    title_patterns: List[str] = Field(
        default_factory=list,
        description="Common patterns or phrases used in competitor titles.",
    )
    content_formats: List[str] = Field(
        default_factory=list,
        description="Typical content formats found (guides, listicles, comparison pages, etc.).",
    )
    people_also_ask: List[str] = Field(
        default_factory=list,
        description="Representative questions surfaced in People Also Ask.",
    )
    key_themes: List[str] = Field(
        default_factory=list,
        description="Notable recurring themes, features, or angles competitors emphasize.",
    )
    differentiation_opportunities: List[str] = Field(
        default_factory=list,
        description="Opportunities to stand out versus competitors.",
    )


class OptimizationRecommendation(BaseModel):
    priority: str = Field(..., description="Priority level (P0, P1, P2).")
    area: str = Field(..., description="Optimization focus area (content, technical, UX, etc.).")
    recommendation: str = Field(..., description="Recommended action.")
    rationale: str = Field(..., description="Why this change matters, referencing audit/SERP data.")
    expected_impact: str = Field(..., description="Anticipated impact on SEO or user metrics.")
    effort: str = Field(..., description="Relative effort required (low/medium/high).")


# =============================================================================
# Tools
# =============================================================================


def firecrawl_scrape(url: str) -> Dict[str, object]:
    """
    Scrape a target URL with Firecrawl and return structured data for auditing.

    Args:
        url: Fully-qualified URL to crawl.

    Returns:
        Dictionary payload from Firecrawl that includes markdown, html, and link metadata.
    """
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise RuntimeError(
            "FIRECRAWL_API_KEY environment variable is not set. "
            "Provide a valid Firecrawl API key to enable crawling."
        )

    app = FirecrawlApp(api_key=api_key)
    try:
        document = app.scrape(
            url=url,
            formats=[
                "markdown",
                "html",
                "links",
            ],
            only_main_content=True,
            timeout=90000,
            block_ads=True,
        )
    except Exception as exc:  # pragma: no cover - tool errors pass to the agent
        raise RuntimeError(f"Firecrawl scrape failed: {exc}") from exc

    payload = document.model_dump(exclude_none=True)
    if not payload.get("markdown") and not payload.get("html"):
        raise RuntimeError("Firecrawl scrape completed but returned no page content.")
    return payload


firecrawl_tool = FunctionTool(firecrawl_scrape)


# =============================================================================
# Helper Agents
# =============================================================================


search_executor_agent = LlmAgent(
    name="perform_google_search",
    model="gemini-2.5-flash",
    description="Executes Google searches for provided queries and returns structured results.",
    instruction="""The latest user message contains the keyword to search.
- Call google_search with that exact query and fetch the top organic results (aim for 10).
- Respond with JSON text containing the query and an array of result objects (title, url, snippet). Use an empty array when nothing is returned.
- No additional commentary—return JSON text only.""",
    tools=[google_search],
)

google_search_tool = AgentTool(search_executor_agent)


# =============================================================================
# Agent Definitions
# =============================================================================


page_auditor_agent = LlmAgent(
    name="PageAuditorAgent",
    model="gemini-2.5-flash",
    description=(
        "Scrapes the target URL, performs a structural on-page SEO audit, and extracts keyword signals."
    ),
    instruction="""You are Agent 1 in a sequential SEO workflow.
- Extract the URL from the latest user message. If no valid URL is provided, ask the user for one and stop.
- Call the `firecrawl_scrape` tool exactly once to gather page content, metadata, and links.
- Audit the page structure: title tag, meta description, headings hierarchy, word count, link health, and technical flags.
- Infer the dominant search intent and identify the primary and secondary keyword targets based on page content.
- Populate every field in the PageAuditOutput schema and store the result in `state['page_audit']`.
- Output must be valid JSON only, with no extra commentary. Every string field needs meaningful text (use clear fallbacks like "Not available" if necessary). Keep numeric fields as integers and lists as arrays (use [] when empty).""",
    tools=[firecrawl_tool],
    output_schema=PageAuditOutput,
    output_key="page_audit",
)


serp_analyst_agent = LlmAgent(
    name="SerpAnalystAgent",
    model="gemini-2.5-flash",
    description=(
        "Researches the live SERP for the discovered primary keyword and summarizes the competitive landscape."
    ),
    instruction="""You are Agent 2 in the workflow.
- Read the keyword data from `state['page_audit']['target_keywords']`.
- For the primary keyword, call the `perform_google_search` tool with arguments `{"request": "<primary keyword>"}` to fetch the top organic results (request 10 results).
- Summarize each result with rank, title, URL, snippet, and content type.
- Highlight common title patterns, dominant content formats, People Also Ask questions, recurring themes, and opportunities to differentiate the page.
- Populate the SerpAnalysis schema, store it in `state['serp_analysis']`, and return strict JSON only. Ensure `primary_keyword` is a non-empty string (use a clear fallback if the search fails) and keep every list field as an array (return [] when empty).""",
    tools=[google_search_tool],
    output_schema=SerpAnalysis,
    output_key="serp_analysis",
)


optimization_advisor_agent = LlmAgent(
    name="OptimizationAdvisorAgent",
    model="gemini-2.5-flash",
    description="Synthesizes the audit and SERP findings into a prioritized optimization roadmap.",
    instruction="""You are Agent 3 and the final expert in the workflow.
- Review `state['page_audit']` and `state['serp_analysis']` to understand the current page and competitive landscape.
- Produce a polished Markdown report for the user that includes:
  * Executive summary
  * Key audit findings (technical + content + keyword highlights)
  * Prioritized action list grouped by priority level (P0/P1/P2) with rationale and expected impact
  * Keyword strategy and SERP insights
  * Measurement / next-step suggestions
- Reference concrete data points from the earlier agents. If some data is missing, acknowledge it directly rather than fabricating.
- Return Markdown only—no JSON.""",
)


seo_audit_team = SequentialAgent(
    name="SeoAuditTeam",
    description=(
        "Runs a three-agent sequential pipeline that audits a page, researches SERP competitors, "
        "and produces an optimization plan."
    ),
    sub_agents=[
        page_auditor_agent,
        serp_analyst_agent,
        optimization_advisor_agent,
    ],
)


# Expose the root agent for the ADK runtime and Dev UI.
root_agent = seo_audit_team
