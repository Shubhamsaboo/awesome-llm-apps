## 🗃️ AI RAG Agent with Web Access 
This script demonstrates how to build a Retrieval-Augmented Generation (RAG) agent with web access using GPT-4o in just 15 lines of Python code. The agent uses a PDF knowledge base and has the ability to search the web using DuckDuckGo.

### Features

- Creates a RAG agent using GPT-4o
- Incorporates a PDF-based knowledge base
- Uses LanceDB as the vector database for efficient similarity search
- Includes web search capability through DuckDuckGo
- Provides a playground interface for easy interaction

### How to get Started?

1. Clone the GitHub repository
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/rag_tutorials/agentic_rag
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Get your OpenAI API Key

- Sign up for an [OpenAI account](https://platform.openai.com/) (or the LLM provider of your choice) and obtain your API key.
- Set your OpenAI API key as an environment variable:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

4. Run the AI RAG Agent 
```bash
python3 rag_agent.py
```
5. Open your web browser and navigate to the URL provided in the console output to interact with the RAG agent through the playground interface.

### How it works?

1. **Knowledge Base Creation:** The script creates a knowledge base from a PDF file hosted online.
2. **Vector Database Setup:** LanceDB is used as the vector database for efficient similarity search within the knowledge base.
3. **Agent Configuration:** An AI agent is created using GPT-4o as the underlying model, with the PDF knowledge base and DuckDuckGo search tool.
4. **Playground Setup:** A playground interface is set up for easy interaction with the RAG agent.

