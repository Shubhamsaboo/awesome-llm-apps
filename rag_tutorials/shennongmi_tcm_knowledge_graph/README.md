# 🌿 ShennongMi

> Shennong觅 (*Shénnóng mì* — "The Divine Farmer Seeks") — AI-Powered Traditional Chinese Medicine Knowledge Navigator

A comprehensive Traditional Chinese Medicine (TCM) knowledge platform that combines **Neo4j Knowledge Graph** + **LangGraph Intelligent Workflows** + **DeepSeek LLM** + **fastText** + **LoRA Fine-tuning**. It delivers TCM knowledge Q&A, automated RED (Xiaohongshu) content generation & publishing, and interactive knowledge graph exploration.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![uv](https://img.shields.io/badge/uv-package%20manager-blueviolet)](https://docs.astral.sh/uv/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.x-4581C3?logo=neo4j)](https://neo4j.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-workflow-orange)](https://langchain-ai.github.io/langgraph/)
[![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek%20v4-4B70B3)](https://www.deepseek.com/)
[![Streamlit](https://img.shields.io/badge/frontend-Streamlit-FF4B4B?logo=streamlit)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)

---

## 📑 Table of Contents

- [✨ Features](#-features)
- [📸 Demo](#-demo)
- [🏗️ System Architecture](#️-system-architecture)
- [📂 Project Structure](#-project-structure)
- [🚀 Quick Start](#-quick-start)
- [🧪 Running Tests](#-running-tests)
- [🛠️ Tech Stack](#️-tech-stack)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [⚠️ Disclaimer](#️-disclaimer)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 💬 **TCM Knowledge Q&A** | Neo4j knowledge graph + LangGraph workflows for accurate answers about herbal formulas, medicinal herbs, symptoms, efficacy, diseases, and classical TCM texts |
| 📝 **RED Content Generator** | AI-powered TCM wellness content creation with Jimeng AI image generation and Playwright-based browser automation for one-click publishing to Xiaohongshu (RED) |
| 🔍 **Knowledge Graph Explorer** | Interactive browsing of 6 entity types and 6 relationship types in the TCM knowledge network |
| 🧠 **Intelligent Intent Recognition** | Fine-tuned RoBERTa + fastText dual-model architecture for precise user intent classification |

---

## 📸 Demo

| TCM Knowledge Q&A | RED Content Generator | Knowledge Graph Explorer |
|:---:|:---:|:---:|
| ![TCM Q&A](picture/20260724151933吃荔枝有什.png) | ![RED Generator](picture/20260724172933枸杞养生全.png) | ![KG Explorer](picture/20260729211254枸杞养生茶，喝出好气.png) |

---

## 🏗️ System Architecture

```
                              ┌──────────────┐
                              │  User Input   │
                              └──────┬───────┘
                                     │
                                     ▼
              ┌────────────────────────────────────────────┐
              │          LangGraph Workflow Engine          │
              │                                            │
              │  ┌──────────────────┐  ┌───────────────┐  │
              │  │  RED Publishing  │  │  TCM Q&A      │  │
              │  │  Pipeline        │  │  Pipeline     │  │
              │  │                  │  │               │  │
              │  │  ① Intent Recog  │  │  ① Intent Recog│  │
              │  │   ↓             │  │   ↓           │  │
              │  │  ② Content Gen   │  │  ② Entity Extr │  │
              │  │   ↓             │  │   ↓           │  │
              │  │  ③ AI Image Gen  │  │  ③ FAISS Match │  │
              │  │   ↓             │  │   ↓           │  │
              │  │  ④ Content Check │  │  ④ Cypher Gen  │  │
              │  │   ↓             │  │   ↓           │  │
              │  │  ⑤ Auto Publish  │  │  ⑤ KG Query    │  │
              │  │   ↓             │  │   ↓           │  │
              │  │  ⑥ Result Output │  │  ⑥ Answer Gen  │  │
              │  └──────────────────┘  └───────────────┘  │
              │                                            │
              └────────────────────┬───────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
          ┌──────────────────┐         ┌──────────────────┐
          │  Streamlit UI    │         │  FastAPI Backend  │
          │  (Port 8501)     │◄───────►│  (SSE Streaming)  │
          └──────────────────┘         └──────────────────┘
```

---

## 📂 Project Structure

```
ShenNongMi/
├── common/                              # Shared modules
│   ├── config.py                        # Environment configuration
│   ├── llm.py                           # LLM wrapper (DeepSeek via LangChain)
│   ├── neo4j_manager.py                 # Neo4j client
│   ├── embedding_model.py               # BGE text embeddings
│   ├── session_manager.py               # Multi-session management
│   ├── stream_context.py                # Streaming output context
│   ├── output_graph_utils.py            # Graph visualization utilities
│   └── path_utils.py                    # Path utilities
│
├── __001__clawler/                      # 📥 Data Crawling
│   ├── crawl_herbs.py                   # Crawl herb list
│   ├── crawl_formulas.py                # Crawl formula list
│   ├── crawl_herb_detail.py             # Crawl herb details
│   └── crawl_formula_detail.py          # Crawl formula details
│
├── __002__extract_information/          # 🧠 Knowledge Extraction (LLM)
│   ├── __000__extract_graph_data_utils.py  # Extraction utilities
│   ├── __001__extract_herb_data.py         # Extract herb knowledge
│   └── __002__extract_formula_data.py      # Extract formula knowledge
│
├── __003__create_neo4j_database/        # 🗄️ Neo4j Graph Database
│   ├── __001__graph_importer.py         # Knowledge graph importer
│   ├── __002__export_metadata.py        # Schema metadata export
│   └── __003__faiss_embedding.py        # FAISS vector index builder
│
├── __004__langgraph_more_nodes/         # 🔄 LangGraph Workflows
│   ├── langgraph_more_nodes.py          # Graph definition + compilation (incl. integration tests)
│   ├── agent_state.py                   # State definitions
│   └── node/                            # Workflow nodes
│       ├── xiaohongshu_publish_intent_node.py  # Publishing intent recognition
│       ├── text_generate_node.py               # Content generation
│       ├── image_generate_node.py              # AI image generation
│       ├── check_text_image_node.py            # Content validation
│       ├── auto_publish_xiaohongshu_node.py    # Automated publishing
│       ├── generate_markdown_node.py           # Result output
│       ├── zhongyi_intent_node.py              # TCM intent recognition
│       ├── extract_entity_from_user_input_node.py  # Entity extraction
│       ├── match_entity_from_neo4j_node.py     # FAISS entity matching
│       ├── generate_neo4j_cypher_node.py       # Cypher generation
│       ├── check_cypher_node.py                # Cypher validation
│       ├── run_cypher_node.py                  # Cypher execution
│       ├── neo4j_answer_generate_node.py       # Answer generation
│       └── llm_direct_out_node.py              # Fallback (non-TCM queries)
│
├── __005__fastapi/                      # 🌐 FastAPI Backend
│   ├── __001__langgraph_fastapi.py      # API service (with SSE streaming)
│   └── __002__langgraph_fastapi_client.py  # Client example
│
├── __006__streamlit/                    # 🎨 Streamlit Frontend
│   ├── app.py                           # Home page
│   ├── pages/
│   │   ├── 01_💬_TCM_Q&A.py            # Knowledge Q&A page
│   │   ├── 02_📝_RED_Generator.py       # Content generator page
│   │   └── 03_🔍_KG_Explorer.py         # Graph explorer page
│   └── utils/
│       ├── api.py                       # FastAPI client
│       └── style.py                     # Styling system
│
├── __007__fine_tune/                    # 🎯 Model Fine-tuning
│   ├── fasttext_xiaohongshu_recognition/   # fastText intent classifier
│   ├── chineserobertawwmext_zhongyi_recognition/  # RoBERTa intent classifier
│   └── intent_recognition_data/             # Training datasets
│
├── picture/                             # 📸 App screenshots
├── .env.example                         # Environment variable template
├── pyproject.toml                       # Project config (uv dependency management)
└── LICENSE                              # MIT License
```

---

## 🚀 Quick Start

### Prerequisites

- **Python** >= 3.10
- **Neo4j** >= 5.x (Graph Database)
- **[uv](https://docs.astral.sh/uv/)** (Python package manager)

### 1. Clone the Repository

```bash
git clone https://github.com/Happy-Chen-CH/ShenNongMi.git
cd ShenNongMi
```

### 2. Install Dependencies

```bash
# Option A: Using uv (recommended — auto-creates virtual environment)
uv sync

# Option B: Using pip
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Install Playwright browser (required for RED auto-publishing)
uv run playwright install chromium
# Or if using pip: playwright install chromium
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys and database credentials
```

| Variable | Description | Required |
|----------|-------------|:--------:|
| `MODEL_API_KEY` | LLM API Key (supports DeepSeek / OpenAI-compatible APIs) | ✅ |
| `MODEL_BASE_URL` | LLM API endpoint (default: `https://api.deepseek.com`) | ✅ |
| `MODEL_NAME` | Model name (e.g., `deepseek-v4-flash`) | ✅ |
| `NEO4J_URI` | Neo4j connection URI (default: `bolt://localhost:7687`) | ✅ |
| `NEO4J_USER` | Neo4j username (default: `neo4j`) | ✅ |
| `NEO4J_PASSWORD` | Neo4j password | ✅ |
| `EMBEDDING_MODEL_PATH` | Local embedding model path (leave empty to auto-download `BAAI/bge-large-zh-v1.5` from HuggingFace) | |
| `JIMENG_AK` | Jimeng AI Access Key (Volcengine, for RED image generation) | |
| `JIMENG_SK` | Jimeng AI Secret Key (Volcengine, for RED image generation) | |

### 4. Prepare the Knowledge Graph

```bash
# Step 1: Crawl TCM encyclopedia data
uv run python __001__clawler/crawl_herbs.py
uv run python __001__clawler/crawl_formulas.py
uv run python __001__clawler/crawl_herb_detail.py
uv run python __001__clawler/crawl_formula_detail.py

# Step 2: Extract structured knowledge with LLM
uv run python __002__extract_information/__001__extract_herb_data.py
uv run python __002__extract_information/__002__extract_formula_data.py

# Step 3: Import into Neo4j + Build FAISS index
uv run python __003__create_neo4j_database/__001__graph_importer.py
uv run python __003__create_neo4j_database/__002__export_metadata.py
uv run python __003__create_neo4j_database/__003__faiss_embedding.py
```

### 5. Launch Services

```bash
# Terminal 1: Start FastAPI backend
uv run python __005__fastapi/__001__langgraph_fastapi.py

# Terminal 2: Start Streamlit frontend
uv run streamlit run __006__streamlit/app.py
```

Open **http://localhost:8501** in your browser.

---

## 🧪 Running Tests

```bash
uv run python __004__langgraph_more_nodes/langgraph_more_nodes.py
```

This script includes integration tests for both main pipelines (TCM Knowledge Q&A + Xiaohongshu Publishing), running with mock data — no external services required.

---

## 🛠️ Tech Stack

| Layer | Technology | Description |
|-------|-----------|-------------|
| 🎨 **Frontend** | Streamlit | Interactive multi-page web interface |
| 🌐 **Backend API** | FastAPI | High-performance async API with SSE streaming |
| 🔄 **Workflow Engine** | LangGraph | Stateful multi-node workflow orchestration |
| 🤖 **LLM** | DeepSeek v4 | OpenAI-compatible API for knowledge extraction & Q&A |
| 🗄️ **Graph Database** | Neo4j | 6 entity types + 6 relationship types of TCM knowledge |
| 🔍 **Vector Search** | FAISS + BGE-Large-Zh-v1.5 | Semantic entity matching, optimized for Chinese |
| 🌐 **Browser Automation** | Playwright | RED (Xiaohongshu) automated publishing |
| 🎯 **Intent Recognition** | RoBERTa + fastText | Dual-model fine-tuning for TCM vs. publishing intent |
| 🎨 **AI Image Generation** | Volcengine Jimeng AI | TCM wellness content image generation |
| 📦 **Package Manager** | uv | Fast, reliable Python dependency management |

---

## 🤝 Contributing

Issues and Pull Requests are welcome!

1. **Fork** this repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'feat: add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

> We recommend using [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

---

## 📚 Related Articles

- [ShennongMi: AI-Powered TCM Knowledge Graph — CSDN Blog (Chinese)](https://blog.csdn.net/2301_81954099/article/details/163312707)

---

## 📄 License

This project is open-sourced under the [MIT License](LICENSE).

---

## ⚠️ Disclaimer

This project is intended for **educational and research purposes only**. The TCM knowledge in the graph is sourced from publicly available TCM encyclopedia websites and does **not** constitute medical advice. Please consult a licensed healthcare professional for any health concerns. The Xiaohongshu auto-publishing feature should be used in compliance with the platform's terms of service.
