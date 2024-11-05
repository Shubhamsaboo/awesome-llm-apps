import streamlit as st
import requests
from anthropic import Anthropic
import time
from typing import List, Dict, Optional
from urllib.parse import urlparse

class RAGPipeline:
    def __init__(self, ragie_api_key: str, anthropic_api_key: str):
        """
        Initialize the RAG pipeline with API keys.
        """
        self.ragie_api_key = ragie_api_key
        self.anthropic_api_key = anthropic_api_key
        self.anthropic_client = Anthropic(api_key=anthropic_api_key)
        
        # API endpoints
        self.RAGIE_UPLOAD_URL = "https://api.ragie.ai/documents/url"
        self.RAGIE_RETRIEVAL_URL = "https://api.ragie.ai/retrievals"
    
    def upload_document(self, url: str, name: Optional[str] = None, mode: str = "fast") -> Dict:
        """
        Upload a document to Ragie from a URL.
        """
        if not name:
            name = urlparse(url).path.split('/')[-1] or "document"
            
        payload = {
            "mode": mode,
            "name": name,
            "url": url
        }
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.ragie_api_key}"
        }
        
        response = requests.post(self.RAGIE_UPLOAD_URL, json=payload, headers=headers)
        
        if not response.ok:
            raise Exception(f"Document upload failed: {response.status_code} {response.reason}")
            
        return response.json()
    
    def retrieve_chunks(self, query: str, scope: str = "tutorial") -> List[str]:
        """
        Retrieve relevant chunks from Ragie for a given query.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.ragie_api_key}"
        }
        
        payload = {
            "query": query,
            "filters": {
                "scope": scope
            }
        }
        
        response = requests.post(
            self.RAGIE_RETRIEVAL_URL,
            headers=headers,
            json=payload
        )
        
        if not response.ok:
            raise Exception(f"Retrieval failed: {response.status_code} {response.reason}")
            
        data = response.json()
        return [chunk["text"] for chunk in data["scored_chunks"]]

    def create_system_prompt(self, chunk_texts: List[str]) -> str:
        """
        Create the system prompt with the retrieved chunks.
        """
        return f"""These are very important to follow: You are "Ragie AI", a professional but friendly AI chatbot working as an assistant to the user. Your current task is to help the user based on all of the information available to you shown below. Answer informally, directly, and concisely without a heading or greeting but include everything relevant. Use richtext Markdown when appropriate including bold, italic, paragraphs, and lists when helpful. If using LaTeX, use double $$ as delimiter instead of single $. Use $$...$$ instead of parentheses. Organize information into multiple sections or points when appropriate. Don't include raw item IDs or other raw fields from the source. Don't use XML or other markup unless requested by the user. Here is all of the information available to answer the user: === {chunk_texts} === If the user asked for a search and there are no results, make sure to let the user know that you couldn't find anything, and what they might be able to do to find the information they need. END SYSTEM INSTRUCTIONS"""

    def generate_response(self, system_prompt: str, query: str) -> str:
        """
        Generate response using Claude 3.5 Sonnet.
        """
        message = self.anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": query
                }
            ]
        )
        
        return message.content[0].text

    def process_query(self, query: str, scope: str = "tutorial") -> str:
        """
        Process a query through the complete RAG pipeline.
        """
        chunks = self.retrieve_chunks(query, scope)
        
        if not chunks:
            return "No relevant information found for your query."
        
        system_prompt = self.create_system_prompt(chunks)
        return self.generate_response(system_prompt, query)

def initialize_session_state():
    """Initialize session state variables."""
    if 'pipeline' not in st.session_state:
        st.session_state.pipeline = None
    if 'document_uploaded' not in st.session_state:
        st.session_state.document_uploaded = False
    if 'api_keys_submitted' not in st.session_state:
        st.session_state.api_keys_submitted = False

def main():
    st.set_page_config(page_title="RAG-as-a-Service", layout="wide")
    initialize_session_state()
    
    st.title(":linked_paperclips: RAG-as-a-Service")
    
    # API Keys Section
    with st.expander("🔑 API Keys Configuration", expanded=not st.session_state.api_keys_submitted):
        col1, col2 = st.columns(2)
        with col1:
            ragie_key = st.text_input("Ragie API Key", type="password", key="ragie_key")
        with col2:
            anthropic_key = st.text_input("Anthropic API Key", type="password", key="anthropic_key")
        
        if st.button("Submit API Keys"):
            if ragie_key and anthropic_key:
                try:
                    st.session_state.pipeline = RAGPipeline(ragie_key, anthropic_key)
                    st.session_state.api_keys_submitted = True
                    st.success("API keys configured successfully!")
                except Exception as e:
                    st.error(f"Error configuring API keys: {str(e)}")
            else:
                st.error("Please provide both API keys.")
    
    # Document Upload Section
    if st.session_state.api_keys_submitted:
        st.markdown("### 📄 Document Upload")
        doc_url = st.text_input("Enter document URL")
        doc_name = st.text_input("Document name (optional)")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            upload_mode = st.selectbox("Upload mode", ["fast", "accurate"])
        
        if st.button("Upload Document"):
            if doc_url:
                try:
                    with st.spinner("Uploading document..."):
                        st.session_state.pipeline.upload_document(
                            url=doc_url,
                            name=doc_name if doc_name else None,
                            mode=upload_mode
                        )
                        time.sleep(5)  # Wait for indexing
                        st.session_state.document_uploaded = True
                        st.success("Document uploaded and indexed successfully!")
                except Exception as e:
                    st.error(f"Error uploading document: {str(e)}")
            else:
                st.error("Please provide a document URL.")
    
    # Query Section
    if st.session_state.document_uploaded:
        st.markdown("### 🔍 Query Document")
        query = st.text_input("Enter your query")
        
        if st.button("Generate Response"):
            if query:
                try:
                    with st.spinner("Generating response..."):
                        response = st.session_state.pipeline.process_query(query)
                        st.markdown("### Response:")
                        st.markdown(response)
                except Exception as e:
                    st.error(f"Error generating response: {str(e)}")
            else:
                st.error("Please enter a query.")

if __name__ == "__main__":
    main()