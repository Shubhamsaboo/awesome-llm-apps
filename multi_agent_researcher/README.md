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
- Once you provide a valid API key, three instances of the Assistant class are created:
    - **story_researcher**: Specializes in researching HackerNews stories.
    - **user_researcher**: Focuses on researching HackerNews users and reading articles from URLs.
    - **hn_assistant**: A team assistant that coordinates the research efforts of the story and user researchers.

- Enter your research query in the provided text input field. This could be a topic, keyword, or specific question related to HackerNews stories or users.
- The hn_assistant will orchestrate the research process by delegating tasks to the story_researcher and user_researcher based on your query.
- The AI assistants will gather relevant information from HackerNews using the provided tools and generate a comprehensive response using the GPT-4 language model.
- The generated content, which could be a blog post, report, or social media post, will be displayed in the app for you to review and use.

