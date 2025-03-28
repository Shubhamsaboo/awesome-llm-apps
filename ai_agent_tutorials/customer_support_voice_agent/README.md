# 🎙️ Customer Support Voice Agent

An OpenAI SDK powered customer support agent application that delivers voice-powered responses to questions about your knowledge base using OpenAI's GPT-4o and TTS capabilities. The system crawls through documentation websites with Firecrawl, processes the content into a searchable knowledge base with Qdrant, and provides both text and voice responses to user queries.

## Features

- Knowledge Base Creation

  - Crawls documentation websites using Firecrawl
  - Stores and indexes content using Qdrant vector database
  - Generates embeddings for semantic search capabilities using FastEmbed
- **AI Agent Team**
  - **Documentation Processor**: Analyzes documentation content and generates clear, concise responses to user queries
  - **TTS Agent**: Converts text responses into natural-sounding speech with appropriate pacing and emphasis
  - **Voice Customization**: Supports multiple OpenAI TTS voices:
    - alloy, ash, ballad, coral, echo, fable, onyx, nova, sage, shimmer, verse

- **Interactive Interface**
  - Clean Streamlit UI with sidebar configuration
  - Real-time documentation search and response generation
  - Built-in audio player with download capability
  - Progress indicators for system initialization and query processing

## How to Run

1. **Setup Environment**
   ```bash
   # Clone the repository
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/ai_agent_tutorials/ai_voice_agent_openaisdk
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configure API Keys**
   - Get OpenAI API key from [OpenAI Platform](https://platform.openai.com)
   - Get Qdrant API key and URL from [Qdrant Cloud](https://cloud.qdrant.io)
   - Get Firecrawl API key for documentation crawling

3. **Run the Application**
   ```bash
   streamlit run ai_voice_agent_docs.py
   ```

4. **Use the Interface**
   - Enter API credentials in the sidebar
   - Input the documentation URL you want to learn about
   - Select your preferred voice from the dropdown
   - Click "Initialize System" to process the documentation
   - Ask questions and receive both text and voice responses

## Features in Detail

- **Knowledge Base Creation**
  - Builds a searchable knowledge base from your documentation
  - Preserves document structure and metadata
  - Supports multiple page crawling (limited to 5 pages per default configuration)

- **Vector Search**
  - Uses FastEmbed for generating embeddings
  - Semantic search capabilities for finding relevant content
  - Efficient document retrieval using Qdrant

- **Voice Generation**
  - High-quality text-to-speech using OpenAI's TTS models
  - Multiple voice options for customization
  - Natural speech patterns with proper pacing and emphasis
