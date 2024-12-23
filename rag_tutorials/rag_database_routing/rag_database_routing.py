import os
from typing import List, Dict, Any, Literal
from dataclasses import dataclass
import streamlit as st
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import tempfile

# Load environment variables
load_dotenv()

# Constants
DatabaseType = Literal["products", "customer_support", "financials"]
PERSIST_DIRECTORY = "db_storage"

@dataclass
class Database:
    """Class to represent a database configuration"""
    name: str
    description: str
    collection_name: str
    persist_directory: str

# Database configurations
DATABASES: Dict[DatabaseType, Database] = {
    "products": Database(
        name="Product Information",
        description="Product details, specifications, and features",
        collection_name="products_db",
        persist_directory=f"{PERSIST_DIRECTORY}/products"
    ),
    "customer_support": Database(
        name="Customer Support & FAQ",
        description="Customer support information, frequently asked questions, and guides",
        collection_name="support_db",
        persist_directory=f"{PERSIST_DIRECTORY}/support"
    ),
    "financials": Database(
        name="Financial Information",
        description="Financial data, revenue, costs, and liabilities",
        collection_name="finance_db",
        persist_directory=f"{PERSIST_DIRECTORY}/finance"
    )
}

# Router prompt template
ROUTER_TEMPLATE = """You are a query routing expert. Your job is to analyze user questions and route them to the most appropriate database.

Available databases:
1. Product Information: Contains product details, specifications, and features
2. Customer Support & FAQ: Contains customer support information, frequently asked questions, and guides
3. Financial Information: Contains financial data, revenue, costs, and liabilities

User question: {question}

Return only one of these exact strings:
- products
- customer_support
- financials

Your response:"""

def init_session_state():
    """Initialize session state variables"""
    if 'databases' not in st.session_state:
        st.session_state.databases = {}
    if 'embeddings' not in st.session_state:
        st.session_state.embeddings = OpenAIEmbeddings()
    if 'llm' not in st.session_state:
        st.session_state.llm = ChatOpenAI(temperature=0)
    if 'router_chain' not in st.session_state:
        router_prompt = PromptTemplate(
            template=ROUTER_TEMPLATE,
            input_variables=["question"]
        )
        st.session_state.router_chain = LLMChain(
            llm=st.session_state.llm,
            prompt=router_prompt
        )

def process_document(file) -> List[Document]:
    """Process uploaded PDF document"""
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

def get_or_create_db(db_type: DatabaseType) -> Chroma:
    """Get or create a database for the specified type with proper initialization and error handling"""
    try:
        if db_type not in st.session_state.databases:
            db_config = DATABASES[db_type]
            
            # Ensure directory exists
            os.makedirs(db_config.persist_directory, exist_ok=True)
            
            # Initialize Chroma with proper settings
            st.session_state.databases[db_type] = Chroma(
                persist_directory=db_config.persist_directory,
                embedding_function=st.session_state.embeddings,
                collection_name=db_config.collection_name,
                collection_metadata={
                    "description": db_config.description,
                    "database_type": db_type
                }
            )
            
            # Log successful initialization
            st.success(f"Initialized {db_config.name} database")
            
        return st.session_state.databases[db_type]
    
    except Exception as e:
        st.error(f"Error initializing {db_type} database: {str(e)}")
        raise

def route_query(question: str) -> DatabaseType:
    """Route the question to the appropriate database"""
    response = st.session_state.router_chain.invoke({"question": question})
    return response["text"].strip().lower()

def query_database(db: Chroma, question: str) -> str:
    """Query the database and return the response"""
    docs = db.similarity_search(question, k=3)
    
    context = "\n\n".join([doc.page_content for doc in docs])
    
    prompt = PromptTemplate(
        template="""Answer the question based on the following context. If you cannot answer the question based on the context, say "I don't have enough information to answer this question."

Context: {context}

Question: {question}

Answer:""",
        input_variables=["context", "question"]
    )
    
    chain = LLMChain(llm=st.session_state.llm, prompt=prompt)
    response = chain.invoke({"context": context, "question": question})
    return response["text"]

def clear_database(db_type: DatabaseType = None):
    """Clear specified database or all databases if none specified"""
    try:
        if db_type:
            if db_type in st.session_state.databases:
                db_config = DATABASES[db_type]
                # Delete collection
                st.session_state.databases[db_type]._collection.delete()
                # Remove from session state
                del st.session_state.databases[db_type]
                # Clean up persist directory
                if os.path.exists(db_config.persist_directory):
                    import shutil
                    shutil.rmtree(db_config.persist_directory)
                st.success(f"Cleared {db_config.name} database")
        else:
            # Clear all databases
            for db_type, db_config in DATABASES.items():
                if db_type in st.session_state.databases:
                    st.session_state.databases[db_type]._collection.delete()
                    if os.path.exists(db_config.persist_directory):
                        import shutil
                        shutil.rmtree(db_config.persist_directory)
            st.session_state.databases = {}
            st.success("Cleared all databases")
    except Exception as e:
        st.error(f"Error clearing database(s): {str(e)}")

def main():
    st.title("📚 RAG Database Router ")
    
    init_session_state()
    
    # Sidebar for database management
    with st.sidebar:
        st.header("Database Management")
        if st.button("Clear All Databases"):
            clear_database()
        
        st.divider()
        st.subheader("Clear Individual Databases")
        for db_type, db_config in DATABASES.items():
            if st.button(f"Clear {db_config.name}"):
                clear_database(db_type)
    
    # Document upload section
    st.header("Document Upload")
    tabs = st.tabs([db.name for db in DATABASES.values()])
    
    for (db_type, db_config), tab in zip(DATABASES.items(), tabs):
        with tab:
            st.write(db_config.description)
            uploaded_file = st.file_uploader(
                "Upload PDF document",
                type="pdf",
                key=f"upload_{db_type}"
            )
            
            if uploaded_file:
                with st.spinner('Processing document...'):
                    texts = process_document(uploaded_file)
                    if texts:
                        db = get_or_create_db(db_type)
                        db.add_documents(texts)
                        st.success("Document processed and added to the database!")
    
    # Query section
    st.header("Ask Questions")
    question = st.text_input("Enter your question:")
    
    if question:
        with st.spinner('Finding answer...'):
            # Route the question
            db_type = route_query(question)
            db = get_or_create_db(db_type)
            
            # Display routing information
            st.info(f"Routing question to: {DATABASES[db_type].name}")
            
            # Get and display answer
            answer = query_database(db, question)
            st.write("### Answer")
            st.write(answer)

if __name__ == "__main__":
    main()
