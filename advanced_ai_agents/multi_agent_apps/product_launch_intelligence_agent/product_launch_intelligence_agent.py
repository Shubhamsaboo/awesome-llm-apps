import streamlit as st
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.firecrawl import FirecrawlTools
from dotenv import load_dotenv
from datetime import datetime
from textwrap import dedent
import os

# ---------------- Page Config & Styles ----------------
st.set_page_config(page_title="Product Intelligence Agent", page_icon="🚀", layout="wide")

st.markdown(
    """
    <style>
    /* Custom CSS for a sleek look */
    .stButton>button {
        border-radius: 5px;
        height: 3em;
        font-weight: 600;
    }
    .analysis-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f9f9f9;
        border: 1px solid #e1e1e1;
    }
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 1.05rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- Environment & Agent ----------------
load_dotenv()

# Add API key inputs in sidebar
with st.sidebar.expander("🔑 API Keys", expanded=True):
    openai_key = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    firecrawl_key = st.text_input("Firecrawl API Key", type="password", value=os.getenv("FIRECRAWL_API_KEY", ""))

# Set environment variables
if openai_key:
    os.environ["OPENAI_API_KEY"] = openai_key
if firecrawl_key:
    os.environ["FIRECRAWL_API_KEY"] = firecrawl_key

# Initialize agent only if both keys are provided
if openai_key and firecrawl_key:
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
        """),
        model=OpenAIChat(id="gpt-4o"),
        tools=[FirecrawlTools(search=True, crawl=True, limit=8, poll_interval=10)],
        show_tool_calls=True,
        markdown=True,
        exponential_backoff=True,
        delay_between_retries=2,
    )
else:
    launch_analyst = None
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
    if not launch_analyst:
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
    long_resp = launch_analyst.run(prompt)
    return long_resp.content if hasattr(long_resp, "content") else str(long_resp)

# Helper to craft competitor-focused launch report for product managers
def expand_competitor_report(bullet_text: str, competitor: str) -> str:
    if not launch_analyst:
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
    resp = launch_analyst.run(prompt)
    return resp.content if hasattr(resp, "content") else str(resp)

# Helper to craft market sentiment report
def expand_sentiment_report(bullet_text: str, product: str) -> str:
    if not launch_analyst:
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
    resp = launch_analyst.run(prompt)
    return resp.content if hasattr(resp, "content") else str(resp)

# Helper to craft launch metrics report
def expand_metrics_report(bullet_text: str, launch: str) -> str:
    if not launch_analyst:
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
    resp = launch_analyst.run(prompt)
    return resp.content if hasattr(resp, "content") else str(resp)

# ---------------- UI ----------------
st.title("🚀 Product Launch Intelligence Agent")
st.caption("AI Agent powered insights for GTM, Product Marketing & Growth Teams")

# Create tabs for analysis types
analysis_tabs = st.tabs(["Competitor Analysis", "Market Sentiment", "Launch Metrics"])

# Persistent storage for latest response
if "analysis_response" not in st.session_state:
    st.session_state.analysis_response = None
    st.session_state.analysis_meta = {}

# -------- Competitor Analysis Tab --------
with analysis_tabs[0]:
    st.subheader("🔍 Competitor Launch Analysis")
    competitor_name = st.text_input("Competitor name", key="competitor_input")

    cols = st.columns([2, 1])
    with cols[0]:
        if st.button("Analyze", key="competitor_btn") and competitor_name:
            if not launch_analyst:
                st.error("⚠️ Please enter both API keys in the sidebar first.")
            else:
                with st.spinner("Gathering competitive insights..."):
                    try:
                        bullets = launch_analyst.run(
                            f"Generate up to 16 evidence-based insight bullets about {competitor_name}'s most recent product launches.\n"
                            f"Format requirements:\n"
                            f"• Start every bullet with exactly one tag: Positioning | Strength | Weakness | Learning\n"
                            f"• Follow the tag with a concise statement (max 30 words) referencing concrete observations: messaging, differentiation, pricing, channel selection, timing, engagement metrics, or customer feedback."
                        )
                        long_text = expand_competitor_report(
                            bullets.content if hasattr(bullets, "content") else str(bullets),
                            competitor_name
                        )
                        st.session_state.analysis_response = long_text
                        st.session_state.analysis_meta = {
                            "type": "Competitor Analysis",
                            "query": competitor_name,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        st.success("✅ Analysis ready")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    if st.session_state.analysis_response and st.session_state.analysis_meta.get("type") == "Competitor Analysis":
        st.markdown("### 📊 Results")
        st.markdown(st.session_state.analysis_response)

# -------- Market Sentiment Tab --------
with analysis_tabs[1]:
    st.subheader("💬 Market Sentiment Analysis")
    product_name = st.text_input("Product name", key="sentiment_input")

    cols = st.columns([2, 1])
    with cols[0]:
        if st.button("Analyze", key="sentiment_btn") and product_name:
            if not launch_analyst:
                st.error("⚠️ Please enter both API keys in the sidebar first.")
            else:
                with st.spinner("Collecting market sentiment..."):
                    try:
                        bullets = launch_analyst.run(
                            f"Summarize market sentiment for {product_name} in <=10 bullets. "
                            f"Cover top positive & negative themes with source mentions (G2, Reddit, Twitter)."
                        )
                        long_text = expand_sentiment_report(
                            bullets.content if hasattr(bullets, "content") else str(bullets),
                            product_name
                        )
                        st.session_state.analysis_response = long_text
                        st.session_state.analysis_meta = {
                            "type": "Market Sentiment",
                            "query": product_name,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        st.success("✅ Sentiment analysis ready")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    if st.session_state.analysis_response and st.session_state.analysis_meta.get("type") == "Market Sentiment":
        st.markdown("### 📈 Sentiment Insights")
        st.markdown(st.session_state.analysis_response)

# -------- Launch Metrics Tab --------
with analysis_tabs[2]:
    st.subheader("📈 Launch Performance Metrics")
    product_launch = st.text_input("Product name / Launch campaign", key="metrics_input")

    cols = st.columns([2, 1])
    with cols[0]:
        if st.button("Analyze", key="metrics_btn") and product_launch:
            if not launch_analyst:
                st.error("⚠️ Please enter both API keys in the sidebar first.")
            else:
                with st.spinner("Fetching launch performance data..."):
                    try:
                        bullets = launch_analyst.run(
                            f"List (max 10 bullets) the most important publicly available KPIs & qualitative signals for {product_launch}. "
                            f"Include engagement stats, press coverage and social traction if available."
                        )
                        long_text = expand_metrics_report(
                            bullets.content if hasattr(bullets, "content") else str(bullets),
                            product_launch
                        )
                        st.session_state.analysis_response = long_text
                        st.session_state.analysis_meta = {
                            "type": "Launch Metrics",
                            "query": product_launch,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        st.success("✅ Metrics analysis ready")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    if st.session_state.analysis_response and st.session_state.analysis_meta.get("type") == "Launch Metrics":
        st.markdown("### 📊 Metric Highlights")
        st.markdown(st.session_state.analysis_response)

# ---------------- Sidebar ----------------
st.sidebar.header("ℹ️ About")
st.sidebar.markdown(
    """
    **Product Launch Intelligence Agent** helps GTM teams quickly:
    - Benchmark competitor launches
    - Monitor market sentiment pre/post-launch
    - Track launch performance signals
    
    Built with **Agno** & **Firecrawl**.
    """
) 