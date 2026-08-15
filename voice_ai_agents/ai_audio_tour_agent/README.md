# 🎧 Self-Guided AI Audio Tour Agent

### 🎓 FREE Step-by-Step Tutorial 
**👉 [Click here to follow our complete step-by-step tutorial](https://www.theunwindai.com/p/build-a-self-guided-ai-audio-tour-agent) and learn how to build this from scratch with detailed code walkthroughs, explanations, and best practices.**

A conversational voice agent system that generates immersive, self-guided audio tours based on the user’s **location**, **areas of interest**, and **tour duration**. Built on a multi-agent architecture using OpenAI Agents SDK, real-time information retrieval, and expressive TTS for natural speech output.

---

## 🚀 Features

### 🎙️ Multi-Agent Architecture

- **Orchestrator Agent**  
  Coordinates the overall tour flow, manages transitions, and assembles content from all expert agents.

- **History Agent**  
  Delivers insightful historical narratives with an authoritative voice.

- **Architecture Agent**  
  Highlights architectural details, styles, and design elements using a descriptive and technical tone.

- **Culture Agent**  
  Explores local customs, traditions, and artistic heritage with an enthusiastic voice.

- **Culinary Agent**  
  Describes iconic dishes and food culture in a passionate and engaging tone.

---

### 📍 Location-Aware Content Generation

- Dynamic content generation based on user-input **location**
- Real-time **web search integration** to fetch relevant, up-to-date details
- Personalized content delivery filtered by user **interest categories**

---

### ⏱️ Customizable Tour Duration

- Selectable tour length: **15, 30, or 60 minutes**
- Time allocations adapt to user interest weights and location relevance
- Ensures well-paced and proportioned narratives across sections

---

### 🔊 Expressive Speech Output

- High-quality audio generated using **Gpt-4o Mini Audio**

### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd voice_ai_agents/ai_audio_tour_agent
```
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```
3. Get your OpenAI API Key

- Sign up for an [OpenAI account](https://platform.openai.com/) (or the LLM provider of your choice) and obtain your API key.

4. Run the Streamlit App
```bash
streamlit run ai_audio_tour_agent.py
```

