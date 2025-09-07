## 🔥 Agentic RAG with EmbeddingGemma

This Streamlit app demonstrates an agentic Retrieval-Augmented Generation (RAG) Agent using Google's EmbeddingGemma for embeddings and Llama 3.2 as the language model, all running locally via Ollama.

### Features

- **Local AI Models**: Uses EmbeddingGemma for vector embeddings and Llama 3.2 for text generation
- **PDF Knowledge Base**: Dynamically add PDF URLs to build a knowledge base
- **Vector Search**: Efficient similarity search using LanceDB
- **Interactive UI**: Beautiful Streamlit interface for adding sources and querying
- **Streaming Responses**: Real-time response generation with tool call visibility

### How to Get Started?

1. Clone the GitHub repository
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/rag_tutorials/agentic_rag_embedding_gemma
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Ensure Ollama is installed and running with the required models:
   - Pull the models: `ollama pull embeddinggemma:latest` and `ollama pull llama3.2:latest`
   - Start Ollama server if not running

4. Run the Streamlit app:
```bash
streamlit run agentic_rag_embeddinggemma.py
```
   (Note: The app file is in the root directory)

5. Open your web browser to the URL provided (usually http://localhost:8501) to interact with the RAG agent.

### How It Works?

1. **Knowledge Base Setup**: Add PDF URLs in the sidebar to load and index documents.
2. **Embedding Generation**: EmbeddingGemma creates vector embeddings for semantic search.
3. **Query Processing**: User queries are embedded and searched against the knowledge base.
4. **Response Generation**: Llama 3.2 generates answers based on retrieved context.
5. **Tool Integration**: The agent uses search tools to fetch relevant information.

### Requirements

- Python 3.8+
- Ollama installed and running
- Required models: `embeddinggemma:latest`, `llama3.2:latest`

### Technologies Used

- **Agno**: Framework for building AI agents
- **Streamlit**: Web app framework
- **LanceDB**: Vector database
- **Ollama**: Local LLM server
- **EmbeddingGemma**: Google's embedding model
- **Llama 3.2**: Meta's language model
