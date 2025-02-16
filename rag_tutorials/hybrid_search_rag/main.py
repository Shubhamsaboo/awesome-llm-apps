import os
import logging
import streamlit as st
from raglite import RAGLiteConfig, insert_document, hybrid_search, retrieve_chunks, rerank_chunks, rag
from rerankers import Reranker
from typing import List
from pathlib import Path
import anthropic
import time
import warnings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore", message=".*torch.classes.*")

RAG_SYSTEM_PROMPT = """
You are a friendly and knowledgeable assistant that provides complete and insightful answers.
Answer the user's question using only the context below.
When responding, you MUST NOT reference the existence of the context, directly or indirectly.
Instead, you MUST treat the context as if its contents are entirely part of your working memory.
""".strip()

def initialize_config(openai_key: str, anthropic_key: str, cohere_key: str, db_url: str) -> RAGLiteConfig:
    """Initializes and returns a RAGLiteConfig object with the specified API keys and database URL.

    This function sets the provided API keys in the environment variables and returns a 
    RAGLiteConfig object configured with the given database URL and pre-defined settings for 
    language model, embedder, and reranker.

    Args:
        openai_key (str): The API key for OpenAI services.
        anthropic_key (str): The API key for Anthropic services.
        cohere_key (str): The API key for Cohere services.
        db_url (str): The database URL for connecting to the desired data source.

    Returns:
        RAGLiteConfig: A configuration object initialized with the specified parameters.

    Raises:
        ValueError: If there is an issue setting up the configuration, an error is raised with details."""
    try:
        os.environ["OPENAI_API_KEY"] = openai_key
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key
        os.environ["COHERE_API_KEY"] = cohere_key
        
        return RAGLiteConfig(
            db_url=db_url,
            llm="claude-3-opus-20240229",
            embedder="text-embedding-3-large",
            embedder_normalize=True,
            chunk_max_size=2000,
            embedder_sentence_window_size=2,
            reranker=Reranker("cohere", api_key=cohere_key, lang="en")
        )
    except Exception as e:
        raise ValueError(f"Configuration error: {e}")

def process_document(file_path: str) -> bool:
    """Processes a document by inserting it into a system with a given configuration.

    This function checks if a configuration is initialized in the session state.
    If the configuration is present, it attempts to insert the document located
    at the given file path using this configuration.

    Args:
        file_path (str): The path to the document to be processed.

    Returns:
        bool: True if the document was successfully processed; False otherwise."""
    try:
        if not st.session_state.get('my_config'):
            raise ValueError("Configuration not initialized")
        insert_document(Path(file_path), config=st.session_state.my_config)
        return True
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        return False

def perform_search(query: str) -> List[dict]:
    """Conducts a hybrid search and returns a list of ranked chunks based on the query.

    This function performs a search using a hybrid search method, retrieves the relevant 
    chunks, and reranks them according to the query. It handles any exceptions that occur 
    during the process and logs the errors.

    Args:
        query (str): The search query string.

    Returns:
        List[dict]: A list of dictionaries representing the ranked chunks. Returns an 
        empty list if no results are found or if an error occurs."""
    try:
        chunk_ids, scores = hybrid_search(query, num_results=10, config=st.session_state.my_config)
        if not chunk_ids:
            return []
        chunks = retrieve_chunks(chunk_ids, config=st.session_state.my_config)
        return rerank_chunks(query, chunks, config=st.session_state.my_config)
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return []

def handle_fallback(query: str) -> str:
    try:
        client = anthropic.Anthropic(api_key=st.session_state.user_env["ANTHROPIC_API_KEY"])
        system_prompt = """You are a helpful AI assistant. When you don't know something, 
        be honest about it. Provide clear, concise, and accurate responses. If the question 
        is not related to any specific document, use your general knowledge to answer."""
        
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": query}],
            temperature=0.7
        )
        return message.content[0].text
    except Exception as e:
        logger.error(f"Fallback error: {str(e)}")
        st.error(f"Fallback error: {str(e)}")  # Show error in UI
        return "I apologize, but I encountered an error while processing your request. Please try again."

def main():
    st.set_page_config(page_title="LLM-Powered Hybrid Search-RAG Assistant", layout="wide")
    
    for state_var in ['chat_history', 'documents_loaded', 'my_config', 'user_env']:
        if state_var not in st.session_state:
            st.session_state[state_var] = [] if state_var == 'chat_history' else False if state_var == 'documents_loaded' else None if state_var == 'my_config' else {}

    with st.sidebar:
        st.title("Configuration")
        openai_key = st.text_input("OpenAI API Key", value=st.session_state.get('openai_key', ''), type="password", placeholder="sk-...")
        anthropic_key = st.text_input("Anthropic API Key", value=st.session_state.get('anthropic_key', ''), type="password", placeholder="sk-ant-...")
        cohere_key = st.text_input("Cohere API Key", value=st.session_state.get('cohere_key', ''), type="password", placeholder="Enter Cohere key")
        db_url = st.text_input("Database URL", value=st.session_state.get('db_url', 'sqlite:///raglite.sqlite'), placeholder="sqlite:///raglite.sqlite")
        
        if st.button("Save Configuration"):
            try:
                if not all([openai_key, anthropic_key, cohere_key, db_url]):
                    st.error("All fields are required!")
                    return
                
                for key, value in {'openai_key': openai_key, 'anthropic_key': anthropic_key, 'cohere_key': cohere_key, 'db_url': db_url}.items():
                    st.session_state[key] = value
                
                st.session_state.my_config = initialize_config(openai_key=openai_key, anthropic_key=anthropic_key, cohere_key=cohere_key, db_url=db_url)
                st.session_state.user_env = {"ANTHROPIC_API_KEY": anthropic_key}
                st.success("Configuration saved successfully!")
            except Exception as e:
                st.error(f"Configuration error: {str(e)}")

    st.title("👀 RAG App with Hybrid Search")

    if st.session_state.my_config:
        uploaded_files = st.file_uploader("Upload PDF documents", type=["pdf"], accept_multiple_files=True, key="pdf_uploader")

        if uploaded_files:
            success = False
            for uploaded_file in uploaded_files:
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    
                    if process_document(temp_path):
                        st.success(f"Successfully processed: {uploaded_file.name}")
                        success = True
                    else:
                        st.error(f"Failed to process: {uploaded_file.name}")
                    os.remove(temp_path)
            
            if success:
                st.session_state.documents_loaded = True
                st.success("Documents are ready! You can now ask questions about them.")

    if st.session_state.documents_loaded:
        for msg in st.session_state.chat_history:
            with st.chat_message("user"): st.write(msg[0])
            with st.chat_message("assistant"): st.write(msg[1])

        user_input = st.chat_input("Ask a question about the documents...")
        if user_input:
            with st.chat_message("user"): st.write(user_input)
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                try:
                    reranked_chunks = perform_search(query=user_input)
                    if not reranked_chunks or len(reranked_chunks) == 0:
                        logger.info("No relevant documents found. Falling back to Claude.")
                        st.info("No relevant documents found. Using general knowledge to answer.")
                        full_response = handle_fallback(user_input)
                    else:
                        formatted_messages = [{"role": "user" if i % 2 == 0 else "assistant", "content": msg}
                                           for i, msg in enumerate([m for pair in st.session_state.chat_history for m in pair]) if msg]
                        
                        response_stream = rag(prompt=user_input, 
                                           system_prompt=RAG_SYSTEM_PROMPT,
                                           search=hybrid_search, 
                                           messages=formatted_messages,
                                           max_contexts=5, 
                                           config=st.session_state.my_config)
                        
                        full_response = ""
                        for chunk in response_stream:
                            full_response += chunk
                            message_placeholder.markdown(full_response + "▌")
                    
                    message_placeholder.markdown(full_response)
                    st.session_state.chat_history.append((user_input, full_response))
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    else:
        st.info("Please configure your API keys and upload documents to get started." if not st.session_state.my_config else "Please upload some documents to get started.")

if __name__ == "__main__":
    main()