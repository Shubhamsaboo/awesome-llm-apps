import os
import tempfile
from datetime import datetime
from typing import List
import streamlit as st
import bs4
from agno.agent import Agent
from agno.models.ollama import Ollama
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_core.embeddings import Embeddings
from agno.tools.exa import ExaTools
from agno.embedder.ollama import OllamaEmbedder


class OllamaEmbedderr(Embeddings):
    def __init__(self, model_name="snowflake-arctic-embed"):
        """
        Initialize the OllamaEmbedderr with a specific model.

        Args:
            model_name (str): The name of the model to use for embedding.
        """
        self.embedder = OllamaEmbedder(id=model_name, dimensions=1024)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self.embedder.get_embedding(text)


# Constants
COLLECTION_NAME = "test-qwen-r1"


# Streamlit App Initialization
st.title("🐋 Qwen 3 Local RAG Reasoning Agent")

# --- Add Model Info Boxes --- 
st.info("**Qwen3:** The latest generation of large language models in Qwen series, offering a comprehensive suite of dense and mixture-of-experts (MoE) models.")
st.info("**Gemma 3:** These models are multimodal—processing text and images—and feature a 128K context window with support for over 140 languages.")
# -------------------------

# Session State Initialization
if 'model_version' not in st.session_state:
    st.session_state.model_version = "qwen3:1.7b"  # Default to lighter model
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = None
if 'processed_documents' not in st.session_state:
    st.session_state.processed_documents = []
if 'history' not in st.session_state:
    st.session_state.history = []
if 'exa_api_key' not in st.session_state:
    st.session_state.exa_api_key = ""
if 'use_web_search' not in st.session_state:
    st.session_state.use_web_search = False
if 'force_web_search' not in st.session_state:
    st.session_state.force_web_search = False
if 'similarity_threshold' not in st.session_state:
    st.session_state.similarity_threshold = 0.7
if 'rag_enabled' not in st.session_state:
    st.session_state.rag_enabled = True  # RAG is enabled by default


# Sidebar Configuration
st.sidebar.header("⚙️ Settings")

# Model Selection
st.sidebar.header("🧠 Model Choice")
model_help = """
- qwen3:1.7b: Lighter model (MoE)
- gemma3:1b: More capable but requires better GPU/RAM(32k context window)
- gemma3:4b: More capable and MultiModal (Vision)(128k context window)
- deepseek-r1:1.5b
- qwen3:8b: More capable but requires better GPU/RAM

Choose based on your hardware capabilities.
"""
st.session_state.model_version = st.sidebar.radio(
    "Select Model Version",
    options=["qwen3:1.7b", "gemma3:1b", "gemma3:4b", "deepseek-r1:1.5b", "qwen3:8b"],
    help=model_help
)

st.sidebar.info("Run ollama pull qwen3:1.7b")

# RAG Mode Toggle
st.sidebar.header("📚 RAG Mode")
st.session_state.rag_enabled = st.sidebar.toggle("Enable RAG", value=st.session_state.rag_enabled)

# Clear Chat Button
if st.sidebar.button("✨ Clear Chat"):
    st.session_state.history = []
    st.rerun()

# Show API Configuration only if RAG is enabled
if st.session_state.rag_enabled:
    st.sidebar.header("🔬 Search Tuning")
    st.session_state.similarity_threshold = st.sidebar.slider(
        "Similarity Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        help="Lower values will return more documents but might be less relevant. Higher values are more strict."
    )

# Add in the sidebar configuration section, after the existing API inputs

st.sidebar.header("🌍 Web Search")
st.session_state.use_web_search = st.sidebar.checkbox("Enable Web Search Fallback", value=st.session_state.use_web_search)

if st.session_state.use_web_search:
    exa_api_key = st.sidebar.text_input(
        "Exa AI API Key", 
        type="password",
        value=st.session_state.exa_api_key,
        help="Required for web search fallback when no relevant documents are found"
    )
    st.session_state.exa_api_key = exa_api_key
    
    # Optional domain filtering
    default_domains = ["arxiv.org", "wikipedia.org", "github.com", "medium.com"]
    custom_domains = st.sidebar.text_input(
        "Custom domains (comma-separated)", 
        value=",".join(default_domains),
        help="Enter domains to search from, e.g.: arxiv.org,wikipedia.org"
    )
    search_domains = [d.strip() for d in custom_domains.split(",") if d.strip()]

# Utility Functions
def init_qdrant() -> QdrantClient | None:
    """Initialize Qdrant client with local Docker setup.

    Returns:
        QdrantClient: The initialized Qdrant client if successful.
        None: If the initialization fails.
    """
    try:
        return QdrantClient(url="http://localhost:6333")
    except Exception as e:
        st.error(f"🔴 Qdrant connection failed: {str(e)}")
        return None


# Document Processing Functions
def process_pdf(file) -> List:
    """Process PDF file and add source metadata."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file.getvalue())
            loader = PyPDFLoader(tmp_file.name)
            documents = loader.load()
            
            # Add source metadata
            for doc in documents:
                doc.metadata.update({
                    "source_type": "pdf",
                    "file_name": file.name,
                    "timestamp": datetime.now().isoformat()
                })
                
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            return text_splitter.split_documents(documents)
    except Exception as e:
        st.error(f"📄 PDF processing error: {str(e)}")
        return []


def process_web(url: str) -> List:
    """Process web URL and add source metadata."""
    try:
        loader = WebBaseLoader(
            web_paths=(url,),
            bs_kwargs=dict(
                parse_only=bs4.SoupStrainer(
                    class_=("post-content", "post-title", "post-header", "content", "main")
                )
            )
        )
        documents = loader.load()
        
        # Add source metadata
        for doc in documents:
            doc.metadata.update({
                "source_type": "url",
                "url": url,
                "timestamp": datetime.now().isoformat()
            })
            
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        return text_splitter.split_documents(documents)
    except Exception as e:
        st.error(f"🌐 Web processing error: {str(e)}")
        return []


# Vector Store Management
def create_vector_store(client, texts):
    """Create and initialize vector store with documents."""
    try:
        # Create collection if needed
        try:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=1024,  
                    distance=Distance.COSINE
                )
            )
            st.success(f"📚 Created new collection: {COLLECTION_NAME}")
        except Exception as e:
            if "already exists" not in str(e).lower():
                raise e
        
        # Initialize vector store
        vector_store = QdrantVectorStore(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding=OllamaEmbedderr()
        )
        
        # Add documents
        with st.spinner('📤 Uploading documents to Qdrant...'):
            vector_store.add_documents(texts)
            st.success("✅ Documents stored successfully!")
            return vector_store
            
    except Exception as e:
        st.error(f"🔴 Vector store error: {str(e)}")
        return None

def get_web_search_agent() -> Agent:
    """Initialize a web search agent."""
    return Agent(
        name="Web Search Agent",
        model=Ollama(id="llama3.2"),
        tools=[ExaTools(
            api_key=st.session_state.exa_api_key,
            include_domains=search_domains,
            num_results=5
        )],
        instructions="""You are a web search expert. Your task is to:
        1. Search the web for relevant information about the query
        2. Compile and summarize the most relevant information
        3. Include sources in your response
        """,
        show_tool_calls=True,
        markdown=True,
    )


def get_rag_agent() -> Agent:
    """Initialize the main RAG agent."""
    return Agent(
        name="Qwen 3 RAG Agent",
        model=Ollama(id=st.session_state.model_version),
        instructions="""You are an Intelligent Agent specializing in providing accurate answers.

        When asked a question:
        - Analyze the question and answer the question with what you know.
        
        When given context from documents:
        - Focus on information from the provided documents
        - Be precise and cite specific details
        
        When given web search results:
        - Clearly indicate that the information comes from web search
        - Synthesize the information clearly
        
        Always maintain high accuracy and clarity in your responses.
        """,
        show_tool_calls=True,
        markdown=True,
    )




def check_document_relevance(query: str, vector_store, threshold: float = 0.7) -> tuple[bool, List]:

    if not vector_store:
        return False, []
        
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 5, "score_threshold": threshold}
    )
    docs = retriever.invoke(query)
    return bool(docs), docs


chat_col, toggle_col = st.columns([0.9, 0.1])

with chat_col:
    prompt = st.chat_input("Ask about your documents..." if st.session_state.rag_enabled else "Ask me anything...")

with toggle_col:
    st.session_state.force_web_search = st.toggle('🌐', help="Force web search")

# Check if RAG is enabled 
if st.session_state.rag_enabled:
    qdrant_client = init_qdrant()
    
    # --- Document Upload Section (Moved to Main Area) ---
    with st.expander("📁 Upload Documents or URLs for RAG", expanded=False):
        if not qdrant_client:
            st.warning("⚠️ Please configure Qdrant API Key and URL in the sidebar to enable document processing.")
        else:
            uploaded_files = st.file_uploader(
                "Upload PDF files", 
                accept_multiple_files=True, 
                type='pdf'
            )
            url_input = st.text_input("Enter URL to scrape")

            if uploaded_files:
                st.write(f"Processing {len(uploaded_files)} PDF file(s)...")
                all_texts = []
                for file in uploaded_files:
                    if file.name not in st.session_state.processed_documents:
                        with st.spinner(f"Processing {file.name}... "): 
                            texts = process_pdf(file)
                            if texts: 
                                all_texts.extend(texts)
                                st.session_state.processed_documents.append(file.name)
                    else:
                        st.write(f"📄 {file.name} already processed.")
                
                if all_texts:
                    with st.spinner("Creating vector store..."):
                        st.session_state.vector_store = create_vector_store(qdrant_client, all_texts)

            if url_input:
                if url_input not in st.session_state.processed_documents:
                    with st.spinner(f"Scraping and processing {url_input}..."):
                        texts = process_web(url_input)
                        if texts:
                            st.session_state.vector_store = create_vector_store(qdrant_client, texts)
                            st.session_state.processed_documents.append(url_input)
                else:
                    st.write(f"🔗 {url_input} already processed.")
                    
            if st.session_state.vector_store:
                st.success("Vector store is ready.")
            elif not uploaded_files and not url_input:
                 st.info("Upload PDFs or enter a URL to populate the vector store.")

    # Display sources in sidebar
    if st.session_state.processed_documents:
        st.sidebar.header("📚 Processed Sources")
        for source in st.session_state.processed_documents:
            if source.endswith('.pdf'):
                st.sidebar.text(f"📄 {source}")
            else:
                st.sidebar.text(f"🌐 {source}")

if prompt:
    # Add user message to history
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    if st.session_state.rag_enabled:

            # Existing RAG flow remains unchanged
            with st.spinner("🤔Evaluating the Query..."):
                try:
                    rewritten_query = prompt
                    
                    with st.expander("Evaluating the query"):
                        st.write(f"User's Prompt: {prompt}")
                except Exception as e:
                    st.error(f"❌ Error rewriting query: {str(e)}")
                    rewritten_query = prompt

            # Step 2: Choose search strategy based on force_web_search toggle
            context = ""
            docs = []
            if not st.session_state.force_web_search and st.session_state.vector_store:
                # Try document search first
                retriever = st.session_state.vector_store.as_retriever(
                    search_type="similarity_score_threshold",
                    search_kwargs={
                        "k": 5, 
                        "score_threshold": st.session_state.similarity_threshold
                    }
                )
                docs = retriever.invoke(rewritten_query)
                if docs:
                    context = "\n\n".join([d.page_content for d in docs])
                    st.info(f"📊 Found {len(docs)} relevant documents (similarity > {st.session_state.similarity_threshold})")
                elif st.session_state.use_web_search:
                    st.info("🔄 No relevant documents found in database, falling back to web search...")

            # Step 3: Use web search if:
            # 1. Web search is forced ON via toggle, or
            # 2. No relevant documents found AND web search is enabled in settings
            if (st.session_state.force_web_search or not context) and st.session_state.use_web_search and st.session_state.exa_api_key:
                with st.spinner("🔍 Searching the web..."):
                    try:
                        web_search_agent = get_web_search_agent()
                        web_results = web_search_agent.run(rewritten_query).content
                        if web_results:
                            context = f"Web Search Results:\n{web_results}"
                            if st.session_state.force_web_search:
                                st.info("ℹ️ Using web search as requested via toggle.")
                            else:
                                st.info("ℹ️ Using web search as fallback since no relevant documents were found.")
                    except Exception as e:
                        st.error(f"❌ Web search error: {str(e)}")

            # Step 4: Generate response using the RAG agent
            with st.spinner("🤖 Thinking..."):
                try:
                    rag_agent = get_rag_agent()
                    
                    if context:
                        full_prompt = f"""Context: {context}

Original Question: {prompt}
Please provide a comprehensive answer based on the available information."""
                    else:
                        full_prompt = f"Original Question: {prompt}\n"
                        st.info("ℹ️ No relevant information found in documents or web search.")

                    response = rag_agent.run(full_prompt)
                    
                    # Add assistant response to history
                    st.session_state.history.append({
                        "role": "assistant",
                        "content": response.content
                    })
                    
                    # Display assistant response
                    with st.chat_message("assistant"):
                        st.write(response.content)
                        
                        # Show sources if available
                        if not st.session_state.force_web_search and 'docs' in locals() and docs:
                            with st.expander("🔍 See document sources"):
                                for i, doc in enumerate(docs, 1):
                                    source_type = doc.metadata.get("source_type", "unknown")
                                    source_icon = "📄" if source_type == "pdf" else "🌐"
                                    source_name = doc.metadata.get("file_name" if source_type == "pdf" else "url", "unknown")
                                    st.write(f"{source_icon} Source {i} from {source_name}:")
                                    st.write(f"{doc.page_content[:200]}...")

                except Exception as e:
                    st.error(f"❌ Error generating response: {str(e)}")

    else:
        # Simple mode without RAG
        with st.spinner("🤖 Thinking..."):
            try:
                rag_agent = get_rag_agent()
                web_search_agent = get_web_search_agent() if st.session_state.use_web_search else None
                
                # Handle web search if forced or enabled
                context = ""
                if st.session_state.force_web_search and web_search_agent:
                    with st.spinner("🔍 Searching the web..."):
                        try:
                            web_results = web_search_agent.run(prompt).content
                            if web_results:
                                context = f"Web Search Results:\n{web_results}"
                                st.info("ℹ️ Using web search as requested.")
                        except Exception as e:
                            st.error(f"❌ Web search error: {str(e)}")
                
                # Generate response
                if context:
                    full_prompt = f"""Context: {context}

Question: {prompt}

Please provide a comprehensive answer based on the available information."""
                else:
                    full_prompt = prompt

                response = rag_agent.run(full_prompt)
                response_content = response.content
                
                # Extract thinking process and final response
                import re
                think_pattern = r'<think>(.*?)</think>'
                think_match = re.search(think_pattern, response_content, re.DOTALL)
                
                if think_match:
                    thinking_process = think_match.group(1).strip()
                    final_response = re.sub(think_pattern, '', response_content, flags=re.DOTALL).strip()
                else:
                    thinking_process = None
                    final_response = response_content
                
                # Add assistant response to history (only the final response)
                st.session_state.history.append({
                    "role": "assistant",
                    "content": final_response
                })
                
                # Display assistant response
                with st.chat_message("assistant"):
                    if thinking_process:
                        with st.expander("🤔 See thinking process"):
                            st.markdown(thinking_process)
                    st.markdown(final_response)

            except Exception as e:
                st.error(f"❌ Error generating response: {str(e)}")

else:
    st.warning("You can directly talk to qwen and gemma models locally! Toggle the RAG mode to upload documents!")