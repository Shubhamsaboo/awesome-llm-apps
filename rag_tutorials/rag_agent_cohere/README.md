# RAG Agent with Cohere ⌘R 

A RAG Agentic system built with Cohere's new model Command-r7b-12-2024, Qdrant for vector storage, Langchain for RAG and LangGraph for orchestration. This application allows users to upload documents, ask questions about them, and get AI-powered responses with fallback to web search when needed.

## Features

- **Document Processing**
  - PDF document upload and processing
  - Automatic text chunking and embedding
  - Vector storage in Qdrant cloud

- **Intelligent Querying**
  - RAG-based document retrieval
  - Similarity search with threshold filtering
  - Automatic fallback to web search when no relevant documents found
  - Source attribution for answers

- **Advanced Capabilities**
  - DuckDuckGo web search integration
  - LangGraph agent for web research
  - Context-aware response generation
  - Long answer summarization

- **Model Specific Features**
  - Command-r7b-12-2024 model for Chat and RAG
  - cohere embed-english-v3.0 model for embeddings
  - create_react_agent function from langgraph 
  - DuckDuckGoSearchRun tool for web search

## Prerequisites

### 1. Cohere API Key
1. Go to [Cohere Platform](https://dashboard.cohere.ai/api-keys)
2. Sign up or log in to your account
3. Navigate to API Keys section
4. Create a new API key

### 2. Qdrant Cloud Setup
1. Visit [Qdrant Cloud](https://cloud.qdrant.io/)
2. Create an account or sign in
3. Create a new cluster
4. Get your credentials:
   - Qdrant API Key: Found in API Keys section
   - Qdrant URL: Your cluster URL (format: `https://xxx-xxx.aws.cloud.qdrant.io`)


## How to Run

1. Clone the repository:
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd rag_tutorials/rag_agent_cohere
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

```bash
streamlit run rag_agent_cohere.py
```


