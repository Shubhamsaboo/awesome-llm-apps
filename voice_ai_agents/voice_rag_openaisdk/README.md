## 🎙️ Voice RAG with OpenAI SDK

### 🎓 FREE Step-by-Step Tutorial 
**👉 [Click here to follow our complete step-by-step tutorial](https://www.theunwindai.com/p/build-a-voice-rag-agent) and learn how to build this from scratch with detailed code walkthroughs, explanations, and best practices.**

This script demonstrates how to build a voice-enabled Retrieval-Augmented Generation (RAG) system using OpenAI's SDK and Streamlit. The application allows users to upload PDF documents, ask questions, and receive both text and voice responses using OpenAI's text-to-speech capabilities.

### Features

- Creates a voice-enabled RAG system using OpenAI's SDK
- Supports PDF document processing and chunking
- Uses Qdrant as the vector database for efficient similarity search
- Implements real-time text-to-speech with multiple voice options
- Provides a user-friendly Streamlit interface
- Allows downloading of generated audio responses
- Supports multiple document uploads and tracking

### How to get Started?

1. Clone the GitHub repository
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/rag_tutorials/voice_rag_openaisdk
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your API keys:
- Get your [OpenAI API key](https://platform.openai.com/)
- Set up a [Qdrant Cloud](https://cloud.qdrant.io/) account and get your API key and URL
- Create a `.env` file with your credentials:
```bash
OPENAI_API_KEY='your-openai-api-key'
QDRANT_URL='your-qdrant-url'
QDRANT_API_KEY='your-qdrant-api-key'
```

4. Run the Voice RAG application:
```bash
streamlit run rag_voice.py
```

5. Open your web browser and navigate to the URL provided in the console output to interact with the Voice RAG system.

### How it works?

1. **Document Processing:** 
   - Upload PDF documents through the Streamlit interface
   - Documents are split into chunks using LangChain's RecursiveCharacterTextSplitter
   - Each chunk is embedded using FastEmbed and stored in Qdrant

2. **Query Processing:**
   - User questions are converted to embeddings
   - Similar documents are retrieved from Qdrant
   - A processing agent generates a clear, spoken-word friendly response
   - A TTS agent optimizes the response for speech synthesis

3. **Voice Generation:**
   - Text responses are converted to speech using OpenAI's TTS
   - Users can choose from multiple voice options
   - Audio can be played directly or downloaded as MP3

4. **Features:**
   - Real-time audio streaming
   - Multiple voice personality options
   - Document source tracking
   - Download capability for audio responses
   - Progress tracking for document processing