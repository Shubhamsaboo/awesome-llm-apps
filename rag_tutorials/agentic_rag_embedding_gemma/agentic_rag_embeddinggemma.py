import streamlit as st
from agno.agent import Agent
from agno.knowledge.embedder.ollama import OllamaEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.models.ollama import Ollama
from agno.vectordb.lancedb import LanceDb, SearchType

# Page configuration
st.set_page_config(
    page_title="Agentic RAG with Google's EmbeddingGemma",
    page_icon="🔥",
    layout="wide"
)

@st.cache_resource
def load_knowledge_base():
    knowledge_base = Knowledge(
        vector_db=LanceDb(
            table_name="recipes",
            uri="tmp/lancedb",
            search_type=SearchType.vector,
            embedder=OllamaEmbedder(id="embeddinggemma:latest", dimensions=768),
        ),
    )
    return knowledge_base

# Initialize URLs in session state
if 'urls' not in st.session_state:
    st.session_state.urls = []
if 'urls_loaded' not in st.session_state:
    st.session_state.urls_loaded = set()

kb = load_knowledge_base()

# Load initial URLs if any (only load once per URL)
for url in st.session_state.urls:
    if url not in st.session_state.urls_loaded:
        kb.add_content(url=url)
        st.session_state.urls_loaded.add(url)

agent = Agent(
    model=Ollama(id="llama3.2:latest"),
    knowledge=kb,
    instructions=[
        "Search the knowledge base for relevant information and base your answers on it.",
        "Be clear, and generate well-structured answers.",
        "Use clear headings, bullet points, or numbered lists where appropriate.",
    ],
    search_knowledge=True,
    debug_mode=False,
    markdown=True,
)

# Sidebar for adding knowledge sources
with st.sidebar:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.image("google.png")
    with col2:
        st.image("ollama.png")
    with col3:
        st.image("agno.png")
    st.header("🌐 Add Knowledge Sources")
    new_url = st.text_input(
        "Add URL",
        placeholder="https://example.com/sample.pdf",
        help="Enter a PDF URL to add to the knowledge base",
    )
    if st.button("➕ Add URL", type="primary"):
        if new_url:
            if new_url not in st.session_state.urls:
                st.session_state.urls.append(new_url)
                with st.spinner("📥 Adding new URL..."):
                    kb.add_content(url=new_url)
                    st.session_state.urls_loaded.add(new_url)
                st.success(f"✅ Added: {new_url}")
                st.rerun()
            else:
                st.warning("This URL has already been added.")
        else:
            st.error("Please enter a URL")

    # Display current URLs
    if st.session_state.urls:
        st.subheader("📚 Current Knowledge Sources")
        for i, url in enumerate(st.session_state.urls, 1):
            st.markdown(f"{i}. {url}")

# Main title and description
st.title("🔥 Agentic RAG with EmbeddingGemma (100% local)")
st.markdown(
    """
This app demonstrates an agentic RAG system using local models via [Ollama](https://ollama.com/):

- **EmbeddingGemma** for creating vector embeddings
- **LanceDB** as the local vector database

Add PDF URLs in the sidebar to start and ask questions about the content.
    """
)
                
query = st.text_input("Enter your question:")

# Simple answer generation
if st.button("🚀 Get Answer", type="primary"):
    if not query:
        st.error("Please enter a question")
    else:
        st.markdown("### 💡 Answer")
        
        with st.spinner("🔍 Searching knowledge and generating answer..."):
            try:
                response = ""
                resp_container = st.empty()
                gen = agent.run(query, stream=True)
                for resp_chunk in gen:
                    # Display response
                    if resp_chunk.content is not None:
                        response += resp_chunk.content
                        resp_container.markdown(response)
            except Exception as e:
                st.error(f"Error: {e}")

with st.expander("📖 How This Works"):
    st.markdown(
        """
**This app uses the Agno framework to create an intelligent Q&A system:**

1. **Knowledge Loading**: PDF URLs are processed and stored in LanceDB vector database
2. **EmbeddingGemma as Embedder**: EmbeddingGemma generates local embeddings for semantic search
3. **Llama 3.2**: The Llama 3.2 model generates answers based on retrieved context

**Key Components:**
- `EmbeddingGemma` as the embedder
- `LanceDB` as the vector database
- `Knowledge`: Manages document loading from PDF URLs
- `OllamaEmbedder`: Uses EmbeddingGemma for embeddings
- `Agno Agent`: Orchestrates everything to answer questions
        """
    )
