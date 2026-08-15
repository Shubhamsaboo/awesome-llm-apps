## 🧠 Local ChatGPT using Llama 3.1 with Personal Memory
This Streamlit application implements a fully local ChatGPT-like experience using Llama 3.1, featuring personalized memory storage for each user. All components, including the language model, embeddings, and vector store, run locally without requiring external API keys.

### Features
- Fully local implementation with no external API dependencies
- Powered by Llama 3.1 via Ollama
- Personal memory space for each user
- Local embedding generation using Nomic Embed
- Vector storage with Qdrant

### How to get Started?

1. Clone the GitHub repository
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Install and start [Qdrant](https://qdrant.tech/documentation/guides/installation/) vector database locally

```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 qdrant/qdrant
```

4. Install [Ollama](https://ollama.com/download) and pull Llama 3.1
```bash
ollama pull llama3.1
```

> Using AMD Strix Halo / Ryzen AI MAX+ 395? The [AMD Strix Halo Local LLM Guide](https://github.com/hogeheer499-commits/strix-halo-guide) documents a tested Ubuntu and Ollama Vulkan/RADV setup, model and quantization choices, benchmark evidence, and known failed routes for this hardware.

5. Run the Streamlit App
```bash
streamlit run local_chatgpt_memory.py
```
