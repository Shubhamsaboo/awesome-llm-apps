## 🖇️ RAG-as-a-Service with Claude 3.5 Sonnet
Build and deploy a production-ready Retrieval-Augmented Generation (RAG) service using Claude 3.5 Sonnet and Ragie.ai. This implementation allows you to create a document querying system with a user-friendly Streamlit interface in less than 50 lines of Python code.

### Features
- Production-ready RAG pipeline
- Integration with Claude 3.5 Sonnet for response generation
- Document upload from URLs
- Real-time document querying
- Support for both fast and accurate document processing modes

### How to get Started?

1. Clone the GitHub repository
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/rag_tutorials/rag-as-a-service
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Get your Anthropic API and Ragie API Key

- Sign up for an [Anthropic account](https://console.anthropic.com/) and get your API key
- Sign up for an [Ragie account](https://www.ragie.ai/) and get your API key

4. Run the Streamlit app
```bash
streamlit run rag_app.py
```

## 📖 How It Works

1. **Document Upload**: Enter URLs of documents you want to query
2. **Processing Mode**: Choose between fast (quick indexing) or accurate (thorough analysis) mode
3. **Document Ingestion**: Ragie.ai processes and indexes your documents
4. **Query Processing**: Ask questions about your uploaded documents
5. **RAG Pipeline**: System retrieves relevant chunks and generates responses using Claude 3.5 Sonnet

## 💡 Usage Examples

Perfect for:
- **Knowledge Base Q&A**: Query technical documentation or manuals
- **Research Assistant**: Analyze academic papers and reports
- **Content Analysis**: Extract insights from articles and blogs
- **Document Intelligence**: Build custom document understanding systems

## 🔧 Configuration

### Processing Modes
- **Fast Mode**: Quick document processing for rapid prototyping
- **Accurate Mode**: Comprehensive analysis for production use

### API Integration
- **Ragie.ai**: Handles document ingestion, chunking, and retrieval
- **Claude 3.5 Sonnet**: Generates contextual responses from retrieved content
- **Streamlit**: Provides the web interface

## 🚀 Advanced Features

- Supports multiple document formats through URL upload
- Maintains document context across queries
- Scalable architecture for production deployment
- Built-in error handling and retry logic

## 🤝 Contributing

Enhance this RAG service by:
- Adding support for local file uploads
- Implementing document management features
- Creating custom retrieval strategies
- Adding authentication and user management

## 📄 License

This project is part of the Awesome LLM Apps repository.

## 🔗 Related Projects

- [Agentic RAG](../agentic_rag)
- [Chat with PDF](../../advanced_llm_apps/chat_with_X_tutorials/chat_with_pdf)
- [Autonomous RAG](../autonomous_rag)