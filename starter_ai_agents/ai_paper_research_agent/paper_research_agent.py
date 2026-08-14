import streamlit as st
from crw import CrwClient
from openai import OpenAI

st.set_page_config(page_title="AI Paper Research Agent", page_icon="📄")
st.title("📄 AI Paper Research Agent")
st.caption(
    "Search academic literature across arXiv, OpenAlex, Semantic Scholar and Crossref, "
    "then get a cited literature review written from the abstracts."
)

# API Keys (Runtime Input)
st.sidebar.header("API Keys")
openai_key = st.sidebar.text_input("OpenAI API Key", type="password")
crw_key = st.sidebar.text_input("CRW API Key", type="password")
st.sidebar.caption("Get a CRW key at fastcrw.com. Self-hosters can leave it blank and set CRW_API_URL instead.")

paper_count = st.sidebar.slider("Papers to review", min_value=3, max_value=15, value=8)

topic = st.text_input("Research topic:", placeholder="graph neural networks for drug discovery")


def find_papers(client: CrwClient, query: str, k: int) -> list[dict]:
    """Search the research index and backfill any abstract the search result omitted."""
    results = client.search_papers(query, k=k).get("results", [])
    papers = []
    for result in results:
        abstract = result.get("abstract")
        if not abstract:
            detail = client.get_paper(result["paperId"], query=query)
            abstract = detail.get("paper", {}).get("abstract")
        if abstract:
            papers.append({"title": result["title"], "abstract": abstract, "id": result["paperId"]})
    return papers


def write_review(client: OpenAI, query: str, papers: list[dict]) -> str:
    sources = "\n\n".join(
        f"[{i}] {p['title']} ({p['id']})\n{p['abstract']}" for i, p in enumerate(papers, 1)
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a research assistant. Write a literature review from the provided "
                    "abstracts only. Cite every claim with the bracketed source number it came "
                    "from. If the abstracts disagree, say so. Do not add outside knowledge."
                ),
            },
            {"role": "user", "content": f"Topic: {query}\n\nSources:\n{sources}"},
        ],
    )
    return response.choices[0].message.content


if st.button("Research", disabled=not (openai_key and topic.strip())):
    with st.spinner("Searching papers..."):
        try:
            crw = CrwClient(api_key=crw_key or None)
            papers = find_papers(crw, topic.strip(), paper_count)
        except Exception as e:
            st.error(f"Paper search failed: {e}")
            st.stop()

    if not papers:
        st.warning("No papers with abstracts found. Try a broader topic.")
        st.stop()

    st.success(f"Found {len(papers)} papers")
    with st.spinner("Writing the literature review..."):
        try:
            review = write_review(OpenAI(api_key=openai_key), topic.strip(), papers)
        except Exception as e:
            st.error(f"Review generation failed: {e}")
            st.stop()

    st.markdown(review)
    st.subheader("Sources")
    for i, paper in enumerate(papers, 1):
        arxiv_id = paper["id"].removeprefix("arxiv:")
        link = f"https://arxiv.org/abs/{arxiv_id}" if paper["id"].startswith("arxiv:") else None
        st.markdown(f"[{i}] [{paper['title']}]({link})" if link else f"[{i}] {paper['title']}")
