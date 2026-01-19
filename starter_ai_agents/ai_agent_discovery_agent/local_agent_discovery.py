"""
AI Agent Discovery (Local) - Find and compare AI agents using local Ollama LLM.
No external API calls for LLM - all AI processing happens locally.
"""

import os
import streamlit as st
import httpx
import ollama

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


def analyze_agents_with_local_llm(query: str, agents: list) -> str:
    """Use local Ollama model to analyze and recommend agents."""
    if not agents:
        return "No agents found matching your query."

    agents_info = []
    for agent in agents[:10]:
        info = f"- {agent.get('name', 'Unknown')} ({agent.get('registry', 'Unknown')}): {agent.get('description', 'No description')[:200]}"
        agents_info.append(info)

    agents_text = "\n".join(agents_info)

    prompt = f"""You are an AI agent discovery assistant. Analyze the available agents and provide recommendations based on the user's needs.

User query: {query}

Available agents:
{agents_text}

Provide concise recommendations for the best agents to use based on this query. Explain why each recommended agent would be helpful."""

    response = ollama.chat(
        model="llama3.2", messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"]


def main():
    st.set_page_config(
        page_title="AI Agent Discovery (Local)", page_icon="🔍", layout="wide"
    )

    st.title("🔍 AI Agent Discovery (Local)")
    st.markdown(
        "Find and compare AI agents using **local Ollama LLM** - no external API keys required!"
    )

    # Sidebar
    with st.sidebar:
        st.header("About")
        st.markdown("""
        This app searches the [Registry Broker](https://hol.org/registry/docs) - 
        a universal index of AI agents across multiple registries:
        
        - **NANDA** - MIT's agent network
        - **MCP** - Model Context Protocol servers
        - **Virtuals** - On-chain AI agents
        - **A2A** - Agent-to-Agent protocol
        - **ERC-8004** - Ethereum agent standard
        
        ---
        
        **Requirements:**
        - Ollama installed and running
        - llama3.2 model pulled
        
        ```bash
        ollama pull llama3.2
        ```
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
                tab1, tab2 = st.tabs(["📋 Agent List", "🤖 Local AI Recommendations"])

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
                    with st.spinner("Analyzing agents with local Llama model..."):
                        try:
                            analysis = analyze_agents_with_local_llm(
                                search_query, agents
                            )
                            st.markdown(analysis)
                        except Exception as e:
                            st.error(f"Error with Ollama: {str(e)}")
                            st.info("Make sure Ollama is running: `ollama serve`")

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
