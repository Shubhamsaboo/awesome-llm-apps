# 👀 RAG App with Hybrid Search 

A powerful document Q&A application that leverages Hybrid Search (RAG) and Claude's advanced language capabilities to provide comprehensive answers. Built with RAGLite for robust document processing and retrieval, and Streamlit for an intuitive chat interface, this system seamlessly combines document-specific knowledge with Claude's general intelligence to deliver accurate and contextual responses.

## Demo video:


https://github.com/user-attachments/assets/b576bf6e-4a48-4a43-9600-48bcc8f359a5


## Features

- **Hybrid Search Question Answering**
    - RAG-based answers for document-specific queries
    - Fallback to Claude for general knowledge questions

- **Document Processing**:
  - PDF document upload and processing
  - Automatic text chunking and embedding
  - Hybrid search combining semantic and keyword matching
  - Reranking for better context selection

- **Multi-Model Integration**:
  - Claude for text generation - tested with Claude 3 Opus 
  - OpenAI for embeddings - tested with text-embedding-3-large
  - Cohere for reranking - tested with Cohere 3.5 reranker

## Prerequisites

You'll need the following API keys and database setup:

1. **Database**: Create a free PostgreSQL database at [Neon](https://neon.tech):
   - Sign up/Login at Neon
   - Create a new project
   - Copy the connection string (looks like: `postgresql://user:pass@ep-xyz.region.aws.neon.tech/dbname`)

2. **API Keys**:
   - [OpenAI API key](https://platform.openai.com/api-keys) for embeddings
   - [Anthropic API key](https://console.anthropic.com/settings/keys) for Claude
   - [Cohere API key](https://dashboard.cohere.com/api-keys) for reranking

## How to get Started?

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd rag_tutorials/hybrid_search_rag
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install spaCy Model**:
   ```bash
   pip install https://github.com/explosion/spacy-models/releases/download/xx_sent_ud_sm-3.7.0/xx_sent_ud_sm-3.7.0-py3-none-any.whl
   ```

4. **Run the Application**:
   ```bash
   streamlit run main.py
   ```

## Usage

1. Start the application
2. Enter your API keys in the sidebar:
   - OpenAI API key
   - Anthropic API key
   - Cohere API key
   - Database URL (optional, defaults to SQLite)
3. Click "Save Configuration"
4. Upload PDF documents
5. Start asking questions!
   - Document-specific questions will use RAG
   - General questions will use Claude directly

## Database Options

The application supports multiple database backends:

- **PostgreSQL** (Recommended):
  - Create a free serverless PostgreSQL database at [Neon](https://neon.tech)
  - Get instant provisioning and scale-to-zero capability
  - Connection string format: `postgresql://user:pass@ep-xyz.region.aws.neon.tech/dbname`

- **MySQL**:
  ```
  mysql://user:pass@host:port/db
  ```
- **SQLite** (Local development):
  ```
  sqlite:///path/to/db.sqlite
  ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
