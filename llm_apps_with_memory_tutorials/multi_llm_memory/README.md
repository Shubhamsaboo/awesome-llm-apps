## 🧠 Multi-LLM App with Shared Memory
This Streamlit application demonstrates a multi-LLM system with a shared memory layer, allowing users to interact with different language models while maintaining conversation history and context across sessions.

### Features

- Support for multiple LLMs:
    - OpenAI's GPT-4o
    - Anthropic's Claude 3.5 Sonnet

- Persistent memory using Qdrant vector store
- User-specific conversation history
- Memory retrieval for contextual responses
- User-friendly interface with LLM selection

### How to get Started?

1. Clone the GitHub repository
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Ensure Qdrant is running:
The app expects Qdrant to be running on localhost:6333. Adjust the configuration in the code if your setup is different.

```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 qdrant/qdrant
```

4. Run the Streamlit App
```bash
streamlit run multi_llm_memory.py
```