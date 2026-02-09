import streamlit as st
import os
from typing import List, Dict, Any

# Import pipeline components from main.py and agents
from main import collect_signals, DEFAULT_SIGNAL_LIMIT
from agents import (
    SignalCollectorAgent,
    RelevanceAgent,
    RiskAgent,
    SynthesisAgent
)

# Page Config
st.set_page_config(
    page_title="DevPulseAI – Signal Intelligence Demo",
    page_icon="🧠",
    layout="wide"
)

# Custom CSS for glassmorphism and premium feel
st.markdown("""
<style>
    .main {
        background: #0f172a;
        color: #f1f5f9;
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    .signal-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: transform 0.2s ease;
    }
    .signal-card:hover {
        transform: translateY(-5px);
        border-color: #3b82f6;
    }
    .badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .risk-low { background: #059669; color: white; }
    .risk-medium { background: #d97706; color: white; }
    .risk-high { background: #dc2626; color: white; }
    .risk-critical { background: #7f1d1d; color: white; }
    
    .relevance-score {
        font-size: 1.5rem;
        font-weight: 700;
        color: #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

# Title and Description
st.title("🧠 DevPulseAI – Signal Intelligence Demo")
st.markdown("""
This demo showcases a **multi-agent system** that aggregates technical signals from various developer sources, 
scores them for relevance, identifies potential risks, and synthesizes a final intelligence digest.
""")

# Sidebar Configuration
st.sidebar.header("⚙️ Pipeline Configuration")

# API Key
api_key = st.sidebar.text_input("Gemini API Key (optional)", type="password", help="Provide a Google Gemini API key. If not provided, agents will use fallback heuristic logic.")
if api_key:
    # Agno's GoogleGemini looks for GOOGLE_API_KEY
    os.environ["GOOGLE_API_KEY"] = api_key

# Source Selection
sources = st.sidebar.multiselect(
    "Signal Sources",
    ["GitHub", "ArXiv", "HackerNews", "Medium", "HuggingFace"],
    default=["GitHub", "ArXiv", "HackerNews", "Medium", "HuggingFace"]
)

# Signal Count Slider
signal_count = st.sidebar.slider(
    "Signals per source",
    min_value=4,
    max_value=32,
    value=DEFAULT_SIGNAL_LIMIT,
    step=4
)

run_button = st.sidebar.button("🚀 Run Intelligence Pipeline", use_container_width=True)

# Main Area Logic
if run_button:
    if not sources:
        st.warning("Please select at least one signal source.")
    else:
        # Initialize Agents
        collector = SignalCollectorAgent()
        relevance = RelevanceAgent()
        risk = RiskAgent()
        synthesis = SynthesisAgent()
        
        # Step 1: Collection
        with st.status("📡 Collecting and normalizing signals...", expanded=True) as status:
            st.write("Fetching raw data from sources...")
            
            # Map selected sources to fetch calls (simplified reuse)
            # We use the collect_signals logic but filter by selected sources
            raw_signals = []
            from adapters.github import fetch_github_trending
            from adapters.arxiv import fetch_arxiv_papers
            from adapters.hackernews import fetch_hackernews_stories
            from adapters.medium import fetch_medium_blogs
            from adapters.huggingface import fetch_huggingface_models
            
            if "GitHub" in sources:
                st.write("Fetching GitHub trending...")
                raw_signals.extend(fetch_github_trending(limit=signal_count))
            if "ArXiv" in sources:
                st.write("Fetching ArXiv papers...")
                raw_signals.extend(fetch_arxiv_papers(limit=signal_count))
            if "HackerNews" in sources:
                st.write("Fetching HackerNews stories...")
                raw_signals.extend(fetch_hackernews_stories(limit=signal_count))
            if "Medium" in sources:
                st.write("Fetching Medium blogs...")
                raw_signals.extend(fetch_medium_blogs(limit=min(signal_count, 3)))
            if "HuggingFace" in sources:
                st.write("Fetching HuggingFace models...")
                raw_signals.extend(fetch_huggingface_models(limit=signal_count))
            
            st.write(f"Normalizing {len(raw_signals)} raw signals...")
            normalized = collector.collect(raw_signals)
            status.update(label=f"✅ {len(normalized)} unique signals collected", state="complete")
        
        # Step 2: Analysis
        col1, col2 = st.columns(2)
        
        with col1:
            with st.status("📊 Scoring Relevance...") as status:
                scored = relevance.score_batch(normalized)
                status.update(label="✅ Relevance scoring complete", state="complete")
        
        with col2:
            with st.status("⚠️ Assessing Security Risks...") as status:
                assessed = risk.assess_batch(scored)
                status.update(label="✅ Risk assessment complete", state="complete")
        
        # Step 3: Synthesis
        with st.status("📋 Generating Intelligence Digest...") as status:
            digest = synthesis.synthesize(assessed)
            status.update(label="✅ Final synthesis complete", state="complete")
            
        # Display Results
        st.divider()
        st.header("📄 Intelligence Digest")
        
        # Executive Summary
        st.info(f"**Executive Summary:** {digest['executive_summary']}")
        
        # Recommendations
        st.subheader("💡 Recommendations")
        for rec in digest['recommendations']:
            st.write(f"• {rec}")
            
        st.divider()
        st.subheader("🎯 Priority Signals")
        
        # Display signals in expandable sections
        for signal in assessed:
            rel = signal.get("relevance", {})
            risk_info = signal.get("risk", {})
            risk_level = risk_info.get("risk_level", "UNKNOWN")
            
            with st.expander(f"[{signal['source'].upper()}] {signal['title']}"):
                col_a, col_b = st.columns([3, 1])
                
                with col_a:
                    st.write(f"**Description:** {signal['description']}")
                    st.write(f"**URL:** [{signal['url']}]({signal['url']})")
                    if risk_info.get("concerns"):
                        st.markdown("**Security Concerns:**")
                        for concern in risk_info["concerns"]:
                            st.write(f"- {concern}")
                
                with col_b:
                    st.markdown("<div style='text-align: center'>", unsafe_allow_html=True)
                    st.markdown(f"<div class='relevance-score'>{rel.get('score', 0)}</div>", unsafe_allow_html=True)
                    st.markdown("<small>RELEVANCE</small>", unsafe_allow_html=True)
                    
                    risk_class = f"risk-{risk_level.lower()}"
                    st.markdown(f"<div class='badge {risk_class}' style='margin-top:10px'>{risk_level} RISK</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    if rel.get("reasoning"):
                        st.caption(f"Reason: {rel['reasoning']}")

else:
    # Landing state
    st.image("https://raw.githubusercontent.com/Shubhamsaboo/awesome-llm-apps/main/advanced_ai_agents/multi_agent_apps/devpulse_ai/assets/logo.png", width=200) # Placeholder for logo logic
    st.info("👈 Use the sidebar to configure the pipeline and click 'Run' to begin.")
    
    # Educational Section
    with st.expander("🛠️ How it works", expanded=True):
        st.markdown("""
        1. **Collector Agent**: Gathers data from GitHub, ArXiv, HN, Medium, and HuggingFace.
        2. **Relevance Agent**: LLM analysis to score each signal for developer impact.
        3. **Risk Agent**: Scans for breaking changes, vulnerabilities, or deprecations.
        4. **Synthesis Agent**: Combines all findings into an actionable report.
        """)
