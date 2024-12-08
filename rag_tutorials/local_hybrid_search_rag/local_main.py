import os
import logging
import streamlit as st
from raglite import RAGLiteConfig, insert_document, hybrid_search, retrieve_chunks, rerank_chunks, rag
from rerankers import Reranker
from typing import List, Dict, Any
from pathlib import Path
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

def initialize_config(settings: Dict[str, Any]) -> RAGLiteConfig:
    try:
        return RAGLiteConfig(
            db_url=settings["DBUrl"],
            llm=f"llama-cpp-python/{settings['LLMPath']}",
            embedder=f"llama-cpp-python/{settings['EmbedderPath']}",
            embedder_normalize=True,
            chunk_max_size=512,
            reranker=Reranker("ms-marco-MiniLM-L-12-v2", model_type="flashrank")
        )
    except Exception as e:
        raise ValueError(f"Configuration error: {e}")

def process_document(file_path: str) -> bool:
    try:
        if not st.session_state.get('my_config'):
            raise ValueError("Configuration not initialized")
        insert_document(Path(file_path), config=st.session_state.my_config)
        return True
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        return False

def perform_search(query: str) -> List[dict]:
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
        system_prompt = """You are a helpful AI assistant. When you don't know something, 
        be honest about it. Provide clear, concise, and accurate responses."""
        
        response_stream = rag(
            prompt=query,
            system_prompt=system_prompt,
            search=None,
            messages=[],
            max_tokens=1024,
            temperature=0.7,
            config=st.session_state.my_config
        )
        
        full_response = ""
        for chunk in response_stream:
            full_response += chunk
        
        if not full_response.strip():
            return "I apologize, but I couldn't generate a response. Please try rephrasing your question."
            
        return full_response
        
    except Exception as e:
        logger.error(f"Fallback error: {str(e)}")
        return "I apologize, but I encountered an error while processing your request. Please try again."

def main():
    st.set_page_config(page_title="Local LLM-Powered Hybrid Search-RAG Assistant", layout="wide")
    
    for state_var in ['chat_history', 'documents_loaded', 'my_config']:
        if state_var not in st.session_state:
            st.session_state[state_var] = [] if state_var == 'chat_history' else False if state_var == 'documents_loaded' else None

    with st.sidebar:
        st.title("Configuration")
        
        llm_path = st.text_input(
            "LLM Model Path", 
            value=st.session_state.get('llm_path', ''),
            placeholder="TheBloke/Llama-2-7B-Chat-GGUF/llama-2-7b-chat.Q4_K_M.gguf@4096",
            help="Path to your local LLM model in GGUF format"
        )
        
        embedder_path = st.text_input(
            "Embedder Model Path",
            value=st.session_state.get('embedder_path', ''),
            placeholder="lm-kit/bge-m3-gguf/bge-m3-Q4_K_M.gguf@1024",
            help="Path to your local embedding model in GGUF format"
        )
        
        db_url = st.text_input(
            "Database URL",
            value=st.session_state.get('db_url', ''),
            placeholder="postgresql://user:pass@host:port/db",
            help="Database connection URL"
        )
        
        if st.button("Save Configuration"):
            try:
                if not all([llm_path, embedder_path, db_url]):
                    st.error("All fields are required!")
                    return
                
                settings = {
                    "LLMPath": llm_path,
                    "EmbedderPath": embedder_path,
                    "DBUrl": db_url
                }
                
                st.session_state.my_config = initialize_config(settings)
                st.success("Configuration saved successfully!")
                
            except Exception as e:
                st.error(f"Configuration error: {str(e)}")

    st.title("🖥️ Local RAG App with Hybrid Search")

    if st.session_state.my_config:
        uploaded_files = st.file_uploader(
            "Upload PDF documents",
            type=["pdf"],
            accept_multiple_files=True,
            key="pdf_uploader"
        )

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
                        logger.info("No relevant documents found. Falling back to local LLM.")
                        with st.spinner("Using general knowledge to answer..."):
                            full_response = handle_fallback(user_input)
                            if full_response.startswith("I apologize"):
                                st.warning("No relevant documents found and fallback failed.")
                            else:
                                st.info("Answering from general knowledge.")
                    else:
                        formatted_messages = [
                            {"role": "user" if i % 2 == 0 else "assistant", "content": msg}
                            for i, msg in enumerate([m for pair in st.session_state.chat_history for m in pair])
                            if msg
                        ]
                        
                        response_stream = rag(
                            prompt=user_input,
                            system_prompt=RAG_SYSTEM_PROMPT,
                            search=hybrid_search,
                            messages=formatted_messages,
                            max_contexts=5,
                            config=st.session_state.my_config
                        )
                        
                        full_response = ""
                        for chunk in response_stream:
                            full_response += chunk
                            message_placeholder.markdown(full_response + "▌")
                    
                    message_placeholder.markdown(full_response)
                    st.session_state.chat_history.append((user_input, full_response))
                    
                except Exception as e:
                    logger.error(f"Error: {str(e)}")
                    st.error(f"Error: {str(e)}")
    else:
        st.info(
            "Please configure your model paths and upload documents to get started."
            if not st.session_state.my_config
            else "Please upload some documents to get started."
        )

if __name__ == "__main__":
    main()
