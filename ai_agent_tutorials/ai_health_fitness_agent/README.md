# AI Health & Fitness Planner Agent 🏋️‍♂️

The **AI Health & Fitness Planner** is a personalized health and fitness Agent powered by Phidata's AI Agent framework. This app generates tailored dietary and fitness plans based on user inputs such as age, weight, height, activity level, dietary preferences, and fitness goals.

Here's a small demo of the application: 

[Watch the demo video here](https://drive.google.com/file/d/1ZdAihfg9NuEnqEFTdDWyRqVe7qTWdz80/view?usp=sharing)


https://github.com/user-attachments/assets/0061d3e9-e2dc-49a7-8710-5cea7fe08741


---

## Features

- **Health Agent and Fitness Agent**
    - The app has two phidata agents that are specialists in giving Diet advice and Fitness/workout advice respectively.

- **Personalized Dietary Plans**:
  - Generates detailed meal plans (breakfast, lunch, dinner, and snacks).
  - Includes important considerations like hydration, electrolytes, and fiber intake.
  - Supports various dietary preferences like Keto, Vegetarian, Low Carb, etc.

- **Personalized Fitness Plans**:
  - Provides customized exercise routines based on fitness goals.
  - Covers warm-ups, main workouts, and cool-downs.
  - Includes actionable fitness tips and progress tracking advice.

- **Interactive Q&A**:
  - Allows users to ask follow-up questions about their plans.
  - Provides AI-generated responses for personalized guidance.

---

## Requirements

The application requires the following Python libraries:

- `phidata`
- `google-generativeai`
- `anthropic`
- `streamlit`

Ensure these dependencies are installed via the `requirements.txt` file according to their mentioned versions

---

## How to Run

Follow the steps below to set up and run the application:
Before anything else, Please get a free Gemini API Key provided by Google AI here: https://aistudio.google.com/apikey



1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd ai_agent_tutorials```

2. **Install the dependencies**
    ```bash
    pip install -r requirements.txt
    ```
3. **Run the Streamlit App(s)**
    If you run the application:
    ```bash
    streamlit run ai_health-fitness_agent/health_agent.py
    ```


