"""
AI Agent Discovery - Find and compare AI agents across multiple registries.
Uses Streamlit UI with OpenAI GPT-4o for intelligent agent recommendations.
"""

import os
import streamlit as st
import httpx
from openai import OpenAI

REGISTRY_BROKER_BASE = "https://hol.org/registry/api/v1"


def search_agents(query: str, limit: int = 20) -> dict:
    """Search for AI agents across multiple registries."""
    with httpx.Client(timeout=30.0) as client:
        response = client.get(
            f"{REGISTRY_BROKER_BASE}/search", params={"q": query, "limit": limit}
        )
        response.raise_for_status()
        return response.json()


def get_agent_details(uaid: str) -> dict:
    """Get detailed information about a specific agent."""
    with httpx.Client(timeout=30.0) as client:
        response = client.get(f"{REGISTRY_BROKER_BASE}/agents/{uaid}")
        response.raise_for_status()
        return response.json()


def get_search_facets() -> dict:
    """Get available search facets (categories, registries)."""
    with httpx.Client(timeout=30.0) as client:
        response = client.get(f"{REGISTRY_BROKER_BASE}/search/facets")
        response.raise_for_status()
        return response.json()


def analyze_agents_with_llm(client: OpenAI, query: str, agents: list) -> str:
    """Use GPT-4o to analyze and recommend agents based on user query."""
    if not agents:
        return "No agents found matching your query."

    agents_info = []
    for agent in agents[:10]:
        info = f"- {agent.get('name', 'Unknown')} ({agent.get('registry', 'Unknown')}): {agent.get('description', 'No description')[:200]}"
        agents_info.append(info)

    agents_text = "\n".join(agents_info)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """You are an AI agent discovery assistant. Analyze the available agents and provide recommendations based on the user's needs. Be concise and helpful. Explain which agents would be best for the user's use case and why.""",
            },
            {
                "role": "user",
                "content": f"User query: {query}\n\nAvailable agents:\n{agents_text}\n\nProvide recommendations for the best agents to use based on this query.",
            },
        ],
        temperature=0.7,
        max_tokens=1000,
    )

    return response.choices[0].message.content


def main():
    st.set_page_config(page_title="AI Agent Discovery", page_icon="🔍", layout="wide")

    st.title("🔍 AI Agent Discovery")
    st.markdown(
        "Find and compare AI agents across **NANDA**, **MCP**, **Virtuals**, **A2A**, and **ERC-8004** registries."
    )

    # Sidebar for API key
    with st.sidebar:
        st.header("Configuration")
        openai_api_key = st.text_input("OpenAI API Key", type="password")
        st.markdown("Get your API key from [OpenAI](https://platform.openai.com/)")

        st.divider()
        st.markdown("### About")
        st.markdown("""
        This app searches the [Registry Broker](https://hol.org/registry/docs) - 
        a universal index of AI agents across multiple registries:
        
        - **NANDA** - MIT's agent network
        - **MCP** - Model Context Protocol servers
        - **Virtuals** - On-chain AI agents
        - **A2A** - Agent-to-Agent protocol
        - **ERC-8004** - Ethereum agent standard
        """)

    # Main search interface
    col1, col2 = st.columns([3, 1])

    with col1:
        search_query = st.text_input(
            "Search for AI agents",
            placeholder="e.g., code review, data analysis, trading bot, database...",
        )

    with col2:
        num_results = st.selectbox("Results", [10, 20, 50], index=1)

    if st.button("🔍 Search Agents", type="primary"):
        if not search_query:
            st.warning("Please enter a search query.")
            return

        with st.spinner("Searching across registries..."):
            try:
                results = search_agents(search_query, limit=num_results)
                agents = results.get("agents", [])

                if not agents:
                    st.info("No agents found. Try a different search term.")
                    return

                st.success(f"Found {len(agents)} agents matching '{search_query}'")

                # Display results in tabs
                tab1, tab2 = st.tabs(["📋 Agent List", "🤖 AI Recommendations"])

                with tab1:
                    for agent in agents:
                        with st.expander(
                            f"**{agent.get('name', 'Unknown')}** - {agent.get('registry', 'Unknown')}"
                        ):
                            st.markdown(
                                f"**Description:** {agent.get('description', 'No description')}"
                            )
                            st.markdown(f"**UAID:** `{agent.get('uaid', 'N/A')}`")
                            if agent.get("capabilities"):
                                st.markdown(
                                    f"**Capabilities:** {', '.join(agent['capabilities'][:5])}"
                                )
                            if agent.get("url"):
                                st.markdown(f"[View Agent]({agent['url']})")

                with tab2:
                    if openai_api_key:
                        with st.spinner("Analyzing agents with GPT-4o..."):
                            client = OpenAI(api_key=openai_api_key)
                            analysis = analyze_agents_with_llm(
                                client, search_query, agents
                            )
                            st.markdown(analysis)
                    else:
                        st.warning(
                            "Enter your OpenAI API key in the sidebar to get AI-powered recommendations."
                        )

            except Exception as e:
                st.error(f"Error searching agents: {str(e)}")

    # Show available categories
    with st.expander("📂 Browse Categories"):
        try:
            facets = get_search_facets()
            if facets.get("registries"):
                st.markdown("**Available Registries:**")
                for registry in facets["registries"]:
                    st.markdown(f"- {registry}")
            if facets.get("categories"):
                st.markdown("**Categories:**")
                cols = st.columns(3)
                for i, category in enumerate(facets["categories"][:15]):
                    cols[i % 3].markdown(f"• {category}")
        except Exception:
            st.info("Could not load categories. Try searching directly.")


if __name__ == "__main__":
    main()
