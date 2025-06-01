## 🎬 AI Movie Production Agent
This Streamlit app is an AI-powered movie production assistant that helps bring your movie ideas to life using Claude 3.5 Sonnet model. It automates the process of script writing and casting, allowing you to create compelling movie concepts with ease.

### Features
- Generates script outlines based on your movie idea, genre, and target audience
- Suggests suitable actors for main roles, considering their past performances and current availability
- Provides a concise movie concept overview

### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/single_agent_apps/ai_movie_production_agent
```
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```
3. Get your Anthropic API Key

- Sign up for an [Anthropic account](https://console.anthropic.com) (or the LLM provider of your choice) and obtain your API key.

4. Get your SerpAPI Key

- Sign up for an [SerpAPI account](https://serpapi.com/) and obtain your API key.

5. Run the Streamlit App
```bash
streamlit run movie_production_agent.py
```

### How it Works?

The AI Movie Production Agent utilizes three main components:
- **ScriptWriter**: Develops a compelling script outline with character descriptions and key plot points based on the given movie idea and genre.
- **CastingDirector**: Suggests suitable actors for the main roles, considering their past performances and current availability.
- **MovieProducer**: Oversees the entire process, coordinating between the ScriptWriter and CastingDirector, and providing a concise movie concept overview.