## 💻 Local Lllama-3 with RAG
Streamlit app that allows you to chat with any webpage using local Llama-3 and Retrieval Augmented Generation (RAG). This app runs entirely on your computer, making it 100% free and without the need for an internet connection.


### Features
- Input a webpage URL
- Ask questions about the content of the webpage
- Get accurate answers using RAG and the Llama-3 model running locally on your computer

### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
```
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```
3. Get your OpenAI API Key

- Sign up for an [OpenAI account](https://platform.openai.com/) (or the LLM provider of your choice) and obtain your API key.

4. Run the Streamlit App
```bash
streamlit run llama3_local_rag.py
```

### How it Works?

- The app loads the webpage data using WebBaseLoader and splits it into chunks using RecursiveCharacterTextSplitter.
- It creates Ollama embeddings and a vector store using Chroma.
- The app sets up a RAG (Retrieval-Augmented Generation) chain, which retrieves relevant documents based on the user's question.
- The Llama-3 model is called to generate an answer using the retrieved context.
- The app displays the answer to the user's question.

