# 🧐 Agentic RAG with Reasoning
A sophisticated RAG system that demonstrates an AI agent's step-by-step reasoning process using Agno, Claude and OpenAI. This implementation allows users to upload documents, add web sources, ask questions, and observe the agent's thought process in real-time.


## Features

1. Interactive Knowledge Base Management
- Upload documents to expand the knowledge base
- Add URLs dynamically for web content
- Persistent vector database storage using LanceDB


2. Transparent Reasoning Process
- Real-time display of the agent's thinking steps
- Side-by-side view of reasoning and final answer
- Clear visibility into the RAG process


3. Advanced RAG Capabilities
- Vector search using OpenAI embeddings for semantic matching
- Source attribution with citations


## Agent Configuration

- Claude 3.5 Sonnet for language processing
- OpenAI embedding model for vector search
- ReasoningTools for step-by-step analysis
- Customizable agent instructions

## Prerequisites

You'll need the following API keys:

1. Anthropic API Key

- Sign up at console.anthropic.com
- Navigate to API Keys section
- Create a new API key

2. OpenAI API Key

- Sign up at platform.openai.com
- Navigate to API Keys section
- Generate a new API key

## How to Run

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
    cd rag_tutorials/agentic_rag_with_reasoning
    ```

2. **Install the dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Run the Application:**
    ```bash
    streamlit run rag_reasoning_agent.py
    ```

4. **Configure API Keys:**

- Enter your Anthropic API key in the first field
- Enter your OpenAI API key in the second field
- Both keys are required for the app to function


5. **Use the Application:**

- Add Knowledge Sources: Use the sidebar to add URLs to your knowledge base
- Ask Questions: Enter queries in the main input field
- View Reasoning: Watch the agent's thought process unfold in real-time
- Get Answers: Receive comprehensive responses with source citations

## How It Works

The application uses a sophisticated RAG pipeline:

### Knowledge Base Setup
- Documents are loaded from URLs using WebBaseLoader
- Text is chunked and embedded using OpenAI's embedding model 
- Vectors are stored in LanceDB for efficient retrieval
- Vector search enables semantic matching for relevant information

### Agent Processing
- User queries trigger the agent's reasoning process
- ReasoningTools help the agent think step-by-step
- The agent searches the knowledge base for relevant information
- Claude 4 Sonnet generates comprehensive answers with citations

### UI Flow
- Enter API keys → Add knowledge sources → Ask questions
- Reasoning process and answer generation displayed side-by-side
- Sources cited for transparency and verification