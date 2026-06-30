from textwrap import dedent

import streamlit as st
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.scavio import ScavioTools

st.set_page_config(page_title="Real-Time Research Agent", page_icon="🔎", layout="wide")
st.title("🔎 AI Real-Time Research Agent")
st.markdown(
    "Ask anything. This agent searches **Google, Reddit, and YouTube in real time** via "
    "[Scavio](https://scavio.dev) and writes a cited briefing — web facts, real community "
    "opinion, and video sources in one answer. No stale training data, no scraping to maintain."
)

with st.sidebar:
    st.header("API Keys")
    openai_key = st.text_input("OpenAI API Key", type="password")
    scavio_key = st.text_input(
        "Scavio API Key",
        type="password",
        help="Free key, 50 credits, no card required.",
    )
    st.markdown("[Get a free Scavio key →](https://dashboard.scavio.dev)")
    st.divider()
    sources = st.multiselect(
        "Sources to search",
        ["Google", "Reddit", "YouTube"],
        default=["Google", "Reddit", "YouTube"],
    )

query = st.text_input(
    "What do you want to research?",
    placeholder="e.g. Is the Framework Laptop worth it in 2026?",
)

if st.button("Research", type="primary"):
    if not openai_key or not scavio_key:
        st.error("Add your OpenAI and Scavio API keys in the sidebar.")
    elif not query:
        st.warning("Enter a research question.")
    elif not sources:
        st.warning("Pick at least one source.")
    else:
        agent = Agent(
            model=OpenAIChat(id="gpt-5.5", api_key=openai_key),
            tools=[
                ScavioTools(
                    api_key=scavio_key,
                    enable_google="Google" in sources,
                    enable_reddit="Reddit" in sources,
                    enable_youtube="YouTube" in sources,
                    enable_amazon=False,
                    enable_walmart=False,
                    enable_tiktok=False,
                    enable_instagram=False,
                )
            ],
            instructions=dedent(
                """\
                You are a research analyst. For the user's question:
                - Search the web (Google) for authoritative, up-to-date facts.
                - Search Reddit for first-hand community opinion, caveats, and edge cases.
                - Search YouTube for relevant reviews or explainers.
                Then write a concise briefing with, in this order:
                1. A direct one-paragraph answer.
                2. Key findings as bullet points.
                3. What the community actually says (Reddit sentiment, the good and the bad).
                4. A Sources list with titles and links.
                Cite every claim with its source. Never invent sources or numbers.
                """
            ),
            markdown=True,
        )
        with st.spinner("Searching Google, Reddit, and YouTube in real time..."):
            result = agent.run(query)
        st.markdown(result.content)
