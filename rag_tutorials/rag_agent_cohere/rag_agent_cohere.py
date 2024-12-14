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


def init_session_state():
    """Initialize session state variables."""
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
    """Render API credentials form in sidebar."""
    with st.sidebar:
        st.header("API Credentials")
        
        # Show current status
        if st.session_state.api_keys_submitted:
            st.success("API credentials verified")
            if st.button("Reset Credentials"):
                st.session_state.clear()
                st.rerun()
            return True
        
        # Show API form
        with st.form("api_credentials"):
            cohere_key = st.text_input("Cohere API Key", type="password")
            qdrant_key = st.text_input(
                "Qdrant API Key",
                type="password",
                help="Enter your Qdrant API key"
            )
            qdrant_url = st.text_input(
                "Qdrant URL",
                placeholder="https://xyz-example.eu-central.aws.cloud.qdrant.io:6333",
                help="Enter your Qdrant instance URL"
            )
            
            if st.form_submit_button("Submit Credentials"):
                try:
                    # First validate the credentials before saving to session state
                    client = QdrantClient(
                        url=qdrant_url,
                        api_key=qdrant_key,
                        timeout=60
                    )
                    # Test connection
                    client.get_collections()
                    
                    # Only save to session state after successful validation
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
    """Initialize Qdrant vector database."""
    if not st.session_state.get("qdrant_api_key"):
        raise ValueError("Qdrant API key not provided")
    if not st.session_state.get("qdrant_url"):
        raise ValueError("Qdrant URL not provided")
    
    return QdrantClient(
        url=st.session_state.qdrant_url,
        api_key=st.session_state.qdrant_api_key,
        timeout=60
    )

# Initialize session state
init_session_state()

# Main application logic
if not sidebar_api_form():
    st.info("Please enter your API credentials in the sidebar to continue.")
    st.stop()

# Initialize services with verified credentials
embedding = CohereEmbeddings(
    model="embed-english-v3.0",
    cohere_api_key=st.session_state.cohere_api_key
)

chat_model = ChatCohere(
    model="command-r7b-12-2024",
    temperature=0.1,
    max_tokens=512,
    verbose=True,
    cohere_api_key=st.session_state.cohere_api_key
)

client = init_qdrant()

#document preprocessing

def process_document(file):
    """Process uploaded PDF document using a temporary file."""
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file.getvalue())
            tmp_path = tmp_file.name
            
        # Process the temporary file
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)
        
        # Clean up the temporary file
        os.unlink(tmp_path)
        
        return texts
    except Exception as e:
        st.error(f"Error processing document: {e}")
        return []

COLLECTION_NAME = "cohere_rag"

def create_vector_stores(texts):
    """Create and populate vector store with documents."""
    try:
        # First, create the collection explicitly
        try:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=1024,  # Dimension for Cohere embed-english-v3.0
                    distance=Distance.COSINE
                )
            )
            st.success(f"Created new collection: {COLLECTION_NAME}")
        except Exception as e:
            if "already exists" not in str(e).lower():
                raise e
        
        # Then initialize the vector store
        vector_store = QdrantVectorStore(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding=embedding,
        )
        
        with st.spinner('Storing documents in Qdrant...'):
            vector_store.add_documents(texts)
            st.success("Documents successfully stored in Qdrant!")
        
        return vector_store
        
    except Exception as e:
        st.error(f"Error in vector store creation: {str(e)}")
        return None

def create_fallback_agent():
    """Create a LangGraph agent with DuckDuckGo search tool."""
    
    def web_research(query: str) -> str:
        """Search the web for information about a query."""
        search = DuckDuckGoSearchRun()
        results = search.run(query)
        return f"Web search results: {results}"
    
    tools = [web_research]
    
    # Create agent with Cohere model
    agent = create_react_agent(
        chat_model,  # Using the already initialized Cohere model
        tools=tools,
    )
    
    return agent

def process_query(vectorstore, query) -> tuple[str, list]:
    """Process a query using RAG with fallback to web search."""
    try:
        # First try vector store retrieval
        retriever = vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": 10,
                "score_threshold": 0.7  # Only return relevant documents
            }
        )

        # Get relevant documents
        with st.spinner('Searching document database...'):
            relevant_docs = retriever.get_relevant_documents(query)

        if relevant_docs:
            # Use RAG with document context
            retrieval_qa_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
            
            combine_docs_chain = create_stuff_documents_chain(
                chat_model, 
                retrieval_qa_prompt
            )
            
            retrieval_chain = create_retrieval_chain(
                retriever, 
                combine_docs_chain
            )
            
            with st.spinner('Generating response from documents...'):
                response = retrieval_chain.invoke({"input": query})
                if not response or 'answer' not in response:
                    raise ValueError("No response generated")
                
                return response['answer'], relevant_docs
        else:
            # Fallback to web search using LangGraph agent
            st.info("No relevant documents found. Searching the web...")
            
            fallback_agent = create_fallback_agent()
            
            with st.spinner('Searching web and generating response...'):
                # Prepare input for the agent
                agent_input = {
                    "messages": [
                        ("user", f"Please search and answer this question: {query}")
                    ]
                }
                
                # Get agent response
                response = fallback_agent.invoke(agent_input)
                last_message = response["messages"][-1]
                
                if isinstance(last_message, tuple):
                    answer = last_message[1]
                else:
                    answer = last_message.content
                
                return f"Based on web search: {answer}", []

    except Exception as e:
        st.error(f"Error processing query: {str(e)}")
        return "I encountered an error processing your query. Please try again.", []

#post processing - strip, summarize along with formatted sources
def post_process(answer, sources):
    """Post-process the answer and format sources."""
    answer = answer.strip()

    # Summarize long answers
    if len(answer) > 500:
        summary_prompt = f"Summarize the following answer in 2-3 sentences: {answer}"
        summary = chat_model.invoke(summary_prompt).content  # Changed from predict to invoke
        answer = f"{summary}\n\nFull Answer: {answer}"
    
    formatted_sources = []
    for i, source in enumerate(sources, 1):
        formatted_source = f"{i}. {source.page_content[:200]}..."
        formatted_sources.append(formatted_source)
    return answer, formatted_sources

st.title("RAG Agent with Cohere 🤖")  # New heading

uploaded_file = st.file_uploader("Choose a PDF or Image File", type=["pdf", "jpg", "jpeg"])

if uploaded_file is not None:
    with st.spinner('Processing file... This may take a while for images.'):
        texts = process_document(uploaded_file)
        vectorstore = create_vector_stores(texts)
        if vectorstore:
            st.session_state.vectorstore = vectorstore
            st.success('File uploaded and processed successfully!')
        else:
            st.error('Failed to process file. Please try again.')

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if query := st.chat_input("Ask a question about the document:"):
    st.session_state.chat_history.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    if st.session_state.vectorstore:
        with st.chat_message("assistant"):
            try:
                answer, sources = process_query(st.session_state.vectorstore, query)
                
                if sources:  # Only post-process if we have sources
                    processed_answer, formatted_sources = post_process(answer, sources)
                else:
                    processed_answer, formatted_sources = answer, []
                
                st.markdown(f"{processed_answer}")
                
                if formatted_sources:
                    with st.expander("Sources"):
                        for source in formatted_sources:
                            st.markdown(f"- {source}")
                
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": processed_answer
                })
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info("Please try asking your question again.")
    else:
        st.error("Please upload a document first.")


# Add to sidebar
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
                # Check if collections exist before deleting
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
