import os
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings, ChatCohere
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain import hub
import tempfile
from langgraph.prebuilt import create_react_agent
from langchain_community.tools import DuckDuckGoSearchRun
from typing import TypedDict, List
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from time import sleep
from tenacity import retry, wait_exponential, stop_after_attempt


def init_session_state():
    if 'api_keys_submitted' not in st.session_state:
        st.session_state.api_keys_submitted = False
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'vectorstore' not in st.session_state:
        st.session_state.vectorstore = None
    if 'qdrant_api_key' not in st.session_state:
        st.session_state.qdrant_api_key = ""
    if 'qdrant_url' not in st.session_state:
        st.session_state.qdrant_url = ""

def sidebar_api_form():
    with st.sidebar:
        st.header("API Credentials")
        
        if st.session_state.api_keys_submitted:
            st.success("API credentials verified")
            if st.button("Reset Credentials"):
                st.session_state.clear()
                st.rerun()
            return True
        
        with st.form("api_credentials"):
            cohere_key = st.text_input("Cohere API Key", type="password")
            qdrant_key = st.text_input("Qdrant API Key", type="password", help="Enter your Qdrant API key")
            qdrant_url = st.text_input("Qdrant URL", 
                                     placeholder="https://xyz-example.eu-central.aws.cloud.qdrant.io:6333",
                                     help="Enter your Qdrant instance URL")
            
            if st.form_submit_button("Submit Credentials"):
                try:
                    client = QdrantClient(url=qdrant_url, api_key=qdrant_key, timeout=60)
                    client.get_collections()
                    
                    st.session_state.cohere_api_key = cohere_key
                    st.session_state.qdrant_api_key = qdrant_key
                    st.session_state.qdrant_url = qdrant_url
                    st.session_state.api_keys_submitted = True
                    
                    st.success("Credentials verified!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Qdrant connection failed: {str(e)}")
        return False

def init_qdrant() -> QdrantClient:
    if not st.session_state.get("qdrant_api_key"):
        raise ValueError("Qdrant API key not provided")
    if not st.session_state.get("qdrant_url"):
        raise ValueError("Qdrant URL not provided")
    
    return QdrantClient(url=st.session_state.qdrant_url,
                       api_key=st.session_state.qdrant_api_key,
                       timeout=60)

init_session_state()

if not sidebar_api_form():
    st.info("Please enter your API credentials in the sidebar to continue.")
    st.stop()

embedding = CohereEmbeddings(model="embed-english-v3.0",
                            cohere_api_key=st.session_state.cohere_api_key)

chat_model = ChatCohere(model="command-r7b-12-2024",
                       temperature=0.1,
                       max_tokens=512,
                       verbose=True,
                       cohere_api_key=st.session_state.cohere_api_key)

client = init_qdrant()

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

COLLECTION_NAME = "cohere_rag"

def create_vector_stores(texts):
    """Create and populate vector store with documents."""
    try:
        try:
            client.create_collection(collection_name=COLLECTION_NAME,
                                   vectors_config=VectorParams(size=1024,
                                                            distance=Distance.COSINE))
            st.success(f"Created new collection: {COLLECTION_NAME}")
        except Exception as e:
            if "already exists" not in str(e).lower():
                raise e
        
        vector_store = QdrantVectorStore(client=client,
                                       collection_name=COLLECTION_NAME,
                                       embedding=embedding)
        
        with st.spinner('Storing documents in Qdrant...'):
            vector_store.add_documents(texts)
            st.success("Documents successfully stored in Qdrant!")
        
        return vector_store
        
    except Exception as e:
        st.error(f"Error in vector store creation: {str(e)}")
        return None

# Define the state schema using TypedDict
class AgentState(TypedDict):
    """State schema for the agent."""
    messages: List[HumanMessage | AIMessage | SystemMessage]
    is_last_step: bool

class RateLimitedDuckDuckGo(DuckDuckGoSearchRun):
    @retry(wait=wait_exponential(multiplier=1, min=4, max=10),
           stop=stop_after_attempt(3))
    def run(self, query: str) -> str:
        """Run search with rate limiting."""
        try:
            sleep(2)  # Add delay between requests
            return super().run(query)
        except Exception as e:
            if "Ratelimit" in str(e):
                sleep(5)  # Longer delay on rate limit
                return super().run(query)
            raise e

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

def process_query(vectorstore, query) -> tuple[str, list]:
    """Process a query using RAG with fallback to web search."""
    try:
        retriever = vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": 10,
                "score_threshold": 0.7
            }
        )

        relevant_docs = retriever.get_relevant_documents(query)

        if relevant_docs:
            retrieval_qa_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
            combine_docs_chain = create_stuff_documents_chain(chat_model, retrieval_qa_prompt)
            retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)
            response = retrieval_chain.invoke({"input": query})
            return response['answer'], relevant_docs
            
        else:
            st.info("No relevant documents found. Searching web...")
            fallback_agent = create_fallback_agent(chat_model)
            
            with st.spinner('Researching...'):
                agent_input = {
                    "messages": [
                        HumanMessage(content=f"""Please thoroughly research the question: '{query}' and provide a detailed and comprehensive response. Make sure to gather the latest information from credible sources. Minimum 400 words.""")
                    ],
                    "is_last_step": False
                }
                
                config = {"recursion_limit": 100}
                
                try:
                    response = fallback_agent.invoke(agent_input, config=config)
                    
                    if isinstance(response, dict) and "messages" in response:
                        last_message = response["messages"][-1]
                        answer = last_message.content if hasattr(last_message, 'content') else str(last_message)
                        
                        return f"""Web Search Result:
{answer}
""", []
                    
                except Exception as agent_error:
                    fallback_response = chat_model.invoke(f"Please provide a general answer to: {query}").content
                    return f"Web search unavailable. General response: {fallback_response}", []

    except Exception as e:
        st.error(f"Error: {str(e)}")
        return "I encountered an error. Please try rephrasing your question.", []

def post_process(answer, sources):
    """Post-process the answer and format sources."""
    answer = answer.strip()

    # Summarize long answers
    if len(answer) > 500:
        summary_prompt = f"Summarize the following answer in 2-3 sentences: {answer}"
        summary = chat_model.invoke(summary_prompt).content
        answer = f"{summary}\n\nFull Answer: {answer}"
    
    formatted_sources = []
    for i, source in enumerate(sources, 1):
        formatted_source = f"{i}. {source.page_content[:200]}..."
        formatted_sources.append(formatted_source)
    return answer, formatted_sources

st.title("RAG Agent with Cohere ⌘R")

uploaded_file = st.file_uploader("Choose a PDF or Image File", type=["pdf", "jpg", "jpeg"])

if uploaded_file is not None and 'processed_file' not in st.session_state:
    with st.spinner('Processing file... This may take a while for images.'):
        texts = process_document(uploaded_file)
        vectorstore = create_vector_stores(texts)
        if vectorstore:
            st.session_state.vectorstore = vectorstore
            st.session_state.processed_file = True
            st.success('File uploaded and processed successfully!')
        else:
            st.error('Failed to process file. Please try again.')

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if query := st.chat_input("Ask a question about the document:"):
    st.session_state.chat_history.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    if st.session_state.vectorstore:
        with st.chat_message("assistant"):
            try:
                answer, sources = process_query(st.session_state.vectorstore, query)
                st.markdown(answer)
                
                if sources:
                    with st.expander("Sources"):
                        for source in sources:
                            st.markdown(f"- {source.page_content[:200]}...")
                
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer
                })
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info("Please try asking your question again.")
    else:
        st.error("Please upload a document first.")

with st.sidebar:
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button('Clear Chat History'):
            st.session_state.chat_history = []
            st.rerun()
    with col2:
        if st.button('Clear All Data'):
            try:
                collections = client.get_collections().collections
                collection_names = [col.name for col in collections]
                
                if COLLECTION_NAME in collection_names:
                    client.delete_collection(COLLECTION_NAME)
                if f"{COLLECTION_NAME}_compressed" in collection_names:
                    client.delete_collection(f"{COLLECTION_NAME}_compressed")
                
                st.session_state.vectorstore = None
                st.session_state.chat_history = []
                st.success("All data cleared successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error clearing data: {str(e)}")
