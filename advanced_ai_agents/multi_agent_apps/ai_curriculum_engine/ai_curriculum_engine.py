"""
Plot Ark — AI Curriculum Engine
A multi-agent pipeline that generates pedagogically grounded course modules
using Bloom's Taxonomy, Tavily research, and LightRAG knowledge graphs.
"""

import os
import json
import asyncio
import tempfile
import streamlit as st
from openai import OpenAI
from tavily import TavilyClient
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
from lightrag.utils import EmbeddingFunc
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Bloom's Taxonomy constraints by learner level
# ---------------------------------------------------------------------------
BLOOMS_CONSTRAINTS = {
    "beginner": (
        "Focus on Remember and Understand (Bloom's levels 1-2). "
        "Objectives use verbs: define, identify, describe, explain, summarize. "
        "Avoid analysis or evaluation tasks."
    ),
    "intermediate": (
        "Focus on Apply and Analyze (Bloom's levels 3-4). "
        "Objectives use verbs: apply, demonstrate, differentiate, compare, examine. "
        "Include at least one application or case study per module."
    ),
    "advanced": (
        "Focus on Evaluate and Create (Bloom's levels 5-6). "
        "Objectives use verbs: evaluate, critique, design, construct, synthesize. "
        "Modules should require original thinking and complex problem-solving."
    ),
}

RESOURCE_TYPES = {
    "academic": {
        "domains": ["jstor.org", "researchgate.net", "springer.com", "wiley.com",
                    "scholar.google.com", "cambridge.org", "sciencedirect.com"],
        "query": "{topic} academic research {level} {audience}",
        "max_results": 4,
    },
    "video": {
        "domains": ["youtube.com", "ted.com", "coursera.org", "edx.org", "khanacademy.org"],
        "query": "{topic} lecture video course {level}",
        "max_results": 3,
    },
    "news": {
        "domains": ["hbr.org", "economist.com", "mit.edu", "stanford.edu", "theguardian.com"],
        "query": "{topic} analysis report",
        "max_results": 2,
    },
}


# ---------------------------------------------------------------------------
# Agent 1: Research — finds real sources via Tavily
# ---------------------------------------------------------------------------
def research_sources(topic: str, level: str, audience: str, tavily_key: str) -> list:
    client = TavilyClient(api_key=tavily_key)
    results = []
    for source_type, config in RESOURCE_TYPES.items():
        query = config["query"].format(topic=topic, level=level, audience=audience)
        try:
            resp = client.search(
                query=query,
                search_depth="basic",
                max_results=config["max_results"],
                include_domains=config["domains"],
            )
            for r in resp.get("results", []):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", "")[:400],
                    "type": source_type,
                })
        except Exception as e:
            st.warning(f"Source search error ({source_type}): {e}")

    # Deduplicate by URL
    seen, unique = set(), []
    for r in results:
        if r["url"] not in seen and r["title"]:
            seen.add(r["url"])
            unique.append(r)
    return unique[:12]


# ---------------------------------------------------------------------------
# Agent 2: Knowledge Graph — builds per-course LightRAG graph from sources
# ---------------------------------------------------------------------------
def build_knowledge_graph(topic: str, sources: list, openai_key: str) -> LightRAG:
    storage_dir = tempfile.mkdtemp(prefix=f"plotark_{topic[:20].replace(' ', '_')}_")

    async def _init():
        rag = LightRAG(
            working_dir=storage_dir,
            llm_model_func=gpt_4o_mini_complete,
            embedding_func=EmbeddingFunc(
                embedding_dim=1536,
                max_token_size=8192,
                func=lambda texts: openai_embed(
                    texts,
                    model="text-embedding-3-small",
                    api_key=openai_key,
                ),
            ),
        )
        await rag.initialize_storages()

        # Insert source content into graph
        corpus = "\n\n".join(
            f"[{s['type'].upper()}] {s['title']}\n{s['content']}"
            for s in sources
            if s.get("content")
        )
        if corpus.strip():
            await rag.ainsert(corpus)
        return rag

    loop = asyncio.new_event_loop()
    rag = loop.run_until_complete(_init())
    loop.close()
    return rag


def query_knowledge_graph(rag: LightRAG, query: str) -> str:
    async def _query():
        return await rag.aquery(query, param=QueryParam(mode="hybrid"))
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(_query())
    loop.close()
    return result or ""


# ---------------------------------------------------------------------------
# Agent 3: Curriculum Generation — produces structured modules via OpenAI
# ---------------------------------------------------------------------------
def generate_curriculum(
    topic: str,
    level: str,
    audience: str,
    module_count: int,
    sources: list,
    rag_context: str,
    openai_key: str,
) -> dict:
    client = OpenAI(api_key=openai_key)
    blooms = BLOOMS_CONSTRAINTS.get(level.lower(), BLOOMS_CONSTRAINTS["intermediate"])

    sources_text = "\n".join(
        f"- [{s['type']}] {s['title']} ({s['url']})"
        for s in sources[:8]
    )

    system_prompt = (
        "You are an expert instructional designer. Generate a complete course curriculum "
        "using ADDIE methodology and Bloom's Taxonomy. Return only valid JSON."
    )

    user_prompt = f"""Design a {module_count}-module course on "{topic}" for {audience} ({level} level).

Bloom's Taxonomy Constraint:
{blooms}

Knowledge Graph Context (key concepts and relationships):
{rag_context[:1500] if rag_context else "N/A"}

Available Sources:
{sources_text}

Return this exact JSON structure:
{{
  "course_title": "string",
  "course_description": "2-3 sentence overview",
  "learning_outcomes": ["outcome 1", "outcome 2", "outcome 3"],
  "modules": [
    {{
      "module_number": 1,
      "title": "string",
      "narrative": "2-3 sentence pedagogical rationale",
      "objectives": ["verb + content (Bloom-aligned)", "..."],
      "key_concepts": ["concept1", "concept2", "concept3"],
      "resources": [
        {{"title": "from provided sources or suggested", "url": "url or null", "type": "academic|video|news"}}
      ],
      "assessment": {{
        "type": "quiz|project|essay|discussion",
        "description": "1-2 sentence description"
      }},
      "complexity": 1-5
    }}
  ]
}}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Plot Ark — AI Curriculum Engine", page_icon="📚", layout="wide")

    st.title("📚 Plot Ark — AI Curriculum Engine")
    st.markdown(
        "A multi-agent pipeline: **Tavily** researches real sources → "
        "**LightRAG** builds a knowledge graph → **GPT-4o-mini** generates "
        "Bloom's Taxonomy-aligned course modules."
    )

    # API Keys
    with st.sidebar:
        st.header("🔑 API Keys")
        openai_key = st.text_input("OpenAI API Key", type="password",
                                   value=os.getenv("OPENAI_API_KEY", ""))
        tavily_key = st.text_input("Tavily API Key", type="password",
                                   value=os.getenv("TAVILY_API_KEY", ""))
        st.markdown("---")
        st.markdown("**[Plot Ark GitHub](https://github.com/Schlaflied/Plot-Ark)**")

    # Course parameters
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("Course Topic", placeholder="e.g. Introduction to Machine Learning Ethics")
        audience = st.text_input("Target Audience", placeholder="e.g. undergraduate computer science students")
    with col2:
        level = st.selectbox("Learner Level", ["Beginner", "Intermediate", "Advanced"])
        module_count = st.slider("Number of Modules", min_value=3, max_value=10, value=5)

    if st.button("🚀 Generate Curriculum", type="primary", disabled=not (topic and openai_key and tavily_key)):

        if not topic or not openai_key or not tavily_key:
            st.error("Please fill in the course topic and both API keys.")
            return

        # Agent 1: Research
        with st.status("🔍 Agent 1: Researching sources via Tavily...", expanded=True) as status:
            sources = research_sources(topic, level.lower(), audience, tavily_key)
            status.update(label=f"✅ Found {len(sources)} sources", state="complete")

        # Agent 2: Knowledge Graph
        with st.status("🕸️ Agent 2: Building LightRAG knowledge graph...", expanded=True) as status:
            try:
                rag = build_knowledge_graph(topic, sources, openai_key)
                rag_context = query_knowledge_graph(rag, f"key concepts and relationships in {topic}")
                status.update(label="✅ Knowledge graph built", state="complete")
            except Exception as e:
                st.warning(f"LightRAG unavailable, continuing without graph: {e}")
                rag_context = ""

        # Agent 3: Curriculum Generation
        with st.status("✍️ Agent 3: Generating curriculum with GPT-4o-mini...", expanded=True) as status:
            curriculum = generate_curriculum(
                topic, level.lower(), audience, module_count,
                sources, rag_context, openai_key
            )
            status.update(label="✅ Curriculum generated", state="complete")

        # Display results
        st.markdown("---")
        st.header(curriculum.get("course_title", topic))
        st.markdown(curriculum.get("course_description", ""))

        outcomes = curriculum.get("learning_outcomes", [])
        if outcomes:
            with st.expander("🎯 Course Learning Outcomes", expanded=True):
                for o in outcomes:
                    st.markdown(f"- {o}")

        # Module cards
        modules = curriculum.get("modules", [])
        st.subheader(f"📖 {len(modules)} Modules")

        for mod in modules:
            complexity = mod.get("complexity", 3)
            complexity_bar = "█" * complexity + "░" * (5 - complexity)
            with st.expander(f"Module {mod['module_number']}: {mod['title']}  [{complexity_bar}]"):
                st.markdown(f"*{mod.get('narrative', '')}*")

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**Learning Objectives**")
                    for obj in mod.get("objectives", []):
                        st.markdown(f"- {obj}")
                    st.markdown("**Key Concepts**")
                    st.markdown(" · ".join(mod.get("key_concepts", [])))

                with col_b:
                    st.markdown("**Resources**")
                    for r in mod.get("resources", []):
                        url = r.get("url")
                        title = r.get("title", "Resource")
                        badge = {"academic": "🎓", "video": "🎬", "news": "📰"}.get(r.get("type", ""), "📎")
                        if url:
                            st.markdown(f"{badge} [{title}]({url})")
                        else:
                            st.markdown(f"{badge} {title}")

                    assessment = mod.get("assessment", {})
                    if assessment:
                        st.markdown("**Assessment**")
                        st.markdown(f"`{assessment.get('type', '').upper()}` — {assessment.get('description', '')}")

        # Sources panel
        if sources:
            with st.expander(f"📚 {len(sources)} Research Sources"):
                for s in sources:
                    badge = {"academic": "🎓", "video": "🎬", "news": "📰"}.get(s["type"], "📎")
                    st.markdown(f"{badge} [{s['title']}]({s['url']})")

        # Download JSON
        st.download_button(
            "⬇️ Download Curriculum JSON",
            data=json.dumps(curriculum, indent=2),
            file_name=f"curriculum_{topic[:30].replace(' ', '_')}.json",
            mime="application/json",
        )


if __name__ == "__main__":
    main()
