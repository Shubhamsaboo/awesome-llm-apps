## 🖇️ RAG-as-a-Service with Claude 3.5 Sonnet
Build and deploy a production-ready Retrieval-Augmented Generation (RAG) service using Claude 3.5 Sonnet and Ragie.ai. This implementation allows you to create a document querying system with a user-friendly Streamlit interface in less than 50 lines of Python code.

### Features
- Production-ready RAG pipeline
- Integration with Claude 3.5 Sonnet for response generation
- Document upload from URLs
- Real-time document querying
- Support for both fast and accurate document processing modes

### How to get Started?

1. Clone the GitHub repository
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/rag_tutorials/rag-as-a-service
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Get your Anthropic API and Ragie API Key

- Sign up for an [Anthropic account](https://console.anthropic.com/) and get your API key
- Sign up for an [Ragie account](https://www.ragie.ai/) and get your API key

4. Run the Streamlit app
```bash
streamlit run rag_app.py
```