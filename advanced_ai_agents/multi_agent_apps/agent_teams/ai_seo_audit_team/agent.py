"""
On-Page SEO Audit & Optimization Team built with Google ADK.

The workflow runs three specialized agents in sequence:
1. Page Auditor → scrapes the target URL with Firecrawl and extracts the structural audit + keyword focus.
2. SERP Analyst → performs competitive analysis with Google Search using the discovered primary keyword.
3. Optimization Advisor → synthesizes the audit and SERP insights into a prioritized optimization report.
"""

from __future__ import annotations
import os
from typing import List, Optional
from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters


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

# Firecrawl MCP Toolset - connects to Firecrawl's MCP server for web scraping
firecrawl_toolset = MCPToolset(
    connection_params=StdioServerParameters(
        command='npx',
        args=[
            "-y",  # Auto-confirm npm package installation
            "firecrawl-mcp",  # The Firecrawl MCP server package
        ],
        env={
            "FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY", "")
        }
    ),
    # Filter to use only the scrape tool for this agent
    tool_filter=['firecrawl_scrape']
)


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
    instruction="""You are Agent 1 in a sequential SEO workflow. Your role is to gather data silently for the next agents.

STEP 1: Extract the URL
- Look for a URL in the user's message (it will start with http:// or https://)
- Example: If user says "Audit https://theunwindai.com", extract "https://theunwindai.com"

STEP 2: Call firecrawl_scrape
- Call `firecrawl_scrape` with these exact parameters:
  url: <the URL you extracted>
  formats: ["markdown", "html", "links"]
  onlyMainContent: true
  timeout: 90000
- Note: timeout is 90 seconds (90000ms)

STEP 3: Analyze the scraped data
- Parse the markdown content to find title tag, meta description, H1, H2-H4 headings
- Count words in the main content
- Count internal and external links
- Identify technical SEO issues
- Identify content opportunities

STEP 4: Infer keywords
- Based on the page content, determine the primary keyword (1-3 words)
- Identify 2-5 secondary keywords
- Determine search intent (informational, transactional, navigational, commercial)
- List 3-5 supporting topics

STEP 5: Return JSON
- Populate EVERY field in the PageAuditOutput schema with actual data
- Use "Not available" only if truly missing from scraped data
- Return ONLY valid JSON, no extra text before or after""",
    tools=[firecrawl_toolset],
    output_schema=PageAuditOutput,
    output_key="page_audit",
)


serp_analyst_agent = LlmAgent(
    name="SerpAnalystAgent",
    model="gemini-2.5-flash",
    description=(
        "Researches the live SERP for the discovered primary keyword and summarizes the competitive landscape."
    ),
    instruction="""You are Agent 2 in the workflow. Your role is to silently gather SERP data for the final report agent.

STEP 1: Get the primary keyword
- Read `state['page_audit']['target_keywords']['primary_keyword']`
- Example: if it's "AI tools", you'll use that for search

STEP 2: Call perform_google_search
- IMPORTANT: You MUST call the `perform_google_search` tool
- Pass the primary keyword as the request parameter
- Example: if primary_keyword is "AI tools", call perform_google_search with request="AI tools"

STEP 3: Parse search results
- You should receive 10+ search results with title, url, snippet
- For each result (up to 10):
  * Assign rank (1-10)
  * Extract title
  * Extract URL
  * Extract snippet
  * Infer content_type (blog post, landing page, tool, directory, video, etc.)

STEP 4: Analyze patterns
- title_patterns: Common words/phrases in titles (e.g., "Best", "Top 10", "Free", year)
- content_formats: Types you see (guides, listicles, comparison pages, tool directories)
- people_also_ask: Related questions (infer from snippets if not explicit)
- key_themes: Recurring topics across results
- differentiation_opportunities: Gaps or unique angles not covered by competitors

STEP 5: Return JSON
- Populate ALL fields in SerpAnalysis schema
- top_10_results MUST have 10 items (or as many as you found)
- DO NOT return empty arrays unless search truly failed
- Return ONLY valid JSON, no extra text""",
    tools=[google_search_tool],
    output_schema=SerpAnalysis,
    output_key="serp_analysis",
)


optimization_advisor_agent = LlmAgent(
    name="OptimizationAdvisorAgent",
    model="gemini-2.5-flash",
    description="Synthesizes the audit and SERP findings into a prioritized optimization roadmap.",
    instruction="""You are Agent 3 and the final expert in the workflow. You create the user-facing report.

STEP 1: Review the data
- Read `state['page_audit']` for:
  * Title tag, meta description, H1
  * Word count, headings structure
  * Link counts
  * Technical findings
  * Content opportunities
  * Primary and secondary keywords
- Read `state['serp_analysis']` for:
  * Top 10 competitors
  * Title patterns
  * Content formats
  * Key themes
  * Differentiation opportunities

STEP 2: Create the report
Start with "# SEO Audit Report" and include these sections:

1. **Executive Summary** (2-3 paragraphs)
   - Page being audited
   - Primary keyword focus
   - Key strengths and weaknesses

2. **Technical & On-Page Findings**
   - Current title tag and suggestions
   - Current meta description and suggestions
   - H1 and heading structure analysis
   - Word count and content depth
   - Link profile (internal/external counts)
   - Technical issues found

3. **Keyword Analysis**
   - Primary keyword: [from state]
   - Secondary keywords: [list from state]
   - Search intent: [from state]
   - Supporting topics: [list from state]

4. **Competitive SERP Analysis**
   - What top competitors are doing
   - Common title patterns
   - Dominant content formats
   - Key themes in top results
   - Content gaps/opportunities

5. **Prioritized Recommendations**
   Group by P0/P1/P2 with:
   - Specific action
   - Rationale (cite data)
   - Expected impact
   - Effort level

6. **Next Steps**
   - Measurement plan
   - Timeline suggestions

STEP 3: Output
- Return ONLY Markdown
- NO JSON
- NO preamble text
- Start directly with "# SEO Audit Report"
- Be specific with data points (e.g., "Current title is X characters, recommend Y"
""",
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
