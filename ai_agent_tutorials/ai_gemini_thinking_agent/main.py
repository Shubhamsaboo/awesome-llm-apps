import os
import streamlit as st
import google.generativeai as genai
import tempfile
import bs4
from typing import List
from agno.agent import Agent
from agno.models.google import Gemini
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_core.embeddings import Embeddings


# Custom Gemini Embedder Class
class GeminiEmbedder(Embeddings):
    def __init__(self, model_name="models/embedding-004"):
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        self.model = model_name

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        response = genai.embed_content(
            model=self.model,
            content=text,
            task_type="retrieval_document"
        )
        return response['embedding']

# Initialize Streamlit App
st.title("🤖 AI Agent with Gemini & Qdrant RAG")

# Sidebar Configuration
st.sidebar.header("🔑 API Configuration")
google_api_key = st.sidebar.text_input("Google API Key", type="password")
qdrant_api_key = st.sidebar.text_input("Qdrant API Key", type="password")
qdrant_url = st.sidebar.text_input("Qdrant URL", 
                                 placeholder="https://your-cluster.cloud.qdrant.io:6333")

# Initialize Qdrant Client
def init_qdrant():
    if not all([qdrant_api_key, qdrant_url]):
        return None
    try:
        return QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
            timeout=60
        )
    except Exception as e:
        st.error(f"🔴 Qdrant connection failed: {str(e)}")
        return None

# Document Processing Functions
def process_pdf(file):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file.getvalue())
            loader = PyPDFLoader(tmp_file.name)
            documents = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            return text_splitter.split_documents(documents)
    except Exception as e:
        st.error(f"📄 PDF processing error: {str(e)}")
        return []

def process_web(url):
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
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        return text_splitter.split_documents(documents)
    except Exception as e:
        st.error(f"🌐 Web processing error: {str(e)}")
        return []

# Vector Store Management
COLLECTION_NAME = "agno_rag"

def create_vector_store(client, texts):
    try:
        # Create collection if needed
        try:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=768,  # Gemini embedding-004 dimension
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
            embedding=GeminiEmbedder()
        )
        
        # Add documents
        with st.spinner('📤 Uploading documents to Qdrant...'):
            vector_store.add_documents(texts)
            st.success("✅ Documents stored successfully!")
            return vector_store
            
    except Exception as e:
        st.error(f"🔴 Vector store error: {str(e)}")
        return None

# Main Application Flow
if google_api_key:
    os.environ["GOOGLE_API_KEY"] = google_api_key
    genai.configure(api_key=google_api_key)
    
    qdrant_client = init_qdrant()
    
    # File/URL Upload Section
    st.sidebar.header("📁 Data Upload")
    uploaded_file = st.sidebar.file_uploader("Upload PDF", type=["pdf"])
    web_url = st.sidebar.text_input("Or enter URL")
    
    # Process documents
    vector_store = None
    if uploaded_file:
        texts = process_pdf(uploaded_file)
        if texts and qdrant_client:
            vector_store = create_vector_store(qdrant_client, texts)
    elif web_url:
        texts = process_web(web_url)
        if texts and qdrant_client:
            vector_store = create_vector_store(qdrant_client, texts)

    # Initialize Agent
    agent = Agent(
        name="Gemini RAG Agent",
        model=Gemini(id="gemini-2.0-flash-exp"),
        instructions="You are AGI. You are elite speicialist in all fields and an expert in all fields. Answer user's questions clearly, if any document is added, Use retrieved documents to answer questions accurately",
        show_tool_calls=True,
        markdown=True,
    )

    # Initialize chat history
    if 'history' not in st.session_state:
        st.session_state.history = []
        
    # Display chat messages
    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # User input
    if prompt := st.chat_input("Ask about your documents..."):
        # Add user message to history
        st.session_state.history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        # Retrieve relevant documents
        context = ""
        if vector_store:
            retriever = vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={"k": 5, "score_threshold": 0.7}
            )
            docs = retriever.invoke(prompt)
            context = "\n\n".join([d.page_content for d in docs])
        
        # Generate response
        with st.spinner("🤖 Thinking..."):
            try:
                full_prompt = f"Context: {context}\n\nQuestion: {prompt}"
                response = agent.run(full_prompt)
                
                # Add assistant response to history
                st.session_state.history.append({
                    "role": "assistant",
                    "content": response.content
                })
                
                with st.chat_message("assistant"):
                    st.write(response.content)
                    
                    if vector_store and docs:
                        with st.expander("🔍 See sources"):
                            for i, doc in enumerate(docs, 1):
                                st.write(f"Source {i}: {doc.page_content[:200]}...")
                                
            except Exception as e:
                st.error(f"❌ Error generating response: {str(e)}")

else:
    st.warning("⚠️ Please enter your Google API Key to continue")