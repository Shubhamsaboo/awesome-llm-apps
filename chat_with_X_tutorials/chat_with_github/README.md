## 💬 Chat with GitHub Repo

LLM app with RAG to chat with GitHub Repo in just 30 lines of Python Code. The app uses Retrieval Augmented Generation (RAG) to provide accurate answers to questions based on the content of the specified GitHub repository.

### Features

- Provide the name of GitHub Repository as input
- Ask questions about the content of the GitHub repository
- Get accurate answers using OpenAI's API and Embedchain

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

4. Get your GitHub Access Token

- Create a [personal access token](https://docs.github.com/en/enterprise-server@3.6/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token) with the necessary permissions to access the desired GitHub repository.

4. Run the Streamlit App
```bash
streamlit run chat_github.py
```

### How it Works?

- The app prompts the user to enter their OpenAI API key, which is used to authenticate requests to the OpenAI API.

- It initializes an instance of the Embedchain App class and a GithubLoader with the provided GitHub Access Token.

- The user is prompted to enter a GitHub repository URL, which is then added to the Embedchain app's knowledge base using the GithubLoader.

- The user can ask questions about the GitHub repository using the text input.

- When a question is asked, the app uses the chat method of the Embedchain app to generate an answer based on the content of the GitHub repository.

- The app displays the generated answer to the user.
