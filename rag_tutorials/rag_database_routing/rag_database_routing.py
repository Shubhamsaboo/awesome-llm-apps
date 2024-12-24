import os
from typing import List, Dict, Literal
from dataclasses import dataclass
import streamlit as st
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
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

def init_session_state():
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
    if st.session_state.openai_api_key:
        os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key
        st.session_state.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        st.session_state.llm = ChatOpenAI(temperature=0)
        
        for config in COLLECTIONS.values():
            os.makedirs(config.persist_directory, exist_ok=True)
        
        st.session_state.databases = {
            db_type: Chroma(
                collection_name=config.collection_name,
                embedding_function=st.session_state.embeddings,
                persist_directory=config.persist_directory
            ) for db_type, config in COLLECTIONS.items()
        }
        return True
    return False

def process_document(file) -> List[Document]:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file.getvalue())
            tmp_path = tmp_file.name
            
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()
        os.unlink(tmp_path)
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=300)
        return text_splitter.split_documents(documents)
    except Exception as e:
        st.error(f"Error processing document: {e}")
        return []

def create_routing_agent() -> Agent:
    return Agent(
        model=OpenAIChat(id="gpt-4o", api_key=st.session_state.openai_api_key),
        tools=[],
        description="You are a query routing expert. Your only job is to analyze questions and determine which database they should be routed to.",
        instructions=[
            "1. For questions about products, return 'products'",
            "2. For questions about support, return 'support'",
            "3. For questions about finance, return 'finance'",
            "4. Return ONLY the database name"
        ],
        markdown=False,
        show_tool_calls=False
    )

def route_query(question: str) -> DatabaseType:
    try:
        routing_agent = create_routing_agent()
        response = routing_agent.run(question)
        db_type = response.content.strip().lower().translate(str.maketrans('', '', '`\'"'))
        
        if db_type not in COLLECTIONS:
            st.warning(f"Invalid database type: {db_type}, defaulting to products")
            return "products"
        
        st.info(f"Routing question to {db_type} database")
        return db_type
    except Exception as e:
        st.error(f"Routing error: {str(e)}")
        return "products"

def create_fallback_agent(chat_model: BaseLanguageModel):
    def web_research(query: str) -> str:
        try:
            search = DuckDuckGoSearchRun(num_results=5)
            return search.run(query)
        except Exception as e:
            return f"Search failed: {str(e)}. Providing answer based on general knowledge."

    tools = [web_research]
    return create_react_agent(model=chat_model, tools=tools, debug=False)

def query_database(db: Chroma, question: str) -> tuple[str, list]:
    try:
        retriever = db.as_retriever(search_type="similarity_score_threshold", search_kwargs={"k": 4, "score_threshold": 0.4})
        relevant_docs = retriever.get_relevant_documents(question)

        if relevant_docs:
            retrieval_qa_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
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
            "messages": [HumanMessage(content=f"Research and provide a detailed answer for: '{question}'")],
            "is_last_step": False
        }
        
        try:
            response = fallback_agent.invoke(agent_input, config={"recursion_limit": 100})
            if isinstance(response, dict) and "messages" in response:
                answer = response["messages"][-1].content
                return f"Web Search Result:\n{answer}", []
        except Exception:
            fallback_response = st.session_state.llm.invoke(question).content
            return f"Web search unavailable. General response: {fallback_response}", []

def main():
    st.set_page_config(page_title="RAG Agent with Database Routing", page_icon="📚")
    st.title("📚 RAG Agent with Database Routing")
    
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("Enter OpenAI API Key:", type="password", value=st.session_state.openai_api_key, key="api_key_input")
        
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
    tabs = st.tabs([config.name for config in COLLECTIONS.values()])
    
    for (collection_type, config), tab in zip(COLLECTIONS.items(), tabs):
        with tab:
            st.write(config.description)
            uploaded_files = st.file_uploader(f"Upload PDF documents to {config.name}", type="pdf", key=f"upload_{collection_type}", accept_multiple_files=True)
            
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
    
    st.header("Ask Questions")
    st.info("Enter your question below to find answers from the relevant database.")
    question = st.text_input("Enter your question:")
    
    if question:
        with st.spinner('Finding answer...'):
            collection_type = route_query(question)
            db = st.session_state.databases[collection_type]
            st.info(f"Routing question to: {COLLECTIONS[collection_type].name}")
            answer, relevant_docs = query_database(db, question)
            st.write("### Answer")
            st.write(answer)

if __name__ == "__main__":
    main()
