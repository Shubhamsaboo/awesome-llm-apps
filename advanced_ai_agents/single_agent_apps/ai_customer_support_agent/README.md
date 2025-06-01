## 🛒 AI Customer Support Agent with Memory
This Streamlit app implements an AI-powered customer support agent for synthetic data generated using GPT-4o. The agent uses OpenAI's GPT-4o model and maintains a memory of past interactions using the Mem0 library with Qdrant as the vector store.

### Features

- Chat interface for interacting with the AI customer support agent
- Persistent memory of customer interactions and profiles
- Synthetic data generation for testing and demonstration
- Utilizes OpenAI's GPT-4o model for intelligent responses

### How to get Started?

1. Clone the GitHub repository
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/single_agent_apps/ai_customer_support_agent
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
    -v "$(pwd)/qdrant_storage:/qdrant/storage:z" \
    qdrant/qdrant
```

4. Run the Streamlit App
```bash
streamlit run customer_support_agent.py
```
