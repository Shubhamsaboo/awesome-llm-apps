## 📰 Multi-Agent AI Researcher
This Streamlit app empowers you to research top stories and users on HackerNews using a team of AI assistants with GPT-4o. 

### Features
- Research top stories and users on HackerNews
- Utilize a team of AI assistants specialized in story and user research
- Generate blog posts, reports, and social media content based on your research queries

### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/multi_agent_apps/multi_agent_researcher
```
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```
3. Get your OpenAI API Key

- Sign up for an [OpenAI account](https://platform.openai.com/) (or the LLM provider of your choice) and obtain your API key.

4. Run the Streamlit App
```bash
streamlit run research_agent.py
```

### How it works?

- Upon running the app, you will be prompted to enter your OpenAI API key. This key is used to authenticate and access the OpenAI language models.
- Once you provide a valid API key, three specialized AI agents are created:
    - **HackerNews Researcher**: Specializes in getting top stories from HackerNews using the HackerNews API.
    - **Web Searcher**: Searches the web for additional information on topics using DuckDuckGo search.
    - **Article Reader**: Reads and extracts content from article URLs using newspaper4k tools.

- These agents work together as a coordinated team under the **HackerNews Team** which orchestrates the research process.
- Enter your research query in the provided text input field. This could be a topic, keyword, or specific question related to HackerNews stories or users.
- The HackerNews Team follows a structured workflow:
    1. First searches HackerNews for relevant stories based on your query
    2. Uses the Article Reader to extract detailed content from the story URLs
    3. Leverages the Web Searcher to gather additional context and information
    4. Finally provides a thoughtful and engaging summary with title, summary, and reference links
- The generated content is structured as an Article with a title, summary, and reference links for easy review and use.

