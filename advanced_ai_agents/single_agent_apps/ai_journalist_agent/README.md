## 🗞️ AI Journalist Agent 
This Streamlit app is an AI-powered journalist agent that generates high-quality articles using OpenAI GPT-4o. It automates the process of researching, writing, and editing articles, allowing you to create compelling content on any topic with ease.

### Features
- Searches the web for relevant information on a given topic
- Writes well-structured, informative, and engaging articles
- Edits and refines the generated content to meet the high standards of the New York Times

### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/single_agent_apps/ai_journalist_agent
```
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```
3. Get your OpenAI API Key

- Sign up for an [OpenAI account](https://platform.openai.com/) (or the LLM provider of your choice) and obtain your API key.

4. Get your SerpAPI Key

- Sign up for an [SerpAPI account](https://serpapi.com/) and obtain your API key.

5. Run the Streamlit App
```bash
streamlit run journalist_agent.py
```

### How it Works?

The AI Journalist Agent utilizes three main components:
- Searcher: Responsible for generating search terms based on the given topic and searching the web for relevant URLs using the SerpAPI.
- Writer: Retrieves the text from the provided URLs using the NewspaperToolkit and writes a high-quality article based on the extracted information.
- Editor: Coordinates the workflow between the Searcher and Writer, and performs final editing and refinement of the generated article.

