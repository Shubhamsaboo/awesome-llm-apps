## � AI Contextual Memory Assistant

This Streamlit app implements an AI-powered assistant that learns from your conversations and recalls relevant context when needed. It provides a chat interface where you can discuss anything, and the assistant will remember important details across sessions using Memlayer for intelligent memory management.

### Features
- **Natural Conversation Interface**: Chat with an AI assistant that feels personal and contextual
- **Remembers Your Preferences**: Tell it once about your favorite coffee, your work schedule, or your project details - it won't forget
- **Multi-tier Memory Search**: Choose how deeply the assistant searches its memory (Fast/Balanced/Deep)
- **User-Specific Memory**: Each user gets their own isolated memory space
- **Simple Setup**: No databases to configure - just run the app and start chatting
- **Local Memory Storage**: All conversations and memories stay on your machine
- **Memory Statistics**: View insights about stored memories and retrieval settings
- **Powered by GPT-4o-mini**: Intelligent responses with context-aware memory

### How to get Started?

1. Clone the GitHub repository
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_llm_apps/llm_apps_with_memory_tutorials/ai_contextual_memory_assistant
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Run the Streamlit App
```bash
streamlit run contextual_memory_assistant.py
```

4. Enter your OpenAI API key and username to start chatting!

### How it Works

The app automatically manages memory in the background:
1. **Smart Storage**: Only meaningful information from your conversations is stored
2. **Contextual Retrieval**: When you ask questions, relevant past conversations are surfaced automatically
3. **Relationship Mapping**: Connects related pieces of information for better context
4. **Multiple Sessions**: Create and switch between different chat sessions while maintaining shared memory

All memories are stored locally in the `./memories` directory, organized by username.

### Learn More

- [Memlayer Documentation](https://divagr18.github.io/memlayer/) - Learn about the memory layer powering this app
