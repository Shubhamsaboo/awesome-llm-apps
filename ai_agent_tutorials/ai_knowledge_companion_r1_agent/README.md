# Deepseek r1 Knowledge Agent 🤔

A versatile knowledge companion built with Deepseek r1 (via Ollama), Gemini for embeddings, Qdrant for vector storage, and Agno for agent orchestration. This application features dual-mode operation - a simple chat mode using local Deepseek r1 and an advanced RAG mode with document processing and web search capabilities.

## Features

- **Dual Operation Modes**
  - Simple Chat Mode: Direct interaction with Deepseek r1 locally
  - RAG Mode: Enhanced responses with document context and web search

- **Document Processing** (RAG Mode)
  - PDF document upload and processing
  - Web page content extraction
  - Automatic text chunking
  - Vector storage in Qdrant cloud

- **Intelligent Querying** (RAG Mode)
  - Query rewriting using Gemini
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
  - Gemini Embedding model for vector embeddings
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
```

### 2. Google API Key (for RAG Mode)
1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign up or log in to your account
3. Create a new API key

### 3. Qdrant Cloud Setup (for RAG Mode)
1. Visit [Qdrant Cloud](https://cloud.qdrant.io/)
2. Create an account or sign in
3. Create a new cluster
4. Get your credentials:
   - Qdrant API Key: Found in API Keys section
   - Qdrant URL: Your cluster URL (format: `https://xxx-xxx.cloud.qdrant.io`)

### 4. Exa AI API Key (Optional)
1. Visit [Exa AI](https://exa.ai)
2. Sign up for an account
3. Generate an API key for web search capabilities

## How to Run

1. Clone the repository:
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd ai_agent_tutorials/ai_knowledge_companion_r1_agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run ai_knowledge_r1_agent.py
```

