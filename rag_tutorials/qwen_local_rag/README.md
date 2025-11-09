# 🐋 Qwen 3 Local RAG Reasoning Agent

This RAG Application demonstrates how to build a powerful Retrieval-Augmented Generation (RAG) system using locally running Qwen 3 and Gemma 3 models via Ollama. It combines document processing, vector search, and web search capabilities to provide accurate, context-aware responses to user queries. Built with Agno v2.0.

## Features

- **🧠 Multiple Local LLM Options**:

  - Qwen3 (1.7b, 8b) - Alibaba's latest language models
  - Gemma3 (1b, 4b) - Google's efficient language models with multimodal capabilities
  - DeepSeek (1.5b) - Alternative model option
- **📚 Comprehensive RAG System**:

  - Upload and process PDF documents
  - Extract content from web URLs
  - Intelligent chunking and embedding
  - Similarity search with adjustable threshold
- **🌐 Web Search Integration**:

  - Fallback to web search when document knowledge is insufficient
  - Configurable domain filtering
  - Source attribution in responses
- **🔄 Flexible Operation Modes**:

  - Toggle between RAG and direct LLM interaction
  - Force web search when needed
  - Adjust similarity thresholds for document retrieval
- **💾 Vector Database Integration**:

  - Qdrant vector database for efficient similarity search
  - Persistent storage of document embeddings
- **🔧 Agno v2.0 Framework**:

  - Uses Agno v2.0 Knowledge embedder system
  - Debug mode for enhanced development experience
  - Modern agent architecture with improved tool integration

## How to Get Started

### Prerequisites

- [Ollama](https://ollama.ai/) installed locally
- Python 3.8+
- Qdrant running locally (via Docker) for vector storage
- Exa API key (optional, for web search capability)
- Agno v2.0 installed

### Installation

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd rag_tutorials/qwen_local_rag
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Pull the required models using Ollama:

```bash
ollama pull qwen3:1.7b # Or any other model you want to use
ollama pull snowflake-arctic-embed # For embeddings
```

4. Run Qdrant locally through Docker:

```bash
docker pull qdrant/qdrant

docker run -p 6333:6333 -p 6334:6334 \
    -v "$(pwd)/qdrant_storage:/qdrant/storage:z" \
    qdrant/qdrant
```

5. Get your API keys (optional):

   - Exa API key (for web search fallback capability)
   
6. Run the application:

```bash
streamlit run qwen_local_rag_agent.py
```

## How It Works

1. **Document Processing**:

   - PDF files are processed using PyPDFLoader
   - Web content is extracted using WebBaseLoader
   - Documents are split into chunks with RecursiveCharacterTextSplitter
   - Metadata is added to track source types and timestamps

2. **Vector Database**:

   - Document chunks are embedded using Ollama's embedding models via Agno's OllamaEmbedder
   - Embeddings are stored in Qdrant vector database
   - Similarity search retrieves relevant documents based on query with configurable threshold

3. **Query Processing**:

   - User queries are analyzed to determine the best information source
   - System checks document relevance using similarity threshold
   - Falls back to web search if no relevant documents are found (when enabled)
   - Supports forced web search mode via toggle

4. **Response Generation**:

   - Local LLM (Qwen/Gemma/DeepSeek) generates responses based on retrieved context
   - Agno agents use debug mode for enhanced visibility into tool calls
   - Sources are cited and displayed to the user
   - Web search results are clearly indicated when used
   - Reasoning process is displayed for reasoning models

## Configuration Options

- **Model Selection**: Choose between different Qwen, Gemma, and DeepSeek models
- **RAG Mode**: Toggle between RAG-enabled and direct LLM interaction
- **Search Tuning**: Adjust similarity threshold (0.0-1.0) for document retrieval
- **Web Search**: Enable/disable web search fallback and configure domain filtering
- **Debug Mode**: Agents use debug mode by default for better visibility into tool calls and execution flow

## Use Cases

- **Document Q&A**: Ask questions about your uploaded documents
- **Research Assistant**: Combine document knowledge with web search
- **Local Privacy**: Process sensitive documents without sending data to external APIs
- **Offline Operation**: Run advanced AI capabilities with limited or no internet access

## Requirements

See `requirements.txt` for the complete list of dependencies.
