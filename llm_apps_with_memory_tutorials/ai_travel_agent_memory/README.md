## 🧳 AI Travel Agent with Memory
This Streamlit app implements an AI-powered travel assistant that remembers user preferences and past interactions. It utilizes OpenAI's GPT-4o for generating responses and Mem0 with Qdrant for maintaining conversation history.

### Features
- Chat-based interface for interacting with an AI travel assistant
- Persistent memory of user preferences and past conversations
- Utilizes OpenAI's GPT-4o model for intelligent responses
- Implements memory storage and retrieval using Mem0 and Qdrant
- User-specific conversation history and memory viewing

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

docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant
```

4. Run the Streamlit App
```bash
streamlit run travel_agent_memory.py
```
