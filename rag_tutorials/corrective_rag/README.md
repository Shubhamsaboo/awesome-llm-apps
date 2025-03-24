# 🔄 Corrective RAG Agent
A sophisticated Retrieval-Augmented Generation (RAG) system that implements a corrective multi-stage workflow using LangGraph. This system combines document retrieval, relevance grading, query transformation, and web search to provide comprehensive and accurate responses.

## Features

- **Smart Document Retrieval**: Uses Qdrant vector store for efficient document retrieval
- **Document Relevance Grading**: Employs Claude 3.5 sonnet to assess document relevance
- **Query Transformation**: Improves search results by optimizing queries when needed
- **Web Search Fallback**: Uses Tavily API for web search when local documents aren't sufficient
- **Multi-Model Approach**: Combines OpenAI embeddings and Claude 3.5 sonnet for different tasks
- **Interactive UI**: Built with Streamlit for easy document upload and querying

## How to Run?

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd rag_tutorials/corrective_rag
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up API Keys**:
   You'll need to obtain the following API keys:
   - [OpenAI API key](https://platform.openai.com/api-keys) (for embeddings)
   - [Anthropic API key](https://console.anthropic.com/settings/keys) (for Claude 3.5 sonnet as LLM)
   - [Tavily API key](https://app.tavily.com/home) (for web search)
   - Qdrant Cloud Setup
      1. Visit [Qdrant Cloud](https://cloud.qdrant.io/)
      2. Create an account or sign in
      3. Create a new cluster
      4. Get your credentials:
         - Qdrant API Key: Found in API Keys section
         - Qdrant URL: Your cluster URL (format: `https://xxx-xxx.aws.cloud.qdrant.io`)

4. **Run the Application**:
   ```bash
   streamlit run corrective_rag.py
   ```

5. **Use the Application**:
   - Upload documents or provide URLs
   - Enter your questions in the query box
   - View the step-by-step Corrective RAG process
   - Get comprehensive answers

## Tech Stack

- **LangChain**: For RAG orchestration and chains
- **LangGraph**: For workflow management
- **Qdrant**: Vector database for document storage
- **Claude 3.5 sonnet**: Main language model for analysis and generation
- **OpenAI**: For document embeddings
- **Tavily**: For web search capabilities
- **Streamlit**: For the user interface
