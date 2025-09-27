## 🦙 Local RAG Agent with Llama 3.2
This application implements a Retrieval-Augmented Generation (RAG) system using Llama 3.2 via Ollama, with Qdrant as the vector database.


### Features
- Fully local RAG implementation
- Powered by Llama 3.2 through Ollama
- Vector search using Qdrant
- Interactive playground interface
- No external API dependencies

### How to get Started?

1. Clone the GitHub repository
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
```

2. Install the required dependencies:

```bash
cd awesome-llm-apps/rag_tutorials/local_rag_agent
pip install -r requirements.txt
```

3. Install and start [Qdrant](https://qdrant.tech/) vector database locally

```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 qdrant/qdrant
```

4. Install [Ollama](https://ollama.com/download) and pull Llama 3.2 for LLM and OpenHermes as the embedder for OllamaEmbedder
```bash
ollama pull llama3.2
ollama pull openhermes
```

4. Run the AI RAG Agent 
```bash
python local_rag_agent.py
```

5. Open your web browser and navigate to the URL provided in the console output to interact with the RAG agent through the playground interface.


