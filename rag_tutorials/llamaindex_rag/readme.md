
#  RAG Knowledge Assistant

### Qdrant + HuggingFace + Groq + LlamaIndex

---

##  Overview

This repository implements a **Retrieval-Augmented Generation (RAG) pipeline** that allows users to build AI assistants powered by custom knowledge bases.

The system enables:

* Document ingestion into a vector database
* Semantic search over stored knowledge
* Natural language question answering using LLMs

The project is designed to be **simple, modular, and beginner-friendly** while remaining scalable for production use.

---

##  How It Works

The system is divided into two main pipelines:

###  Document Ingestion Pipeline

Processes raw documents and stores them as vector embeddings.

```
Documents → Chunking → Embeddings → Qdrant Vector Storage
```

---

###  Query Answering Pipeline

Retrieves relevant knowledge and generates answers.

```
User Query → Vector Search → Context Retrieval → LLM Response
```

---

##  Tech Stack

| Component       | Technology                |
| --------------- | ------------------------- |
| RAG Framework   | LlamaIndex                |
| Vector Database | Qdrant Cloud              |
| Embedding Model | HuggingFace Inference API |
| LLM Provider    | Groq                      |
| Language        | Python                    |

---

##  Repository Structure

```
project/
│
├── ingestion.py          # Document ingestion pipeline
├── query_pipeline.py     # Query answering pipeline
├── data/                 # Place input documents here
├── requirements.txt
├── .env                  # API keys & configuration
└── README.md
```

---

##  Setup Guide

---

###  Clone Repository

```bash
git clone <your-repository-url>
cd <project-folder>
```

---

###  Install Dependencies

```bash
pip install -r requirements.txt
```

---

###  Create Environment File

Create `.env` in project root:

```
QDRANT_URL=your_qdrant_cluster_url
QDRANT_API_KEY=your_qdrant_api_key
HF_API_KEY=your_huggingface_api_key
GROQ_API_KEY=your_groq_api_key
```

---

###  Prepare Documents

Place knowledge files inside:

```
data/
```

Supported formats:

* PDF
* DOCX
* TXT
* HTML
* Markdown

---

##  Quick Start

---

### Step 1 — Run Document Ingestion

```bash
python ingestion.py
```

This will:

* Load documents
* Generate embeddings
* Store vectors in Qdrant Cloud

---

### Step 2 — Start Query System

```bash
python query_pipeline.py
```

You can now ask questions interactively.

---

##  Example Usage

---

### Ingest Documents Programmatically

```python
from ingestion import DocumentIngestionPipeline

pipeline = DocumentIngestionPipeline()
pipeline.run()
```

---

### Query Knowledge Base

```python
from query_pipeline import QueryAnsweringPipeline

pipeline = QueryAnsweringPipeline()
response = pipeline.query("Your question here")
print(response)
```

---

##  Required Accounts

You need:

* Qdrant Cloud → [https://cloud.qdrant.io](https://cloud.qdrant.io)
* HuggingFace → [https://huggingface.co](https://huggingface.co)
* Groq → [https://console.groq.com](https://console.groq.com)

---
