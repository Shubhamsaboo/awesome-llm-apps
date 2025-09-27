## 🛫 AI Travel Agent
This Streamlit app is an AI-powered travel Agent that generates personalized travel itineraries using OpenAI GPT-4o. It automates the process of researching, planning, and organizing your dream vacation, allowing you to explore exciting destinations with ease.

### Features
- Research and discover exciting travel destinations, activities, and accommodations
- Customize your itinerary based on the number of days you want to travel
- Utilize the power of GPT-4o to generate intelligent and personalized travel plans
- Download your itinerary as a calendar (.ics) file to import into Google Calendar, Apple Calendar, or other calendar apps

### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/ai_agent_tutorials/ai_travel_agent
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

For local LLM usage (with Ollama):
```bash
streamlit run local_travel_agent.py
```

### How it Works?

The AI Travel Agent has two main components:
- **Researcher:** Responsible for generating search terms based on the user's destination and travel duration, and searching the web for relevant activities and accommodations using SerpAPI.
- **Planner:** Takes the research results and user preferences to generate a personalized draft itinerary that includes suggested activities, dining options, and accommodations.

### Using the Calendar Download Feature

After generating your travel itinerary:
1. Click the "Download Itinerary as Calendar (.ics)" button that appears next to the "Generate Itinerary" button
2. Save the .ics file to your computer
3. Import the file into your preferred calendar application (Google Calendar, Apple Calendar, Outlook, etc.)
4. Each day of your itinerary will appear as an all-day event in your calendar
5. The complete details for each day's activities are included in the event description

This feature makes it easy to keep track of your travel plans and have your itinerary available on all your devices, even offline.

### Local vs Cloud Version

- **travel_agent.py**: Uses OpenAI's GPT-4o for high-quality itineraries (requires OpenAI API key)
- **local_travel_agent.py**: Uses Ollama for local LLM inference without sending data to external APIs (requires Ollama to be installed and running)