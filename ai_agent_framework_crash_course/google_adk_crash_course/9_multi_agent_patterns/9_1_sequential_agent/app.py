import streamlit as st
import asyncio
from agent import business_intelligence_team, analyze_business_intelligence

# Page configuration
st.set_page_config(
    page_title="Sequential Agent Demo",
    page_icon=":arrow_right:",
    layout="wide"
)

# Title and description
st.title("🚀 Business Implementation Plan Generator Agent")
st.markdown("""
This **Business Implementation Plan Generator Agent** analyzes business opportunities through a comprehensive 4-step process:

1. **🔍 Market Analysis** - Researches market, competitors, and trends using web search
2. **📊 SWOT Analysis** - Identifies strengths, weaknesses, opportunities, and threats  
3. **🎯 Strategy Development** - Creates strategic objectives and action plans
4. **📋 Implementation Planning** - Generates detailed business implementation roadmap

**Result**: A complete business implementation plan ready for execution.
""")

# This is a placeholder user_id for demo purposes.
# In a real app, you might use authentication or session state to set this.
user_id = "demo_user"

# Sample business topics
sample_topics = [
    "Electric vehicle charging stations in urban areas",
    "AI-powered healthcare diagnostics",
    "Sustainable food delivery services",
    "Remote work collaboration tools",
    "Renewable energy storage solutions"
]

# Main content
st.header("Generate Your Business Implementation Plan")

# Topic input
business_topic = st.text_area(
    "Enter a business opportunity to analyze:",
    value=sample_topics[0],
    height=100,
    placeholder="Describe a business opportunity, industry, or market you'd like to analyze for implementation planning..."
)

# Sample topics
st.subheader("Or choose from sample business opportunities:")
cols = st.columns(len(sample_topics))
for i, topic in enumerate(sample_topics):
    if cols[i].button(topic, key=f"topic_{i}"):
        business_topic = topic
        st.rerun()

# Analysis button
if st.button("🚀 Generate Business Implementation Plan", type="primary"):
    if business_topic.strip():
        st.info("🚀 Starting business analysis... This will research the market, perform SWOT analysis, develop strategy, and create an implementation plan.")
        
        # Display the workflow
        st.subheader("Business Analysis Workflow")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("**1. Market Analysis**")
            st.markdown("🔍 Web search + competitive research")
        
        with col2:
            st.markdown("**2. SWOT Analysis**")
            st.markdown("📊 Strengths, Weaknesses, Opportunities, Threats")
        
        with col3:
            st.markdown("**3. Strategy Development**")
            st.markdown("🎯 Strategic objectives and action plans")
        
        with col4:
            st.markdown("**4. Implementation Planning**")
            st.markdown("📋 Detailed roadmap and execution plan")
        
        # Run the actual analysis
        with st.spinner("Generating comprehensive business implementation plan..."):
            try:
                result = asyncio.run(analyze_business_intelligence(user_id, business_topic))
                
                st.success("✅ Business Implementation Plan Generated!")
                st.subheader("Your Business Implementation Plan")
                st.markdown(result)
                
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                st.info("Make sure you have set up your GOOGLE_API_KEY in the .env file")
        
    else:
        st.error("Please enter a business opportunity to analyze.")

# How it works (in sidebar)
with st.sidebar:
    st.header("How It Works")
    st.markdown("""
    The **Business Implementation Plan Generator Agent** uses a sophisticated sequential workflow to create comprehensive business plans:

    1. **🔍 Market Analysis Agent**: Uses web search to research current market conditions, competitors, and trends
    2. **📊 SWOT Analysis Agent**: Analyzes the market research to identify strategic insights  
    3. **🎯 Strategy Development Agent**: Creates strategic objectives and action plans based on SWOT analysis
    4. **📋 Implementation Planning Agent**: Develops detailed execution roadmaps and resource requirements

    **Key Innovation**: The Market Analysis Agent has access to a specialized Search Agent (wrapped as AgentTool) that can perform real-time web searches for current market intelligence.

    Each agent builds upon the previous agent's output, creating a comprehensive business implementation plan ready for execution.
    """)
