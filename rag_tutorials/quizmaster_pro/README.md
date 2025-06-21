# 📚 QuizMaster Pro

Transform any document into intelligent, personalized quizzes using AI. QuizMaster Pro offers flexible document processing and quiz generation using either OpenAI or local Ollama models.

![QuizMasterPro Demo](https://github.com/maurizioorani/QuizMasterPro/raw/main/screenshots/QuizMasterPro.gif)

> **Note on Local Model Performance:**
> I am actively working to improve topic generation time with local models (LlamaCPP), as it can be slow. Additionally, local models may have difficulty with reliable JSON generation. For the best experience, I recommend using OpenAI's frontier models, which are currently more reliable for these tasks.

## 🎯 Core Concept

Upload documents → AI extracts key concepts → Select topics to focus on → Generate targeted quizzes → Get personalized learning insights

## ✨ Key Features

### 📄 Smart Document Processing
- **Multi-format support**: PDF, DOCX, TXT, HTML with robust error handling
- **Advanced concept extraction**:
    - Utilizes ContextGem for sophisticated document understanding.
    - Supports local GGUF models (e.g., Mistral 7B Instruct) via LlamaCPP with grammar-enforced JSON output for reliable structured data.
    - New LlamaCPP -> ContextGem pipeline: LlamaCPP preprocesses text into structured JSON, which is then fed to ContextGem for refined concept mapping.
- **Interactive topic selection**: Browse and select from automatically extracted concepts and topics.
- **Persistent storage**: Document management with semantic search capabilities.
- **Model synchronization**: Consistent AI model usage across document processing and quiz generation.

### 🧠 Intelligent Quiz Generation
- **Unified model management**: Seamless switching between OpenAI, local Ollama models, and local GGUF models (via LlamaCPP).
- **Enhanced model support**: Includes Ollama models (e.g., `llama3.3:8b`, `mistral:7b`) and local GGUF models like `mistral-7b-instruct-gguf (Local)`.
- **Topic-focused generation**: Create quizzes from selected concepts rather than entire documents.
- **Question type**: Multiple choice
- **Three difficulty levels**: Easy, medium, hard with adaptive content based on selected topics
- **Smart question diversity**: Advanced algorithms to prevent repetitive questions

### 📊 Advanced Analytics
- **Performance insights**: Comprehensive analysis using enhanced InsightsGenerator
- **Learning patterns**: Cognitive load assessment, retention analysis, knowledge gap identification
- **Personalized recommendations**: Study strategies, improvement plans, actionable next steps
- **Progress tracking**: Historical performance and milestone progression

### 🎮 Interactive Experience
- **Modern interface**: Clean Streamlit UI with real-time progress tracking
- **Smart navigation**: Question flow with immediate feedback and explanations
- **Session management**: Resume quizzes and track completion status

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- **AI Model Access**: Either OpenAI API Key OR [Ollama](https://ollama.ai/) for local models
- Recommended: Both for maximum flexibility

### Installation
```bash
# 1. Clone repository
git clone https://github.com/maurizioorani/QuizMasterPro.git
cd QuizMasterPro

# 2. Install dependencies
# Ensure you have build tools for llama-cpp-python if installing from source (e.g., C++ compiler)
# Or install from pre-built wheels if available for your platform.
pip install -r requirements.txt

# 3. Launch application
streamlit run src/quizmaster/streamlit_app.py
```

### Model Setup (Choose One or More)

**Option A: OpenAI Models**
```bash
# Configure OpenAI API key
echo "OPENAI_API_KEY=your_key_here" > .env
```

**Option B: Local Ollama Models**
```bash
# Install Ollama (visit https://ollama.ai/)
ollama serve

# Ollama models (e.g., mistral:7b) auto-download when selected in app
```

**Option C: Local GGUF Models (via LlamaCPP)**
```bash
# 1. Download the GGUF model (e.g., Mistral 7B Instruct Q8_0):
# Ensure huggingface-cli is installed: pip install huggingface-hub
python download_gguf_model.py
# This script downloads mistral-7b-instruct-v0.1.Q8_0.gguf to the project root by default.
# You can configure the model path in src/quizmaster/config.py (gguf_model_path).

# 2. Select "mistral-7b-instruct-gguf (Local)" in the app's AI Model Selection.
```

## 🎯 How to Use

### 1. **Process Documents & Extract Topics**
- Upload PDF, DOCX, TXT, or HTML files
- **AI automatically extracts key concepts** using dual-source analysis:
  - ContextGem for advanced document understanding  
  - Direct LLM analysis for topic identification
- **Review extracted concepts** organized by categories (Key Definitions, Main Ideas, Important Facts)
- Documents stored persistently with concept metadata for reuse

### 2. **Interactive Topic Selection**
- **Browse automatically extracted concepts** in an organized interface
- **Select specific topics** you want to focus on for learning
- **Combine multiple concepts** from different categories
- **Use "Select All" or individual checkboxes** for fine-grained control
- Preview selected concepts before quiz generation

### 3. **Generate Targeted Quiz**
- **Configure quiz settings**: question types, difficulty, number of questions
- **Select your AI model**: Choose between OpenAI or local Ollama models  
- **Enable model synchronization** for consistent concept extraction and quiz generation
- AI creates questions **focused exclusively on your selected topics**
- Get immediate feedback and detailed explanations

### 4. **Analyze Performance & Track Progress**
- Receive detailed insights and analytics on your selected topics
- Get personalized study recommendations based on performance
- Track learning progress over time with concept-specific metrics
- Review which topics need more attention

## 🔧 Model Configuration

### Document Processing & Quiz Generation
**🏆 Recommended Local Models (Ollama - Served via Ollama API):**
- **`llama3.3:8b`** - Strong general-purpose model
- **`mistral:7b`** - Efficient, good for JSON generation (4.1GB) (Note: This is the Ollama-served version)
- **`qwen2.5:7b`** - Strong structured output, multilingual (4.4GB)
- **`deepseek-coder:6.7b`** - Excellent for code-related tasks and structured output

**⚙️ Local GGUF Models (via LlamaCPP - Direct File Access):**
- **`mistral-7b-instruct-gguf (Local)`**: (Default: `mistral-7b-instruct-v0.1.Q8_0.gguf`) Uses LlamaCPP for grammar-enforced JSON, good for structured tasks. Download via `download_gguf_model.py`. Path configurable in `src/quizmaster/config.py`.

**☁️ OpenAI Models:**
- **`gpt-4o-mini`** - Fast and cost-effective, good for structured output.
- **`gpt-4o`** - High-quality structured output.
- **`gpt-3.5-turbo`** - Balanced performance.

### Model Selection Tips
- **For document processing (concept extraction)**:
    - **OpenAI models (e.g., `gpt-4o-mini`)**: Generally reliable for structured JSON with ContextGem.
    - **`mistral-7b-instruct-gguf (Local)`**: Recommended for local processing. It uses LlamaCPP with grammar to generate structured JSON, which is then fed to ContextGem for concept mapping. This aims to improve reliability over direct ContextGem use with other local models.
    - **Ollama-served models (e.g., `mistral:7b`, `deepseek-coder:6.7b`)**: Can be used with ContextGem, but JSON output consistency for ContextGem's internal parsing may vary. The system has fallbacks.
- **For quiz generation**: All listed models generally provide good quality. The selected model for document processing will also be used for quiz generation by default.
- **Model synchronization**: Using the same model (or engine type) for both document processing and quiz generation is handled automatically.

## 🏗️ Architecture

### Core Components
```
├── streamlit_app.py              # Main Streamlit UI, event handling, and orchestration
├── config.py                     # Shared application configuration (model paths, engine selection)
├── llm_manager.py                # Manages LLM selection, availability & shared model configuration
├── document_processor.py         # Orchestrates document processing: parsing, text extraction, concept extraction routing
├── file_parsers.py               # Handles text extraction from different file formats (PDF, DOCX, TXT, HTML)
├── text_utils.py                 # Text processing utilities (token counting, chunking)
├── llm_concept_extractors.py     # Houses strategies for concept extraction (ContextGem, LlamaCPP)
├── vector_manager.py             # Document storage (PostgreSQL), metadata extraction (ContextGem/LlamaCPP) & retrieval
├── quiz_generator.py             # AI-powered quiz question generation
├── insights_generator.py         # Generates learning insights and performance analytics
└── database_manager.py           # Handles PostgreSQL database interactions
```

### Document Processing Pipelines
- **Flexible Engine Selection**: Users can choose the AI model and underlying processing engine:
    - **ContextGem Engine**: Leverages the ContextGem library with models like OpenAI or Ollama-served LLMs for advanced document understanding and concept/aspect extraction.
    - **LlamaCPP GGUF Engine**:
        - Uses local GGUF models (e.g., Mistral 7B Instruct) via LlamaCPP.
        - Employs grammar-enforced JSON output for structured data extraction.
        - **LlamaCPP -> ContextGem Pre-processing**: For concept extraction, LlamaCPP first preprocesses text chunks into structured JSON (identifying potential topics, definitions, etc.). This structured JSON is then passed to ContextGem, which uses its configured LLM (e.g., an Ollama model or OpenAI model) to map this pre-processed information to its defined concepts and aspects. This aims to improve reliability for ContextGem when local models are preferred for the initial heavy lifting.
- **Modular Design**: Text extraction (`file_parsers.py`), text utilities (`text_utils.py`), and LLM-specific extraction logic (`llm_concept_extractors.py`) are separated for clarity and maintainability.
- **Smart Retrieval**: Semantic search based on extracted concepts allows for efficient retrieval of relevant document sections for quiz generation.
- **Rich Metadata**: Document structure, creation timestamps, and extraction summaries are stored as metadata for comprehensive document management.
- **Topic Mapping**: Organized concept categories facilitate targeted quiz generation based on specific topics selected by the user.

### Intelligent Analytics Pipeline
- **Performance analysis**: Multi-dimensional scoring and pattern recognition
- **Learning style detection**: Adaptive recommendations based on quiz behavior
- **Cognitive load assessment**: Personalized study strategies and pacing
- **Progress benchmarking**: Milestone tracking and improvement measurement

## 🛠️ Troubleshooting

### Common Solutions
| Issue | Solution |
|-------|----------|
| Ollama connection failed | Run `ollama serve` and ensure port 11434 is available |
| OpenAI API errors | Verify OpenAI API key in `.env` file (if using OpenAI models) |
| Document processing errors | Check selected model is available and running |
| Poor quiz quality | Use recommended models (deepseek-r1, mistral:7b, qwen2.5:7b) |
| Slow performance | Reduce document size or use focus sections |

### System Requirements
- **Minimum**: 8GB RAM, 4GB storage
- **Recommended**: 16GB RAM, 10GB storage
- **Large models**: 32GB+ RAM

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Submit pull request

---

**QuizMaster Pro** - Intelligent learning through AI-powered quiz generation 🎓
