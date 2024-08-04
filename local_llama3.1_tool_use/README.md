## 🦙 Local Llama3 Tool Use
This Streamlit app demonstrates function calling with the local Llama3 model using Ollama. It allows users to interact with an AI assistant that can access specific tools based on user selection.

### Features
- Utilizes local Llama3 model via Ollama as LLM
- Integrates YFinance for stock data retrieval and SerpAPI for web search capabilities 
- Dynamic tool selection through a user-friendly sidebar
- Real-time chat interface with the AI assistant

### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd local-llama3-tool-use
```
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Get your OpenAI API Key

- Set up your SerpAPI API key: Export your SerpAPI API key as an environment variable.
```bash
export SERPAPI_API_KEY=your_api_key_here
```

4. Run the Streamlit App
```bash
streamlit run llama3_tool_use.py
```

## How it Works?

1. **Tool Selection:** Users can select which tools (YFinance and/or SerpAPI) they want the assistant to use via checkboxes in the sidebar.

2. **Assistant Initialization:** The app initializes or updates the assistant based on the selected tools.

3. **Chat Interface:** Users can ask questions through a chat input, and the assistant responds using the enabled tools.

4. **Real-time Response:** The assistant's response is displayed in real-time, with a typing indicator.

5. **Tool Usage Display:** The app shows which tools are currently enabled in the sidebar.