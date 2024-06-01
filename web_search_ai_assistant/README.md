## 🎯 Generative AI Search Assistant
This Streamlit app combines the power of search engines and LLMs to provide you with pinpointed answers to your queries. By leveraging OpenAI's GPT-4o and the DuckDuckGo search engine, this AI search assistant delivers accurate and concise responses to your questions.

### Features
- Get pinpointed answers to your queries
- Utilize DuckDuckGo search engine for web searching
- Use OpenAI GPT-4o for intelligent answer generation

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
streamlit run ai_websearch.py
```

### How It Works?

- Upon running the app, you will be prompted to enter your OpenAI API key. This key is used to authenticate and access the OpenAI language models.

- Once you provide a valid API key, an instance of the Assistant class is created. This assistant utilizes the GPT-4 language model from OpenAI and the DuckDuckGo search engine tool.

- Enter your search query in the provided text input field.

- The assistant will perform the following steps:
    - Conduct a web search using DuckDuckGo based on your query
    - Analyze the search results and extract relevant information
    - Generate a concise and targeted answer using the GPT-4 language model

- The pinpointed answer will be displayed in the app, providing you with the information you need.