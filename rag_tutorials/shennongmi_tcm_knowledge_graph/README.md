# 🌿 ShenNongMi — TCM Knowledge Graph RAG

> Traditional Chinese Medicine Q&A powered by **Neo4j** + **LangGraph** + **DeepSeek LLM**

A self-contained knowledge-graph RAG tutorial that demonstrates how to combine a
structured graph database with LLM-powered query generation. The app extracts
TCM entities from user questions, matches them against a Neo4j knowledge graph
via FAISS vector search, generates Cypher queries, validates and executes them,
and returns natural-language answers.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.x-4581C3?logo=neo4j)](https://neo4j.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-workflow-orange)](https://langchain-ai.github.io/langgraph/)
[![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek-4B70B3)](https://www.deepseek.com/)
[![Streamlit](https://img.shields.io/badge/frontend-Streamlit-FF4B4B?logo=streamlit)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)

---

## How It Works

```
User Question
     │
     ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Intent Classifier│───▶│  Entity Extraction│───▶│  FAISS Matching │
│ (RoBERTa+LoRA)  │    │      (LLM)        │    │ (BGE-Large-Zh)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Natural Answer │◀───│  Cypher Execution│◀───│ Cypher Generation│
│     (LLM)       │    │     (Neo4j)      │    │ (LLM + Validate) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

1. **Intent Classification** — A fine-tuned RoBERTa+LoRA model determines if the query is TCM-related
2. **Entity Extraction** — The LLM extracts symptoms, herbs, formulas, effects, diseases from the user input
3. **FAISS Matching** — Extracted entities are matched against the Neo4j knowledge graph via vector similarity (BGE-Large-Zh-v1.5 embeddings)
4. **Cypher Generation** — The LLM generates Neo4j Cypher queries based on matched entities and the graph schema
5. **Validation Loop** — Cypher syntax is validated; invalid queries loop back for LLM self-correction (up to 3 retries)
6. **Execution + Answer** — Valid queries run against Neo4j, results are synthesized into a natural-language answer

---

## Quick Start

### Prerequisites

- **Python** >= 3.10
- **Neo4j** >= 5.x ([Download](https://neo4j.com/download/))
- A DeepSeek API key (or any OpenAI-compatible endpoint)

### 1. Clone & Install

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/rag_tutorials/shennongmi_tcm_knowledge_graph
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

| Variable | Description |
|----------|-------------|
| `MODEL_API_KEY` | Your LLM API key |
| `MODEL_BASE_URL` | API endpoint (default: `https://api.deepseek.com`) |
| `MODEL_NAME` | Model name (e.g. `deepseek-chat`, `gpt-4o`) |
| `NEO4J_URI` | Neo4j bolt URI (default: `bolt://localhost:7687`) |
| `NEO4J_USER` | Neo4j username (default: `neo4j`) |
| `NEO4J_PASSWORD` | Neo4j password |
| `EMBEDDING_MODEL_PATH` | Local embedding model path (leave empty to auto-download) |

### 3. Set Up the Knowledge Graph

The project includes sample TCM graph schema metadata (`kg_setup/tcm_metadata.json`).
To build a full knowledge graph from scratch, you need extracted TCM data in JSON format:

```bash
# Place your extracted data files in kg_data/ (create if needed):
#   kg_data/extract_formula_data.json
#   kg_data/extract_herb_data.json

# Then import into Neo4j
python kg_setup/graph_importer.py

# Build FAISS vector index for entity matching
python kg_setup/faiss_embedding.py
```

> **Note**: The knowledge graph data pipeline (web crawling + LLM extraction) is
> not included in this tutorial. See the [standalone ShenNongMi repo](https://github.com/Happy-Chen-CH/ShenNongMi)
> for the full data preparation pipeline. You can also use any TCM data source
> that conforms to the schema in `kg_setup/tcm_metadata.json`.

### 4. Run

```bash
# Terminal 1: Start FastAPI backend
python fastapi_app/main.py

# Terminal 2: Start Streamlit frontend
streamlit run streamlit_app/app.py
```

Open **http://localhost:8501** and ask TCM questions like:
- "四君子汤由哪些药材组成？"
- "人参有什么功效和禁忌？"
- "治疗风寒感冒有哪些方剂？"

---

## Project Structure

```
shennongmi_tcm_knowledge_graph/
├── common/                     # Shared modules
│   ├── config.py               # Environment config (LLM, Neo4j, FAISS)
│   ├── llm.py                  # LLM wrapper (DeepSeek via LangChain)
│   ├── neo4j_manager.py        # Neo4j client
│   └── embedding_model.py      # BGE text embeddings
│
├── kg_setup/                   # Knowledge graph setup
│   ├── graph_importer.py       # Neo4j data import
│   ├── faiss_embedding.py      # FAISS vector index builder
│   └── tcm_metadata.json       # Graph schema metadata
│
├── langgraph_workflow/         # LangGraph workflow
│   ├── langgraph_more_nodes.py # Graph definition + compilation
│   ├── agent_state.py          # State definitions
│   ├── tcm_predictor.py        # RoBERTa+LoRA intent classifier
│   └── node/                   # Workflow nodes
│       ├── zhongyi_intent_node.py                  # TCM intent
│       ├── extract_entity_from_user_input_node.py  # Entity extraction
│       ├── match_entity_from_neo4j_node.py         # FAISS matching
│       ├── generate_neo4j_cypher_node.py           # Cypher generation
│       ├── check_cypher_node.py                    # Cypher validation
│       ├── run_cypher_node.py                      # Cypher execution
│       ├── neo4j_answer_generate_node.py           # Answer generation
│       └── llm_direct_out_node.py                  # Non-TCM fallback
│
├── fastapi_app/                # FastAPI backend
│   └── main.py                 # REST API with SSE streaming
│
├── streamlit_app/              # Streamlit frontend
│   ├── app.py                  # Home page
│   ├── pages/                  # Multi-page app
│   │   ├── 01_TCM_Q&A.py      # Knowledge Q&A
│   │   └── 02_KG_Explorer.py  # Graph browser
│   └── utils/
│       ├── api.py              # FastAPI client
│       └── style.py            # Styling
│
├── requirements.txt
├── .env.example
└── LICENSE
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit (multi-page) |
| Backend | FastAPI (SSE streaming) |
| Workflow | LangGraph |
| LLM | DeepSeek (OpenAI-compatible) |
| Graph DB | Neo4j 5.x |
| Vector Search | FAISS + BGE-Large-Zh-v1.5 |
| Intent Recognition | RoBERTa + LoRA (fine-tuned) |
| Embeddings | Sentence-Transformers |

---

## Key Design Decisions

**Why Cypher generation instead of pure vector RAG?**
Vector search alone can't answer questions like "What herbs treat both headache and fever?". A knowledge graph with structured Cypher queries enables multi-hop reasoning across entity relationships.

**Why a local RoBERTa model for intent classification?**
Faster (milliseconds), cheaper (zero API cost), and more accurate (fine-tuned on 4,000 labeled TCM queries) than prompting an LLM per request.

**Self-correction loop for Cypher**
LLM-generated Cypher is validated before execution. Invalid queries loop back to the generator with error feedback, preventing runtime failures and improving reliability.

---

## License

Apache-2.0 — see [LICENSE](LICENSE).

## Disclaimer

This project is for **educational and research purposes only**. The TCM knowledge
in the graph comes from publicly available sources and does **not** constitute
medical advice. Consult a licensed healthcare professional for health concerns.

---

*Part of [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) — a curated collection of runnable LLM applications.*
