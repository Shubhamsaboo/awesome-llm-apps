## 🎙️ Voice RAG with Groq and Edge-TTS

### 🎓 FREE Step-by-Step Tutorial 
**👉 [Click here to follow our complete step-by-step tutorial](https://www.theunwindai.com/p/build-a-voice-rag-agent) and learn how to build this from scratch with detailed code walkthroughs, explanations, and best practices.**

This script demonstrates how to build a voice-enabled Retrieval-Augmented Generation (RAG) system using Groq and Edge-TTS with Streamlit. The application allows users to upload PDF documents, ask questions, and receive both text and voice responses using Microsoft Edge's Neural Text-to-Speech — all on a completely free stack.

### Features

- Creates a voice-enabled RAG system powered by Groq (Llama 3.1) and Edge-TTS
- Supports PDF document processing and chunking
- Uses Qdrant as the vector database for efficient similarity search
- Implements real-time text-to-speech with multiple neural voice options via Edge-TTS (no API key required)
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
- Get your free [Groq API key](https://console.groq.com/) (no credit card required)
- Set up a [Qdrant Cloud](https://cloud.qdrant.io/) account and get your API key and URL
- **Edge-TTS requires no API key** — it works out of the box once installed
- Create a `.env` file with your credentials:
```bash
GROQ_API_KEY='your-groq-api-key'
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
   - Groq (Llama 3.1) generates a clear, spoken-word friendly response from the retrieved context
   - The response is passed to Edge-TTS for speech synthesis

3. **Voice Generation:**
   - Text responses are converted to speech using Microsoft Edge-TTS (free, no API key needed)
   - Users can choose from multiple neural voice options across different accents and genders
   - Audio can be played directly or downloaded as MP3

4. **Features:**
   - Real-time audio streaming
   - Multiple neural voice personality options (US, UK, Australian, Canadian, and Indian English)
   - Document source tracking
   - Download capability for audio responses
   - Progress tracking for document processing