# Hybrid RAG Claude Chat 🤖

A powerful document Q&A application that combines Hybrid Search (RAG) with Claude's general knowledge. This is built on the RAGLite framework and Chainlit for the UI. 

## Features

- **Hybrid Question Answering**
    - RAG-based answers for document-specific queries
    - Fallback to Claude for general knowledge questions
    - Seamless switching between modes

- **Document Processing**:
  - PDF document upload and processing
  - Automatic text chunking and embedding
  - Hybrid search combining semantic and keyword matching
  - Reranking for better context selection

- **Interactive Chat Interface**:
  - Real-time streaming responses
  - Chat history preservation
  - Error handling with retry options
  - File upload validation

- **Multi-Model Integration**:
  - Claude for text generation
  - OpenAI for embeddings
  - Cohere for reranking (tried using the new Cohere 3.5 reranker)

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

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd rag_tutorials/llm_app_hybrid_RAG_claude
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
   chainlit run main.py
   ```

## Usage

1. Start the application
2. When prompted, enter your:
   - OpenAI API key
   - Anthropic API key
   - Cohere API key
   - Neon PostgreSQL URL
3. Upload PDF documents
4. Start asking questions!
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
