# – Local AI Legal Agent Team

A privacy-focused legal document analysis system running entirely on local infrastructure using Ollama models and Qdrant vector database.

## < Features

- **100% Local Processing**: All data stays on your machine - no cloud APIs
- **Multi-Agent Legal Team**: Specialized agents for different legal tasks
- **PDF Document Analysis**: Upload and analyze legal documents
- **Vector Database**: Local Qdrant instance for document retrieval
- **Privacy First**: Perfect for sensitive legal documents

## =Ë Prerequisites

- Python 3.8+
- Docker (for Qdrant vector database)
- Ollama installed locally with required models
- At least 8GB RAM recommended

## =€ Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_ai_agents/multi_agent_apps/agent_teams/ai_legal_agent_team/local_ai_legal_agent_team
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Local Infrastructure

#### Install Ollama
```bash
# Linux/Mac
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required models
ollama pull openhermes
ollama pull llama2  # or your preferred local model
```

#### Start Qdrant Vector Database
```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 -p 6334:6334 \
    -v "$(pwd)/qdrant_storage:/qdrant/storage:z" \
    qdrant/qdrant
```

### 4. Run the Application
```bash
streamlit run local_legal_agent.py
```

## =Ö How It Works

1. **Document Upload**: Upload PDF legal documents through the interface
2. **Local Processing**: Documents are processed using Ollama embeddings
3. **Vector Storage**: Document chunks stored in local Qdrant database
4. **Agent Analysis**: Legal agent team analyzes documents using local LLMs
5. **Privacy Preserved**: All processing happens locally - no data leaves your machine

## <Û Legal Agent Roles

The system includes specialized agents for:
- **Document Reviewer**: Initial document analysis and summarization
- **Legal Researcher**: Finding relevant precedents and references
- **Contract Analyst**: Specific contract clause analysis
- **Compliance Checker**: Regulatory compliance verification

## =¡ Usage Tips

- Ensure Ollama and Qdrant are running before starting the app
- Larger documents may take time to process locally
- Use appropriate Ollama models based on your hardware capabilities
- Regular cleanup of vector database recommended for optimal performance

## =' Configuration

### Ollama Models
- Default embedding model: `openhermes`
- Default LLM: Configure in the app based on available models
- Check available models: `ollama list`

### Qdrant Settings
- Default URL: `http://localhost:6333`
- Collection name: `legal_knowledge`
- Persistence: Data saved in `./qdrant_storage`

##   Important Notes

- This is a demonstration system for educational purposes
- Not a replacement for professional legal advice
- Ensure compliance with local regulations when processing legal documents
- Performance depends on local hardware capabilities

## > Contributing

Contributions welcome! Areas for improvement:
- Support for more document formats
- Additional legal agent specializations
- Performance optimizations for local processing
- Enhanced security features

## =Ä License

This project is part of the Awesome LLM Apps repository.

## = Related Projects

- [AI Legal Agent Team (Cloud)](../README.md)
- [AI Finance Agent Team](../../ai_finance_agent_team)
- [AI Teaching Agent Team](../../ai_teaching_agent_team)