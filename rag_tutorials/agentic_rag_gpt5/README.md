# 🧠 Agentic RAG with GPT-5

An agentic RAG application built with the Agno framework, featuring GPT-5 and LanceDB for efficient knowledge retrieval and question answering.

## ✨ Features

- **🤖 GPT-5**: Latest OpenAI model for intelligent responses
- **🗄️ LanceDB**: Lightweight vector database for fast similarity search
- **🔍 Agentic RAG**: Intelligent retrieval augmented generation
- **📝 Markdown Formatting**: Beautiful, structured responses
- **🌐 Dynamic Knowledge**: Add URLs to expand knowledge base
- **⚡ Real-time Streaming**: Watch answers generate live
- **🎯 Clean Interface**: Simplified UI without configuration complexity

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key with GPT-5 access

### Installation

1. **Clone and navigate to the project**
   ```bash
   cd rag_tutorials/agentic_rag_gpt5
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your OpenAI API key**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
   Or create a `.env` file:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

4. **Run the application**
   ```bash
   streamlit run agentic_rag_gpt5.py
   ```

## 🎯 How to Use

1. **Enter your OpenAI API key** in the sidebar
2. **Add knowledge sources** by entering URLs in the sidebar
3. **Ask questions** using the text area or suggested prompts
4. **Watch answers stream** in real-time with markdown formatting

### Suggested Questions

- **"What is Agno?"** - Learn about the Agno framework and agents
- **"Teams in Agno"** - Understand how teams work in Agno
- **"Build RAG system"** - Get a step-by-step guide to building RAG systems

## 🏗️ Architecture

### Core Components

- **`Agent`**: Orchestrates the entire Q&A process
- **`UrlKnowledge`**: Manages document loading from URLs
- **`LanceDb`**: Vector database for efficient similarity search
- **`OpenAIEmbedder`**: Converts text to embeddings
- **`OpenAIChat`**: GPT-5-nano model for generating responses

### Data Flow

1. **Knowledge Loading**: URLs are processed and stored in LanceDB
2. **Vector Search**: OpenAI embeddings enable semantic search
3. **Response Generation**: GPT-5-nano processes information and generates answers
4. **Streaming Output**: Real-time display of formatted responses

## 🔧 Configuration

### Database Settings
- **Vector DB**: LanceDB with local storage
- **Table Name**: `agentic_rag_docs`
- **Search Type**: Vector similarity search

## 📚 Knowledge Management

### Adding Sources
- Use the sidebar to add new URLs
- Sources are automatically processed and indexed
- Current sources are displayed as numbered list

### Default Knowledge
- Starts with Agno documentation: `https://docs.agno.com/introduction/agents.md`
- Expandable with any web-based documentation

## 🎨 UI Features

### Sidebar
- **API Key Management**: Secure input for OpenAI credentials
- **URL Addition**: Dynamic knowledge base expansion
- **Current Sources**: Numbered list of loaded URLs

### Main Interface
- **Suggested Prompts**: Quick access to common questions
- **Query Input**: Large text area for custom questions
- **Real-time Streaming**: Live answer generation
- **Markdown Rendering**: Beautiful formatted responses
