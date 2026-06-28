# Amazon Bedrock PDF RAG Agent

A RAG-powered PDF chatbot using **Amazon Bedrock (Claude 3 Haiku)** and **FAISS** for semantic search with page-level citations. Sub-2s response time with local embeddings via sentence-transformers — no embedding API costs.

## Features

- Upload any PDF and chat with it using natural language
- Every answer cites the exact page it came from
- Local embeddings (sentence-transformers) — no embedding API cost on uploads
- Multi-turn Q&A with session isolation for multiple simultaneous users
- FastAPI backend + Streamlit UI + Docker ready

## How to get Started?

**Prerequisites:** Python 3.11+, AWS account with Amazon Bedrock enabled, IAM user with `bedrock:InvokeModel` permission, Claude 3 Haiku enabled in your region.

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
```

2. Install the required dependencies:

```bash
cd awesome-llm-apps/rag_tutorials/bedrock_pdf_rag
pip install -r requirements.txt
```

3. Set up your AWS credentials:

```bash
cp .env.example .env
# Edit .env and fill in:
# AWS_ACCESS_KEY_ID=your_key
# AWS_SECRET_ACCESS_KEY=your_secret
# AWS_REGION=us-east-1
```

4. Run the RAG agent:

```bash
# Terminal 1 — API server
uvicorn rag_agent:app --reload

# Terminal 2 — Streamlit UI
streamlit run streamlit_app.py
```

5. Open `http://localhost:8501`, upload a PDF, and ask questions in plain English.

## Architecture

```
PDF Upload → pypdf (text extraction) → Chunker (500 chars, 50 overlap)
→ sentence-transformers (local embed) → FAISS Index (in-memory)

User Query → sentence-transformers (embed) → FAISS similarity search
→ Top-K chunks → Amazon Bedrock (Claude 3 Haiku) → Answer + Page Citations
```

## Tech Stack

| Component | Technology |
|---|---|
| LLM | Amazon Bedrock (Claude 3 Haiku) |
| Embeddings | sentence-transformers all-MiniLM-L6-v2 (local) |
| Vector Store | FAISS (in-memory) |
| API | FastAPI + uvicorn |
| Frontend | Streamlit |
| PDF Parsing | pypdf |

## API Reference

```bash
# Upload a PDF
curl -X POST http://localhost:8000/upload -F "file=@document.pdf"
# returns: { "session_id": "abc123" }

# Ask a question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"session_id": "abc123", "question": "What is the main topic?"}'
```
