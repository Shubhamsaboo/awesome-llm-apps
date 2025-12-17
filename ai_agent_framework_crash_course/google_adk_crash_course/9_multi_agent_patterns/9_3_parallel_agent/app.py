import streamlit as st
import asyncio
from agent import market_snapshot_team, gather_market_snapshot

st.set_page_config(page_title="Parallel Agent Demo", page_icon=":fast_forward:", layout="wide")

st.title("⚡ Market Snapshot with Gemini 3 Flash(Parallel Agents)")
st.markdown(
    """
This demo runs multiple research agents in parallel using a ParallelAgent:

- Market trends analysis
- Competitor intelligence
- Funding and partnerships news

Each sub-agent writes its results into a shared session.state under distinct keys. A subsequent step (or this UI) can read the combined snapshot.
"""
)

user_id = "demo_parallel_user"

st.header("Run a market snapshot")
topic = st.text_input(
    "Research topic",
    value="AI-powered customer support platforms",
    placeholder="What market/topic do you want a quick parallel snapshot on?",
)

if st.button("Run Parallel Research", type="primary"):
    if topic.strip():
        st.info("Running parallel agents… market trends, competitors, and funding news")
        with st.spinner("Gathering snapshot…"):
            try:
                results = asyncio.run(gather_market_snapshot(user_id, topic))
                st.success("Snapshot ready")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.subheader("Market Trends")
                    st.write(results.get("market_trends", ""))
                with col2:
                    st.subheader("Competitors")
                    st.write(results.get("competitors", ""))
                with col3:
                    st.subheader("Funding News")
                    st.write(results.get("funding_news", ""))
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.error("Please enter a topic")

with st.sidebar:
    st.header("How it works")
    st.markdown(
        """
        - Uses `ParallelAgent` to execute sub-agents concurrently
        - Each child runs on its own invocation branch, but shares the same session.state
        - Distinct `output_key`s prevent overwrites in the shared state
        - This pattern is ideal for fan-out data gathering before synthesis
        """
    )

