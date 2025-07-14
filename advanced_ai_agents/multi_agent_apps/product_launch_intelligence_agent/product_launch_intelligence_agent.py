import streamlit as st
from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat
from agno.tools.firecrawl import FirecrawlTools
from dotenv import load_dotenv
from datetime import datetime
from textwrap import dedent
import os

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="AI Product Intelligence Agent", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- Environment & Agent ----------------
load_dotenv()

# Add API key inputs in sidebar
st.sidebar.header("🔑 API Configuration")
with st.sidebar.container():
    openai_key = st.text_input(
        "OpenAI API Key", 
        type="password", 
        value=os.getenv("OPENAI_API_KEY", ""),
        help="Required for AI agent functionality"
    )
    firecrawl_key = st.text_input(
        "Firecrawl API Key", 
        type="password", 
        value=os.getenv("FIRECRAWL_API_KEY", ""),
        help="Required for web search and crawling"
    )

# Set environment variables
if openai_key:
    os.environ["OPENAI_API_KEY"] = openai_key
if firecrawl_key:
    os.environ["FIRECRAWL_API_KEY"] = firecrawl_key

# Initialize team only if both keys are provided
if openai_key and firecrawl_key:
    # Agent 1: Competitor Launch Analyst
    launch_analyst = Agent(
        name="Product Launch Analyst",
        description=dedent("""
            You are a senior Go-To-Market strategist who evaluates competitor product launches with a critical, evidence-driven lens.
            Your objective is to uncover:
            • How the product is positioned in the market
            • Which launch tactics drove success (strengths)
            • Where execution fell short (weaknesses)
            • Actionable learnings competitors can leverage
            Always cite observable signals (messaging, pricing actions, channel mix, timing, engagement metrics). Maintain a crisp, executive tone and focus on strategic value.
            IMPORTANT: Conclude your report with a 'Sources:' section, listing all URLs of websites you crawled or searched for this analysis.
        """),
        model=OpenAIChat(id="gpt-4o"),
        tools=[FirecrawlTools(search=True, crawl=True, poll_interval=10)],
        show_tool_calls=True,
        markdown=True,
        exponential_backoff=True,
        delay_between_retries=2,
    )
    
    # Agent 2: Market Sentiment Specialist
    sentiment_analyst = Agent(
        name="Market Sentiment Specialist",
        description=dedent("""
            You are a market research expert specializing in sentiment analysis and consumer perception tracking.
            Your expertise includes:
            • Analyzing social media sentiment and customer feedback
            • Identifying positive and negative sentiment drivers
            • Tracking brand perception trends across platforms
            • Monitoring customer satisfaction and review patterns
            • Providing actionable insights on market reception
            Focus on extracting sentiment signals from social platforms, review sites, forums, and customer feedback channels.
            IMPORTANT: Conclude your report with a 'Sources:' section, listing all URLs of websites you crawled or searched for this analysis.
        """),
        model=OpenAIChat(id="gpt-4o"),
        tools=[FirecrawlTools(search=True, crawl=True, poll_interval=10)],
        show_tool_calls=True,
        markdown=True,
        exponential_backoff=True,
        delay_between_retries=2,
    )
    
    # Agent 3: Launch Metrics Specialist
    metrics_analyst = Agent(
        name="Launch Metrics Specialist", 
        description=dedent("""
            You are a product launch performance analyst who specializes in tracking and analyzing launch KPIs.
            Your focus areas include:
            • User adoption and engagement metrics
            • Revenue and business performance indicators
            • Market penetration and growth rates
            • Press coverage and media attention analysis
            • Social media traction and viral coefficient tracking
            • Competitive market share analysis
            Always provide quantitative insights with context and benchmark against industry standards when possible.
            IMPORTANT: Conclude your report with a 'Sources:' section, listing all URLs of websites you crawled or searched for this analysis.
        """),
        model=OpenAIChat(id="gpt-4o"),
        tools=[FirecrawlTools(search=True, crawl=True, poll_interval=10)],
        show_tool_calls=True,
        markdown=True,
        exponential_backoff=True,
        delay_between_retries=2,
    )

    # Create the coordinated team
    product_intelligence_team = Team(
        name="Product Intelligence Team",
        mode="coordinate",
        model=OpenAIChat(id="gpt-4o"),
        members=[launch_analyst, sentiment_analyst, metrics_analyst],
        instructions=[
            "Coordinate the analysis based on the user's request type:",
            "1. For competitor analysis: Use the Product Launch Analyst to evaluate positioning, strengths, weaknesses, and strategic insights",
            "2. For market sentiment: Use the Market Sentiment Specialist to analyze social media sentiment, customer feedback, and brand perception",
            "3. For launch metrics: Use the Launch Metrics Specialist to track KPIs, adoption rates, press coverage, and performance indicators",
            "Always provide evidence-based insights with specific examples and data points",
            "Structure responses with clear sections and actionable recommendations",
            "Include sources section with all URLs crawled or searched"
        ],
        show_tool_calls=True,
        markdown=True,
        debug_mode=True,
        show_members_responses=True,
    )
else:
    product_intelligence_team = None
    st.warning("⚠️ Please enter both API keys in the sidebar to use the application.")

# ---------------- Helper to display response ----------------
def display_agent_response(resp):
    """Render different response structures nicely."""
    if hasattr(resp, "content") and resp.content:
        st.markdown(resp.content)
    elif hasattr(resp, "messages"):
        for m in resp.messages:
            if m.role == "assistant" and m.content:
                st.markdown(m.content)
    else:
        st.markdown(str(resp))

# Helper to expand bullet summary into 1200-word general report
def expand_insight(bullet_text: str, topic: str) -> str:
    if not product_intelligence_team:
        st.error("⚠️ Please enter both API keys in the sidebar first.")
        return ""
        
    prompt = (
        f"Using ONLY the bullet points below, craft an in-depth (~1200-word) launch analysis report on {topic}.\n"
        f"Structure:\n"
        f"1. Executive Summary (<120 words)\n"
        f"2. Strengths & Opportunities (what worked well)\n"
        f"3. Weaknesses & Gaps (what didn't work or could be improved)\n"
        f"4. Actionable Recommendations (bullet list)\n"
        f"5. Key Risks / Watch-outs\n\n"
        f"Bullet Points:\n{bullet_text}\n\n"
        f"Ensure analysis is objective, evidence-based and references the bullet insights. Keep paragraphs short (≤120 words)."
    )
    long_resp = product_intelligence_team.run(prompt)
    return long_resp.content if hasattr(long_resp, "content") else str(long_resp)

# Helper to craft competitor-focused launch report for product managers
def expand_competitor_report(bullet_text: str, competitor: str) -> str:
    if not product_intelligence_team:
        st.error("⚠️ Please enter both API keys in the sidebar first.")
        return ""

    prompt = (
        f"Transform the insight bullets below into a professional launch review for product managers analysing {competitor}.\n\n"
        f"Produce well-structured **Markdown** with a mix of tables, call-outs and concise bullet points — avoid long paragraphs.\n\n"
        f"=== FORMAT SPECIFICATION ===\n"
        f"# {competitor} – Launch Review\n\n"
        f"## 1. Market & Product Positioning\n"
        f"• Bullet point summary of how the product is positioned (max 6 bullets).\n\n"
        f"## 2. Launch Strengths\n"
        f"| Strength | Evidence / Rationale |\n|---|---|\n| … | … | (add 4-6 rows)\n\n"
        f"## 3. Launch Weaknesses\n"
        f"| Weakness | Evidence / Rationale |\n|---|---|\n| … | … | (add 4-6 rows)\n\n"
        f"## 4. Strategic Takeaways for Competitors\n"
        f"1. … (max 5 numbered recommendations)\n\n"
        f"=== SOURCE BULLETS ===\n{bullet_text}\n\n"
        f"Guidelines:\n"
        f"• Populate the tables with specific points derived from the bullets.\n"
        f"• Only include rows that contain meaningful data; omit any blank entries."
    )
    resp = product_intelligence_team.run(prompt)
    return resp.content if hasattr(resp, "content") else str(resp)

# Helper to craft market sentiment report
def expand_sentiment_report(bullet_text: str, product: str) -> str:
    if not product_intelligence_team:
        st.error("⚠️ Please enter both API keys in the sidebar first.")
        return ""

    prompt = (
        f"Use the tagged bullets below to create a concise market-sentiment brief for **{product}**.\n\n"
        f"### Positive Sentiment\n"
        f"• List each positive point as a separate bullet (max 6).\n\n"
        f"### Negative Sentiment\n"
        f"• List each negative point as a separate bullet (max 6).\n\n"
        f"### Overall Summary\n"
        f"Provide a short paragraph (≤120 words) summarising the overall sentiment balance and key drivers.\n\n"
        f"Tagged Bullets:\n{bullet_text}"
    )
    resp = product_intelligence_team.run(prompt)
    return resp.content if hasattr(resp, "content") else str(resp)

# Helper to craft launch metrics report
def expand_metrics_report(bullet_text: str, launch: str) -> str:
    if not product_intelligence_team:
        st.error("⚠️ Please enter both API keys in the sidebar first.")
        return ""

    prompt = (
        f"Convert the KPI bullets below into a launch-performance snapshot for **{launch}** suitable for an executive dashboard.\n\n"
        f"## Key Performance Indicators\n"
        f"| Metric | Value / Detail | Source |\n"
        f"|---|---|---|\n"
        f"| … | … | … |  (include one row per KPI)\n\n"
        f"## Qualitative Signals\n"
        f"• Bullet list of notable qualitative insights (max 5).\n\n"
        f"## Summary & Implications\n"
        f"Brief paragraph (≤120 words) highlighting what the metrics imply about launch success and next steps.\n\n"
        f"KPI Bullets:\n{bullet_text}"
    )
    resp = product_intelligence_team.run(prompt)
    return resp.content if hasattr(resp, "content") else str(resp)

# ---------------- UI ----------------
st.title("🚀 AI Product Launch Intelligence Agent")
st.markdown("*AI-powered insights for GTM, Product Marketing & Growth Teams*")

st.divider()

# Company input section
st.subheader("🏢 Company Analysis")
with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        company_name = st.text_input(
            label="Company Name",
            placeholder="Enter company name (e.g., OpenAI, Tesla, Spotify)",
            help="This company will be analyzed by the coordinated team of specialized agents",
            label_visibility="collapsed"
        )
    with col2:
        if company_name:
            st.success(f"✓ Ready to analyze **{company_name}**")

st.divider()

# Create tabs for analysis types
analysis_tabs = st.tabs([
    "🔍 Competitor Analysis", 
    "💬 Market Sentiment", 
    "📈 Launch Metrics"
])

# Persistent storage for latest response
if "analysis_response" not in st.session_state:
    st.session_state.analysis_response = None
    st.session_state.analysis_meta = {}

# Store separate responses for each agent
if "competitor_response" not in st.session_state:
    st.session_state.competitor_response = None
if "sentiment_response" not in st.session_state:
    st.session_state.sentiment_response = None
if "metrics_response" not in st.session_state:
    st.session_state.metrics_response = None

# -------- Competitor Analysis Tab --------
with analysis_tabs[0]:
    with st.container():
        st.markdown("### 🔍 Competitor Launch Analysis")
        
        with st.expander("ℹ️ About this Agent", expanded=False):
            st.markdown("""
            **Product Launch Analyst** - Strategic GTM Expert
            
            Specializes in:
            - Competitive positioning analysis
            - Launch strategy evaluation  
            - Strengths & weaknesses identification
            - Strategic recommendations
            """)
        
        if company_name:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                analyze_btn = st.button(
                    "🚀 Analyze Competitor Strategy", 
                    key="competitor_btn", 
                    type="primary",
                    use_container_width=True
                )
            
            with col2:
                if st.session_state.competitor_response:
                    st.success("✅ Analysis Complete")
                else:
                    st.info("⏳ Ready to analyze")
            
            if analyze_btn:
                if not product_intelligence_team:
                    st.error("⚠️ Please enter both API keys in the sidebar first.")
                else:
                    with st.spinner("🔍 Product Intelligence Team analyzing competitive strategy..."):
                        try:
                            bullets = product_intelligence_team.run(
                                f"Generate up to 16 evidence-based insight bullets about {company_name}'s most recent product launches.\n"
                                f"Format requirements:\n"
                                f"• Start every bullet with exactly one tag: Positioning | Strength | Weakness | Learning\n"
                                f"• Follow the tag with a concise statement (max 30 words) referencing concrete observations: messaging, differentiation, pricing, channel selection, timing, engagement metrics, or customer feedback."
                            )
                            long_text = expand_competitor_report(
                                bullets.content if hasattr(bullets, "content") else str(bullets),
                                company_name
                            )
                            st.session_state.competitor_response = long_text
                            st.success("✅ Competitor analysis ready")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
            
            # Display results
            if st.session_state.competitor_response:
                st.divider()
                with st.container():
                    st.markdown("### 📊 Analysis Results")
                    st.markdown(st.session_state.competitor_response)
        else:
            st.info("👆 Please enter a company name above to start the analysis")

# -------- Market Sentiment Tab --------
with analysis_tabs[1]:
    with st.container():
        st.markdown("### 💬 Market Sentiment Analysis")
        
        with st.expander("ℹ️ About this Agent", expanded=False):
            st.markdown("""
            **Market Sentiment Specialist** - Consumer Perception Expert
            
            Specializes in:
            - Social media sentiment tracking
            - Customer feedback analysis
            - Brand perception monitoring
            - Review pattern identification
            """)
        
        if company_name:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                sentiment_btn = st.button(
                    "📊 Analyze Market Sentiment", 
                    key="sentiment_btn", 
                    type="primary",
                    use_container_width=True
                )
            
            with col2:
                if st.session_state.sentiment_response:
                    st.success("✅ Analysis Complete")
                else:
                    st.info("⏳ Ready to analyze")
            
            if sentiment_btn:
                if not product_intelligence_team:
                    st.error("⚠️ Please enter both API keys in the sidebar first.")
                else:
                    with st.spinner("💬 Product Intelligence Team analyzing market sentiment..."):
                        try:
                            bullets = product_intelligence_team.run(
                                f"Summarize market sentiment for {company_name} in <=10 bullets. "
                                f"Cover top positive & negative themes with source mentions (G2, Reddit, Twitter, customer reviews)."
                            )
                            long_text = expand_sentiment_report(
                                bullets.content if hasattr(bullets, "content") else str(bullets),
                                company_name
                            )
                            st.session_state.sentiment_response = long_text
                            st.success("✅ Sentiment analysis ready")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
            
            # Display results
            if st.session_state.sentiment_response:
                st.divider()
                with st.container():
                    st.markdown("### 📈 Analysis Results")
                    st.markdown(st.session_state.sentiment_response)
        else:
            st.info("👆 Please enter a company name above to start the analysis")

# -------- Launch Metrics Tab --------
with analysis_tabs[2]:
    with st.container():
        st.markdown("### 📈 Launch Performance Metrics")
        
        with st.expander("ℹ️ About this Agent", expanded=False):
            st.markdown("""
            **Launch Metrics Specialist** - Performance Analytics Expert
            
            Specializes in:
            - User adoption metrics tracking
            - Revenue performance analysis
            - Market penetration evaluation
            - Press coverage monitoring
            """)
        
        if company_name:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                metrics_btn = st.button(
                    "📊 Analyze Launch Metrics", 
                    key="metrics_btn", 
                    type="primary",
                    use_container_width=True
                )
            
            with col2:
                if st.session_state.metrics_response:
                    st.success("✅ Analysis Complete")
                else:
                    st.info("⏳ Ready to analyze")
            
            if metrics_btn:
                if not product_intelligence_team:
                    st.error("⚠️ Please enter both API keys in the sidebar first.")
                else:
                    with st.spinner("📈 Product Intelligence Team analyzing launch metrics..."):
                        try:
                            bullets = product_intelligence_team.run(
                                f"List (max 10 bullets) the most important publicly available KPIs & qualitative signals for {company_name}'s recent product launches. "
                                f"Include engagement stats, press coverage, adoption metrics, and market traction data if available."
                            )
                            long_text = expand_metrics_report(
                                bullets.content if hasattr(bullets, "content") else str(bullets),
                                company_name
                            )
                            st.session_state.metrics_response = long_text
                            st.success("✅ Metrics analysis ready")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
            
            # Display results
            if st.session_state.metrics_response:
                st.divider()
                with st.container():
                    st.markdown("### 📊 Analysis Results")
                    st.markdown(st.session_state.metrics_response)
        else:
            st.info("👆 Please enter a company name above to start the analysis")

# ---------------- Sidebar ----------------
# Agent status indicators
with st.sidebar.container():
    st.markdown("### 🤖 System Status")
    if openai_key and firecrawl_key:
        st.success("✅ Product Intelligence Team ready")
    else:
        st.error("❌ API keys required")

st.sidebar.divider()

# Multi-agent system info
with st.sidebar.container():
    st.markdown("### 🎯 Coordinated Team")
    
    agents_info = [
        ("🔍", "Product Launch Analyst", "Strategic GTM expert"),
        ("💬", "Market Sentiment Specialist", "Consumer perception expert"),
        ("📈", "Launch Metrics Specialist", "Performance analytics expert")
    ]
    
    for icon, name, desc in agents_info:
        with st.container():
            st.markdown(f"**{icon} {name}**")
            st.caption(desc)

st.sidebar.divider()

# Analysis status
if company_name:
    with st.sidebar.container():
        st.markdown("### 📊 Analysis Status")
        st.markdown(f"**Company:** {company_name}")
        
        status_items = [
            ("🔍", "Competitor Analysis", st.session_state.competitor_response),
            ("💬", "Sentiment Analysis", st.session_state.sentiment_response),
            ("📈", "Metrics Analysis", st.session_state.metrics_response)
        ]
        
        for icon, name, status in status_items:
            if status:
                st.success(f"{icon} {name} ✓")
            else:
                st.info(f"{icon} {name} ⏳")

    st.sidebar.divider()

# Quick actions
with st.sidebar.container():
    st.markdown("### ⚡ Quick Actions")
    if company_name:
        st.markdown("""
        **J** - Competitor analysis  
        **K** - Market sentiment  
        **L** - Launch metrics
        """)
