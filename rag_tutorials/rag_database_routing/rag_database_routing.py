import os
import getpass
from typing import List, Dict, Any, Literal
from dataclasses import dataclass
import streamlit as st
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import tempfile
from langchain_core.runnables import RunnableSequence
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma

def init_session_state():
    """Initialize session state variables"""
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = ""
    if 'embeddings' not in st.session_state:
        st.session_state.embeddings = None
    if 'llm' not in st.session_state:
        st.session_state.llm = None
    if 'databases' not in st.session_state:
        st.session_state.databases = {}

# Initialize session state at the top
init_session_state()

# Constants
DatabaseType = Literal["products", "customer_support", "financials"]
PERSIST_DIRECTORY = "db_storage"

ROUTER_TEMPLATE = """You are a query routing expert. Your job is to analyze user questions and determine which databases might contain relevant information.

Available databases:
1. Product Information: Contains product details, specifications, and features
2. Customer Support & FAQ: Contains customer support information, frequently asked questions, and guides
3. Financial Information: Contains financial data, revenue, costs, and liabilities

User question: {question}

Return a comma-separated list of relevant databases (no spaces after commas). Only use these exact strings:
- products
- customer_support
- financials

For example: "products,customer_support" if the question relates to both product info and support.
Your response:"""

@dataclass
class CollectionConfig:
    name: str
    description: str
    collection_name: str
    persist_directory: str

# Collection configurations
COLLECTIONS: Dict[DatabaseType, CollectionConfig] = {
    "products": CollectionConfig(
        name="Product Information",
        description="Product details, specifications, and features",
        collection_name="products_collection",
        persist_directory=f"{PERSIST_DIRECTORY}/products"
    ),
    "customer_support": CollectionConfig(
        name="Customer Support & FAQ",
        description="Customer support information, frequently asked questions, and guides",
        collection_name="support_collection",
        persist_directory=f"{PERSIST_DIRECTORY}/support"
    ),
    "financials": CollectionConfig(
        name="Financial Information",
        description="Financial data, revenue, costs, and liabilities",
        collection_name="finance_collection",
        persist_directory=f"{PERSIST_DIRECTORY}/finance"
    )
}

def initialize_models():
    """Initialize OpenAI models with API key"""
    if st.session_state.openai_api_key:
        try:
            os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key
            # Test the API key with a small embedding request
            test_embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
            test_embeddings.embed_query("test")
            
            # If successful, initialize the models
            st.session_state.embeddings = test_embeddings
            st.session_state.llm = ChatOpenAI(temperature=0)
            st.session_state.databases = {
                "products": Chroma(
                    collection_name=COLLECTIONS["products"].collection_name,
                    embedding_function=st.session_state.embeddings,
                    persist_directory=COLLECTIONS["products"].persist_directory
                ),
                "customer_support": Chroma(
                    collection_name=COLLECTIONS["customer_support"].collection_name,
                    embedding_function=st.session_state.embeddings,
                    persist_directory=COLLECTIONS["customer_support"].persist_directory
                ),
                "financials": Chroma(
                    collection_name=COLLECTIONS["financials"].collection_name,
                    embedding_function=st.session_state.embeddings,
                    persist_directory=COLLECTIONS["financials"].persist_directory
                )
            }
            return True
        except Exception as e:
            st.error(f"Error connecting to OpenAI API: {str(e)}")
            st.error("Please check your internet connection and API key.")
            return False
    return False

def process_document(file) -> List[Document]:
    """Process uploaded PDF document"""
    if not st.session_state.embeddings:
        st.error("OpenAI API connection not initialized. Please check your API key.")
        return []
        
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file.getvalue())
            tmp_path = tmp_file.name
            
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()
        
        # Clean up temporary file
        os.unlink(tmp_path)
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        texts = text_splitter.split_documents(documents)
        
        return texts
    except Exception as e:
        st.error(f"Error processing document: {e}")
        return []

def route_query(question: str) -> List[DatabaseType]:
    """Route the question to appropriate databases"""
    router_prompt = ChatPromptTemplate.from_template(ROUTER_TEMPLATE)
    router_chain = router_prompt | st.session_state.llm | StrOutputParser()
    response = router_chain.invoke({"question": question})
    return response.strip().lower().split(",")

def query_multiple_databases(question: str) -> str:
    """Query multiple relevant databases and combine results"""
    database_types = route_query(question)
    all_docs = []
    
    # Collect relevant documents from each database
    for db_type in database_types:
        db = st.session_state.databases[db_type]
        docs = db.similarity_search(question, k=2)  # Reduced k since we're querying multiple DBs
        all_docs.extend(docs)
    
    # Sort all documents by relevance score if available
    # Note: You might need to modify this based on your similarity search implementation
    context = "\n\n---\n\n".join([doc.page_content for doc in all_docs])
    
    answer_prompt = ChatPromptTemplate.from_template(
        """Answer the question based on the following context from multiple databases. 
        If you use information from multiple sources, please indicate which type of source it came from.
        If you cannot answer the question based on the context, say "I don't have enough information to answer this question."

Context: {context}

Question: {question}

Answer:"""
    )
    
    answer_chain = answer_prompt | st.session_state.llm | StrOutputParser()
    return answer_chain.invoke({"context": context, "question": question})

def clear_collection(collection_type: DatabaseType = None):
    """Clear specified collection or all collections if none specified"""
    try:
        if collection_type:
            if collection_type in st.session_state.databases:
                collection_config = COLLECTIONS[collection_type]
                # Delete collection
                st.session_state.databases[collection_type]._collection.delete()
                # Remove from session state
                del st.session_state.databases[collection_type]
                # Clean up persist directory
                if os.path.exists(collection_config.persist_directory):
                    import shutil
                    shutil.rmtree(collection_config.persist_directory)
                st.success(f"Cleared {collection_config.name} collection")
        else:
            # Clear all collections
            for collection_type, collection_config in COLLECTIONS.items():
                if collection_type in st.session_state.databases:
                    st.session_state.databases[collection_type]._collection.delete()
                    if os.path.exists(collection_config.persist_directory):
                        import shutil
                        shutil.rmtree(collection_config.persist_directory)
            st.session_state.databases = {}
            st.success("Cleared all collections")
    except Exception as e:
        st.error(f"Error clearing collection(s): {str(e)}")

def main():
    st.title("📚 RAG with Database Routing")
 
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input(
            "Enter OpenAI API Key:",
            type="password",
            value=st.session_state.openai_api_key,
            key="api_key_input"
        )
        
        if api_key:
            st.session_state.openai_api_key = api_key
            if initialize_models():
                st.success("API Key set successfully!")
            else:
                st.error("Invalid API Key")
        
        if not st.session_state.openai_api_key:
            st.warning("Please enter your OpenAI API key to continue")
            st.stop()
            
        st.divider()
        st.header("Database Management")
        if st.button("Clear All Databases"):
            clear_collection()
        
        st.divider()
        st.subheader("Clear Individual Databases")
        for collection_type, collection_config in COLLECTIONS.items():
            if st.button(f"Clear {collection_config.name}"):
                clear_collection(collection_type)
    
    # Document upload section
    st.header("Document Upload")
    tabs = st.tabs([collection_config.name for collection_config in COLLECTIONS.values()])
    
    for (collection_type, collection_config), tab in zip(COLLECTIONS.items(), tabs):
        with tab:
            st.write(collection_config.description)
            uploaded_file = st.file_uploader(
                "Upload PDF document",
                type="pdf",
                key=f"upload_{collection_type}"
            )
            
            if uploaded_file:
                with st.spinner('Processing document...'):
                    texts = process_document(uploaded_file)
                    if texts:
                        db = st.session_state.databases[collection_type]
                        db.add_documents(texts)
                        st.success("Document processed and added to the database!")
    
    # Query section
    st.header("Ask Questions")
    question = st.text_input("Enter your question:")
    
    if question:
        with st.spinner('Finding answer...'):
            # Get relevant databases
            database_types = route_query(question)
            
            # Display routing information
            st.info(f"Searching in: {', '.join([COLLECTIONS[db_type].name for db_type in database_types])}")
            
            # Get and display answer
            answer = query_multiple_databases(question)
            st.write("### Answer")
            st.write(answer)

if __name__ == "__main__":
    main()
