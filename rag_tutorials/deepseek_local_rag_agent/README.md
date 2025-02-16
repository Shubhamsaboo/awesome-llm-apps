# 🐋 Deepseek Local RAG Reasoning Agent 

A powerful reasoning agent that combines local Deepseek models with RAG capabilities. Built using Deepseek (via Ollama), Snowflake for embeddings, Qdrant for vector storage, and Agno for agent orchestration, this application offers both simple local chat and advanced RAG-enhanced interactions with comprehensive document processing and web search capabilities.

## Features

- **Dual Operation Modes**
  - Local Chat Mode: Direct interaction with Deepseek locally
  - RAG Mode: Enhanced reasoning with document context and web search integration - llama3.2

- **Document Processing** (RAG Mode)
  - PDF document upload and processing
  - Web page content extraction
  - Automatic text chunking and embedding
  - Vector storage in Qdrant cloud

- **Intelligent Querying** (RAG Mode)
  - RAG-based document retrieval
  - Similarity search with threshold filtering
  - Automatic fallback to web search
  - Source attribution for answers

- **Advanced Capabilities**
  - Exa AI web search integration
  - Custom domain filtering for web search
  - Context-aware response generation
  - Chat history management
  - Thinking process visualization

- **Model Specific Features**
  - Flexible model selection:
    - Deepseek r1 1.5b (lighter, suitable for most laptops)
    - Deepseek r1 7b (more capable, requires better hardware)
  - Snowflake Arctic Embedding model (SOTA) for vector embeddings
  - Agno Agent framework for orchestration
  - Streamlit-based interactive interface

## Prerequisites

### 1. Ollama Setup
1. Install [Ollama](https://ollama.ai)
2. Pull the Deepseek r1 model(s):
```bash
# For the lighter model
ollama pull deepseek-r1:1.5b

# For the more capable model (if your hardware supports it)
ollama pull deepseek-r1:7b

ollama pull snowflake-arctic-embed
ollama pull llama3.2
```

### 2. Qdrant Cloud Setup (for RAG Mode)
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
cd rag_tutorials/deepseek_local_rag_agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run deepseek_rag_agent.py
```

