## 📨 Chat with Gmail Inbox 

LLM app with RAG to chat with Gmail in just 30 lines of Python Code. The app uses Retrieval Augmented Generation (RAG) to provide accurate answers to questions based on the content of your Gmail Inbox.

### Features

- Connect to your Gmail Inbox
- Ask questions about the content of your emails
- Get accurate answers using RAG and the selected LLM

### Installation

1. Clone the repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
```
2. Install the required dependencies

```bash
pip install -r requirements.txt
```

3. Set up your Google Cloud project and enable the Gmail API:

- Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project.
- Navigate to "APIs & Services > OAuth consent screen" and configure the OAuth consent screen.
- Publish the OAuth consent screen by providing the necessary app information.
- Enable the Gmail API and create OAuth client ID credentials.
- Download the credentials in JSON format and save them as `credentials.json` in your working directory.

4. Get your OpenAI API Key

- Sign up for an [OpenAI account](https://platform.openai.com/) (or the LLM provider of your choice) and obtain your API key.

4. Run the Streamlit App

```bash
streamlit run chat_gmail.py
```


