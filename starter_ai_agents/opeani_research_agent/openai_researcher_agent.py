"""
Streamlit UI for Research Agent
"""

import os
import streamlit as st
from .research_agent import deep_search_api_first


def main():
    st.title("Deep Search (API-first)")

    # Sidebar controls
    topic = st.sidebar.text_input("Topic", "cross-border payments fintech")
    days = st.sidebar.radio("Days window", [7, 30, 90], index=2)
    max_items = st.sidebar.slider("Max items", 6, 10, 8)

    tab_live, tab_brief, tab_diag = st.tabs(["Live research", "Brief", "Diagnostics"])

    # Live research tab
    with tab_live:
        st.write("Running deep search…")
        result = deep_search_api_first(topic=topic, days=days, max_items=max_items)
        if "search_log" in result:
            with st.expander("Search log"):
                st.json(result["search_log"])

    # Brief tab
    with tab_brief:
        items = result.get("items", [])
        if not items:
            st.warning("No items returned.")
        else:
            if result.get("summary"):
                st.markdown(f"**Executive Summary**: {result['summary']}")
            st.markdown(f"### What changed in the last {days} days")
            for it in items:
                date = it.get("date") or "Unknown"
                title = it.get("title") or "(no title)"
                one = it.get("one_liner") or ""
                src = it.get("source") or ""
                url = it.get("url") or ""
                st.markdown(f"- {date} — **{title}**: {one} [{src}]({url})")

    # Diagnostics tab
    with tab_diag:
        keys = {
            "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
            "PERPLEXITY_API_KEY": bool(os.getenv("PERPLEXITY_API_KEY")),
            "TAVILY_API_KEY": bool(os.getenv("TAVILY_API_KEY")),
            "FIRECRAWL_API_KEY": bool(os.getenv("FIRECRAWL_API_KEY")),
        }
        st.write({k: ("OK" if v else "MISSING") for k, v in keys.items()})


if __name__ == "__main__":
    main()
