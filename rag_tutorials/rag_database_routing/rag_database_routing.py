import os
from typing import List, Dict, Any, Literal
from dataclasses import dataclass
import streamlit as st
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
import tempfile
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from langchain.schema import HumanMessage
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain import hub
from langgraph.prebuilt import create_react_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.language_models import BaseLanguageModel
from langchain.prompts import ChatPromptTemplate

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

init_session_state()

DatabaseType = Literal["products", "support", "finance"]
PERSIST_DIRECTORY = "db_storage"

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
    "support": CollectionConfig(
        name="Customer Support & FAQ",
        description="Customer support information, frequently asked questions, and guides",
        collection_name="support_collection",
        persist_directory=f"{PERSIST_DIRECTORY}/support"
    ),
    "finance": CollectionConfig(
        name="Financial Information",
        description="Financial data, revenue, costs, and liabilities",
        collection_name="finance_collection",
        persist_directory=f"{PERSIST_DIRECTORY}/finance"
    )
}

def initialize_models():
    """Initialize OpenAI models with API key"""
    if st.session_state.openai_api_key:
        os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key
        st.session_state.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        st.session_state.llm = ChatOpenAI(temperature=0)
        
        # Ensure directories exist
        for collection_config in COLLECTIONS.values():
            os.makedirs(collection_config.persist_directory, exist_ok=True)
        
        # Initialize Chroma collections
        st.session_state.databases = {
            "products": Chroma(
                collection_name=COLLECTIONS["products"].collection_name,
                embedding_function=st.session_state.embeddings,
                persist_directory=COLLECTIONS["products"].persist_directory
            ),
            "support": Chroma(
                collection_name=COLLECTIONS["support"].collection_name,
                embedding_function=st.session_state.embeddings,
                persist_directory=COLLECTIONS["support"].persist_directory
            ),
            "finance": Chroma(
                collection_name=COLLECTIONS["finance"].collection_name,
                embedding_function=st.session_state.embeddings,
                persist_directory=COLLECTIONS["finance"].persist_directory
            )
        }
        return True
    return False

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

def create_routing_agent() -> Agent:
    """Creates a routing agent using phidata framework"""
    return Agent(
        model=OpenAIChat(
            id="gpt-4o",
            api_key=st.session_state.openai_api_key
        ),
        tools=[],
        description="""You are a query routing expert. Your only job is to analyze questions and determine which database they should be routed to.
        You must respond with exactly one of these three options: 'products', 'support', or 'finance'. The user's question is: {question}""",
        instructions=[
            "Follow these rules strictly:",
            "1. For questions about products, features, specifications, or item details, or product manuals → return 'products'",
            "2. For questions about help, guidance, troubleshooting, or customer service, FAQ, or guides → return 'support'",
            "3. For questions about costs, revenue, pricing, or financial data, or financial reports and investments → return 'finance'",
            "4. Return ONLY the database name, no other text or explanation"
        ],
        markdown=False,
        show_tool_calls=False
    )

def route_query(question: str) -> DatabaseType:
    try:
        routing_agent = create_routing_agent()
        response = routing_agent.run(question)
        
        db_type = (response.content
                  .strip()
                  .lower()
                  .translate(str.maketrans('', '', '`\'"')))  # More elegant string cleaning
        
        # Validate database type
        if db_type not in COLLECTIONS:
            st.warning(f"Invalid database type: {db_type}, defaulting to products")
            return "products"
        
        st.info(f"Routing question to {db_type} database")
        return db_type
        
    except Exception as e:
        st.error(f"Routing error: {str(e)}")
        return "products"

def create_fallback_agent(chat_model: BaseLanguageModel):
    """Create a LangGraph agent for web research."""
    
    def web_research(query: str) -> str:
        """Web search with result formatting."""
        try:
            search = DuckDuckGoSearchRun(num_results=5)
            results = search.run(query)
            return results
        except Exception as e:
            return f"Search failed: {str(e)}. Providing answer based on general knowledge."

    tools = [web_research]
    
    agent = create_react_agent(model=chat_model,
                             tools=tools,
                             debug=False)
    
    return agent

def query_database(db: Chroma, question: str) -> tuple[str, list]:
    try:
        retriever = db.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": 4, "score_threshold": 0.3}
        )

        relevant_docs = retriever.get_relevant_documents(question)

        if relevant_docs:
            # Use simpler chain creation with hub prompt
            retrieval_qa_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a helpful AI assistant that answers questions based on provided context.
                             Always be direct and concise in your responses.
                             If the context doesn't contain enough information to fully answer the question, acknowledge this limitation.
                             Base your answers strictly on the provided context and avoid making assumptions."""),
                ("human", "Here is the context:\n{context}"),
                ("human", "Question: {input}"),
                ("assistant", "I'll help answer your question based on the context provided."),
                ("human", "Please provide your answer:"),
            ])
            combine_docs_chain = create_stuff_documents_chain(st.session_state.llm, retrieval_qa_prompt)
            retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)
            
            response = retrieval_chain.invoke({"input": question})
            return response['answer'], relevant_docs
        return _handle_web_fallback(question)

    except Exception as e:
        st.error(f"Error: {str(e)}")
        return "I encountered an error. Please try rephrasing your question.", []

def _handle_web_fallback(question: str) -> tuple[str, list]:
    st.info("No relevant documents found. Searching web...")
    fallback_agent = create_fallback_agent(st.session_state.llm)
    
    with st.spinner('Researching...'):
        agent_input = {
            "messages": [
                HumanMessage(content=f"Research and provide a detailed answer for: '{question}'")
            ],
            "is_last_step": False
        }
        
        try:
            response = fallback_agent.invoke(agent_input, config={"recursion_limit": 100})
            if isinstance(response, dict) and "messages" in response:
                answer = response["messages"][-1].content
                return f"Web Search Result:\n{answer}", []
                
        except Exception:
            # Fallback to general LLM response
            fallback_response = st.session_state.llm.invoke(question).content
            return f"Web search unavailable. General response: {fallback_response}", []

def main():
    """Main application function."""
    st.set_page_config(page_title="RAG Agent with Database Routing", page_icon="📚")
    st.title("📚 RAG Agent with Database Routing")
    
    # Sidebar for API key and database management
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

        st.markdown("---")

    st.header("Document Upload")
    st.info("Upload documents to populate the databases. Each tab corresponds to a different database.")
    tabs = st.tabs([collection_config.name for collection_config in COLLECTIONS.values()])
    
    for (collection_type, collection_config), tab in zip(COLLECTIONS.items(), tabs):
        with tab:
            st.write(collection_config.description)
            uploaded_files = st.file_uploader(
                f"Upload PDF documents to {collection_config.name}",
                type="pdf",
                key=f"upload_{collection_type}",
                accept_multiple_files=True  
            )
            
            if uploaded_files:
                with st.spinner('Processing documents...'):
                    all_texts = []
                    for uploaded_file in uploaded_files:
                        texts = process_document(uploaded_file)
                        all_texts.extend(texts)
                    
                    if all_texts:
                        db = st.session_state.databases[collection_type]
                        db.add_documents(all_texts)
                        st.success("Documents processed and added to the database!")
    
    # Query section
    st.header("Ask Questions")
    st.info("Enter your question below to find answers from the relevant database.")
    question = st.text_input("Enter your question:")
    
    if question:
        with st.spinner('Finding answer...'):
            # Route the question
            collection_type = route_query(question)
            db = st.session_state.databases[collection_type]
            
            # Display routing information
            st.info(f"Routing question to: {COLLECTIONS[collection_type].name}")
            
            # Get and display answer
            answer, relevant_docs = query_database(db, question)
            st.write("### Answer")
            st.write(answer)

if __name__ == "__main__":
    main()
