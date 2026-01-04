# 📊 AI Due Diligence Agent

A multi-agent AI pipeline for startup investment analysis, built with [Google ADK](https://google.github.io/adk-docs/), Gemini 3 Pro, Gemini 3 Flash and Nano Banana Pro.

**Works with any startup** - from early-stage unknowns to well-funded companies. Just provide a company name, website URL, or both.

## Features

- 🔍 **Live Research** - Real-time web search for company and market data
- 🌐 **URL Support** - Analyze any startup by their website URL
- 📈 **Revenue Charts** - Bear/Base/Bull projection charts with matplotlib
- 🧠 **Deep Risk Analysis** - Comprehensive risk assessment across 5 categories
- 📄 **Professional Reports** - McKinsey-style HTML investment reports
- 🎨 **Visual TL;DR** - AI-generated infographic summary for quick review

## What It Does

Given a startup name or URL, the pipeline automatically:

1. **Researches the company** - Founders, funding, product, traction
2. **Analyzes the market** - TAM/SAM, competitors, positioning
3. **Builds financial models** - Revenue projections, unit economics
4. **Assesses risks** - Market, execution, financial, regulatory, exit
5. **Generates investor memo** - Structured investment thesis
6. **Creates HTML report** - Professional due diligence document
7. **Generates infographic** - Visual summary for quick review

## Quick Start

### 1. Clone & Navigate
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_ai_agents/multi_agent_apps/ai_due_diligence_agent
```

### 2. Set Environment
```bash
export GOOGLE_API_KEY=your_api_key
# Or create .env file:
echo "GOOGLE_API_KEY=your_api_key" > .env
```

### 3. Install & Run
```bash
pip install -r requirements.txt
adk web
```

### 4. Try It
Open `http://localhost:8000` and try:
- *"Analyze https://agno.com for Series A investment"*
- *"Due diligence on Lovable - the AI app builder"*
- *"Evaluate Cursor IDE at https://cursor.com"*

## Example Prompts

Works with company names, URLs, or both:

| Input Type | Prompt |
|------------|--------|
| URL only | "Analyze https://agno.com for investment" |
| Name only | "Due diligence on Lovable AI" |
| Both | "Evaluate Cursor IDE at https://cursor.com" |
| Early-stage | "Research https://v0.dev - Vercel's AI tool" |
| Unknown startup | "Check out this startup: https://replit.com" |

---

## Pipeline Architecture

```
User Query: "Analyze https://agno.com for Series A"
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│              DueDiligencePipeline (SequentialAgent)             │
│                                                                 │
│  ┌─────────────┐    ┌────────────────┐    ┌──────────────────┐  │
│  │  Stage 1    │    │    Stage 2     │    │     Stage 3      │  │
│  │  Company    │───▶│    Market      │───▶│    Financial     │  │
│  │  Research   │    │    Analysis    │    │    Modeling      │  │
│  └─────────────┘    └────────────────┘    └──────────────────┘  │
│         │                   │                      │            │
│         ▼                   ▼                      ▼            │
│  ┌─────────────┐    ┌────────────────┐    ┌──────────────────┐  │
│  │  Stage 4    │    │    Stage 5     │    │     Stage 6      │  │
│  │    Risk     │───▶│   Investor     │───▶│     Report       │  │
│  │ Assessment  │    │     Memo       │    │    Generator     │  │
│  └─────────────┘    └────────────────┘    └──────────────────┘  │
│                                                    │            │
│                                                    ▼            │
│                                          ┌──────────────────┐   │
│                                          │     Stage 7      │   │
│                                          │   Infographic    │   │
│                                          │    Generator     │   │
│                                          └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
Artifacts: revenue_chart.png, investment_report.html, infographic.png
```

---

## Agent Details

### Stage 1: Company Research Agent

**Purpose:** Gathers comprehensive company information through web search.

| Property | Value |
|----------|-------|
| Model | `gemini-3-flash-preview` |
| Tools | `google_search` |
| Output Key | `company_info` |

**What it researches:**
- **Company Basics** - What they do, founding date, HQ location, team size
- **Founders & Team** - Key people, backgrounds, LinkedIn profiles
- **Product/Technology** - Core offering, how it works, target customers
- **Funding History** - Rounds raised, investors, amounts
- **Traction** - Customers, partnerships, growth signals
- **Recent News** - Press coverage, product launches, announcements

**For early-stage startups:** Checks website, LinkedIn, Crunchbase, AngelList, founder interviews, and notes when information is limited.

---

### Stage 2: Market Analysis Agent

**Purpose:** Analyzes market size, competition, and positioning.

| Property | Value |
|----------|-------|
| Model | `gemini-3-flash-preview` |
| Tools | `google_search` |
| Input | `{company_info}` |
| Output Key | `market_analysis` |

**What it analyzes:**
- **Market Size** - TAM, SAM, growth rate from industry reports
- **Competitors** - Who else is in the space, their funding/traction
- **Positioning** - How the company differentiates
- **Trends** - Market drivers, emerging tech, regulatory changes

**For early-stage:** Focuses on broader market category, identifies well-funded competitors, looks for market validation signals.

---

### Stage 3: Financial Modeling Agent

**Purpose:** Builds revenue projections and generates financial charts.

| Property | Value |
|----------|-------|
| Model | `gemini-3-pro-preview` |
| Tools | `generate_financial_chart` |
| Input | `{company_info}`, `{market_analysis}` |
| Output Key | `financial_model` |

**What it calculates:**
- **Current Metrics** - Estimated ARR, growth stage
- **Growth Scenarios** (5-year projections):
  - Bear Case: Conservative growth rates
  - Base Case: Expected trajectory
  - Bull Case: Optimistic scenario
- **Return Analysis** - Exit valuations, MOIC, IRR estimates

**Stage benchmarks:**
- Seed: $0.1-0.5M ARR, 3-5x growth
- Series A: $1-3M ARR, 2-3x growth
- Series B: $5-15M ARR, 1.5-2x growth

**Artifact:** Saves `revenue_chart_TIMESTAMP.png` with Bear/Base/Bull projections.

---

### Stage 4: Risk Assessment Agent

**Purpose:** Conducts deep risk analysis across multiple categories.

| Property | Value |
|----------|-------|
| Model | `gemini-3-pro-preview` |
| Tools | None (extended reasoning) |
| Input | `{company_info}`, `{market_analysis}`, `{financial_model}` |
| Output Key | `risk_assessment` |

**Risk categories analyzed:**
1. **Market Risk** - Competition, timing, adoption barriers
2. **Execution Risk** - Team gaps, technology challenges, scaling
3. **Financial Risk** - Burn rate, fundraising, unit economics
4. **Regulatory Risk** - Compliance, legal, geopolitical
5. **Exit Risk** - Acquirer landscape, IPO viability

**For each risk provides:**
- Severity (Low/Medium/High/Critical)
- Description with evidence
- Mitigation strategy

**Final output:**
- Overall Risk Score (1-10)
- Top 3 risks that could kill the investment
- Recommended protective terms

---

### Stage 5: Investor Memo Agent

**Purpose:** Synthesizes all findings into a structured investment memo.

| Property | Value |
|----------|-------|
| Model | `gemini-3-pro-preview` |
| Tools | None |
| Input | All previous stages |
| Output Key | `investor_memo` |

**Memo structure:**
1. **Executive Summary** - Company one-liner, recommendation, key highlights
2. **Company Overview** - What they do, team, product/technology
3. **Funding & Valuation** - History, estimated valuation range
4. **Market Opportunity** - Size, growth, competitors, differentiation
5. **Financial Analysis** - Revenue, unit economics, runway
6. **Risk Analysis** - Top risks with severity, overall score
7. **Investment Thesis** - Why invest, concerns, return scenarios
8. **Recommendation** - Final verdict, suggested next steps

**Recommendations:** Strong Buy / Buy / Hold / Pass

---

### Stage 6: Report Generator Agent

**Purpose:** Creates a professional HTML investment report.

| Property | Value |
|----------|-------|
| Model | `gemini-3-flash-preview` |
| Tools | `generate_html_report` |
| Input | `{investor_memo}` |
| Output Key | `html_report_result` |

**Report features:**
- McKinsey/Goldman Sachs styling
- Dark blue (#1a365d) and gold (#d4af37) color scheme
- Executive summary at top
- Clear section headers with professional typography
- Data tables for metrics
- Print-friendly layout

**Artifact:** Saves `investment_report_TIMESTAMP.html` viewable in any browser.

---

### Stage 7: Infographic Generator Agent

**Purpose:** Creates a visual summary infographic using AI image generation.

| Property | Value |
|----------|-------|
| Model | `gemini-3-flash-preview` |
| Tools | `generate_infographic` (uses `gemini-3-pro-image-preview`) |
| Input | `{investor_memo}` |
| Output Key | `infographic_result` |

**Infographic includes:**
- Company name prominently displayed
- Key metrics in large, bold numbers
- Market size visualization
- Risk score indicator (1-10 scale)
- Investment recommendation badge
- Professional investment banking aesthetic

**Artifact:** Saves `infographic_TIMESTAMP.png` for quick visual review.

---

## Project Structure

```
ai_due_diligence_agent/
├── __init__.py        # Exports root_agent
├── agent.py           # All 7 agents + pipeline defined here
├── tools.py           # Custom tools (chart, report, infographic)
├── outputs/           # Generated artifacts saved here
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## Generated Artifacts

All artifacts are saved to the **Artifacts tab** in ADK web and the **`outputs/`** folder:

```
outputs/
├── revenue_chart_20260104_143030.png       # Financial projections
├── investment_report_20260104_143052.html  # Full HTML report
└── infographic_20260104_143105.png         # Visual TL;DR
```

| Artifact | Format | Description |
|----------|--------|-------------|
| Revenue Chart | PNG | Bear/Base/Bull 5-year projections |
| Investment Report | HTML | Full due diligence document |
| Infographic | PNG/JPG | Visual summary one-pager |

---

## ADK Features Demonstrated

| Feature | Usage |
|---------|-------|
| **SequentialAgent** | 7-stage pipeline orchestration |
| **LlmAgent** | All specialized agents |
| **google_search** | Real-time company/market research |
| **Custom Tools** | Chart generation, HTML reports, infographics |
| **Artifacts** | Saving and versioning generated files |
| **State Management** | Passing data between pipeline stages via `output_key` |
| **Multi-modal Output** | Text analysis + image generation |

## Models Used

| Agent | Model | Why |
|-------|-------|-----|
| CompanyResearch | `gemini-3-flash-preview` | Fast web search |
| MarketAnalysis | `gemini-3-flash-preview` | Fast web search |
| FinancialModeling | `gemini-3-pro-preview` | Complex calculations |
| RiskAssessment | `gemini-3-pro-preview` | Deep reasoning |
| InvestorMemo | `gemini-3-pro-preview` | Synthesis quality |
| ReportGenerator | `gemini-3-flash-preview` | Fast HTML generation |
| InfographicGenerator | `gemini-3-flash-preview` | Orchestration |
| Infographic Tool | `gemini-3-pro-image-preview` | Image generation |

---

## Learn More

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Multi Agent Patterns in ADK](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
- [Gemini API](https://ai.google.dev/gemini-api/docs)
- [Gemini Image Generation](https://ai.google.dev/gemini-api/docs/image-generation)
