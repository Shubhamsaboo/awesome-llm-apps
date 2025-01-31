import os
import streamlit as st
from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from agno.vectordb.pgvector import PgVector
from agno.embedder.google import GeminiEmbedder
import tempfile
import bs4

# Streamlit App Title
st.title("AI Agent with Agno and Gemini Thinking")

# Sidebar for API Key Input
st.sidebar.header("Configuration")
google_api_key = st.sidebar.text_input("Enter your Google API Key", type="password")
qdrant_api_key = st.sidebar.text_input("Enter your Qdrant API Key", type="password")
qdrant_url = st.sidebar.text_input("Enter your Qdrant URL", placeholder="https://your-qdrant-url.com")

if google_api_key:
    os.environ["GOOGLE_API_KEY"] = google_api_key

# Initialize Qdrant Client
def init_qdrant():
    if not qdrant_api_key or not qdrant_url:
        st.warning("Please provide Qdrant API Key and URL in the sidebar.")
        return None
    try:
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=60)
        client.get_collections()  # Test connection
        return client
    except Exception as e:
        st.error(f"Failed to initialize Qdrant: {e}")
        return None

qdrant_client = init_qdrant()

# File/URL Upload Section
st.sidebar.header("Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload a document", type=["txt", "pdf", "jpg", "png"])
web_url = st.sidebar.text_input("Enter a web URL")

# Document and Web URL Processing
def process_document(file):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file.getvalue())
            tmp_path = tmp_file.name

        loader = PyPDFLoader(tmp_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)

        os.unlink(tmp_path)
        return texts
    except Exception as e:
        st.error(f"Error processing document: {e}")
        return []

def process_web_url(url):
    try:
        loader = WebBaseLoader(
            web_paths=(url,),
            bs_kwargs=dict(
                parse_only=bs4.SoupStrainer(
                    class_=("post-content", "post-title", "post-header")
                )
            ),
        )
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)
        return texts
    except Exception as e:
        st.error(f"Error processing web URL: {e}")
        return []

# Create and Populate Qdrant Vector Store
COLLECTION_NAME = "agno_rag"

def create_vector_store(texts):
    if not qdrant_client:
        return None
    try:
        # Create collection if it doesn't exist
        try:
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
            )
            st.success(f"Created new collection: {COLLECTION_NAME}")
        except Exception as e:
            if "already exists" not in str(e).lower():
                raise e

        # Initialize QdrantVectorStore
        vector_store = QdrantVectorStore(
            client=qdrant_client,
            collection_name=COLLECTION_NAME,
            embedding=GeminiEmbedder(dimensions=1024)  # Add embedding model if needed
        )

        # Add documents to the vector store
        with st.spinner('Storing documents in Qdrant...'):
            vector_store.add_documents(texts)
            st.success("Documents successfully stored in Qdrant!")

        return vector_store
    except Exception as e:
        st.error(f"Error creating vector store: {e}")
        return None

# Process Uploaded File or Web URL
if uploaded_file:
    texts = process_document(uploaded_file)
    if texts:
        vector_store = create_vector_store(texts)
elif web_url:
    texts = process_web_url(web_url)
    if texts:
        vector_store = create_vector_store(texts)

# Initialize the Agent
if google_api_key and qdrant_client:
    thinking_agent = Agent(
        name="Thinking Agent",
        role="Think about the problem",
        model=Gemini(id="gemini-2.0-flash-exp", api_key=google_api_key),
        instructions="Given the problem, think about it and provide a detailed explanation",
        show_tool_calls=True,
        markdown=True,
    )

    
    # Display chat history if it exists
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
        
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
    # Chat input using Streamlit's chat_input for better UX
    user_input = st.chat_input("Ask a question or describe a problem you'd like me to think about...")

    if user_input:
        # Query the Qdrant vector store for relevant documents
        if 'vector_store' in locals():
            retriever = vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={"k": 5, "score_threshold": 0.7}
            )
            relevant_docs = retriever.get_relevant_documents(user_input)

            if relevant_docs:
                st.write("Relevant Documents:")
                for doc in relevant_docs:
                    st.write(doc.page_content[:200] + "...")

        # Process the user's input with the agent
        response = thinking_agent.run(user_input)
        st.write("Agent's Response:")
        st.write(response.content)
else:
    st.warning("Please enter your Google API Key and Qdrant credentials in the sidebar to proceed.")