# 🤔 Agentic RAG with Gemini Flash Thinking

A RAG Agentic system built with the new Gemini 2.0 Flash Thinking model and gemini-exp-1206, Qdrant for vector storage, and Agno (phidata prev) for agent orchestration. This application features intelligent query rewriting, document processing, and web search fallback capabilities to provide comprehensive AI-powered responses.

## Features

- **Document Processing**
  - PDF document upload and processing
  - Web page content extraction
  - Automatic text chunking and embedding
  - Vector storage in Qdrant cloud

- **Intelligent Querying**
  - Query rewriting for better retrieval
  - RAG-based document retrieval
  - Similarity search with threshold filtering
  - Automatic fallback to web search
  - Source attribution for answers

- **Advanced Capabilities**
  - Exa AI web search integration
  - Custom domain filtering for web search
  - Context-aware response generation
  - Chat history management
  - Query reformulation agent

- **Model Specific Features**
  - Gemini Thinking 2.0 Flash for chat and reasoning
  - Gemini Embedding model for vector embeddings
  - Agno Agent framework for orchestration
  - Streamlit-based interactive interface

## Prerequisites

### 1. Google API Key
1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign up or log in to your account
3. Create a new API key

### 2. Qdrant Cloud Setup
1. Visit [Qdrant Cloud](https://cloud.qdrant.io/)
2. Create an account or sign in
3. Create a new cluster
4. Get your credentials:
   - Qdrant API Key: Found in API Keys section
   - Qdrant URL: Your cluster URL (format: `https://xxx-xxx.cloud.qdrant.io`)

### 3. Exa AI API Key (Optional)
1. Visit [Exa AI](https://exa.ai)
2. Sign up for an account
3. Generate an API key for web search capabilities

## How to Run

1. Clone the repository:
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd rag_tutorials/gemini_agentic_rag
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run agentic_rag_gemini.py
```

## Usage

1. Configure API keys in the sidebar:
   - Enter your Google API key
   - Add Qdrant credentials
   - (Optional) Add Exa AI key for web search

2. Upload documents:
   - Use the file uploader for PDFs
   - Enter URLs for web content

3. Ask questions:
   - Type your query in the chat interface
   - View rewritten queries and sources
   - See web search results when relevant

4. Manage your session:
   - Clear chat history as needed
   - Configure web search domains
   - Monitor processed documents
