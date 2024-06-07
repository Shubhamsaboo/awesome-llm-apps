## 🛫 AI Travel Agent
This Streamlit app is an AI-powered travel Agent that generates personalized travel itineraries using OpenAI GPT-4o. It automates the process of researching, planning, and organizing your dream vacation, allowing you to explore exciting destinations with ease.

### Features
- Research and discover exciting travel destinations, activities, and accommodations
- Customize your itinerary based on the number of days you want to travel
- Utilize the power of GPT-4o to generate intelligent and personalized travel plans

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

4. Get your SerpAPI Key

- Sign up for an [SerpAPI account](https://serpapi.com/) and obtain your API key.

5. Run the Streamlit App
```bash
streamlit run travel_agent.py
```

### How it Works?

The AI Travel Agent has two main components:
- Researcher: Responsible for generating search terms based on the user's destination and travel duration, and searching the web for relevant activities and accommodations using SerpAPI.
- Planner: Takes the research results and user preferences to generate a personalized draft itinerary that includes suggested activiti