# AI Mental Wellbeing Agent Team 🧠

The AI Mental Wellbeing Agent Team is a supportive mental health assessment and guidance system powered by [AG2](https://github.com/ag2ai/ag2?tab=readme-ov-file)(formerly AutoGen)'s AI Agent framework. This app provides personalized mental health support through the coordination of specialized AI agents, each focusing on different aspects of mental health care based on user inputs such as emotional state, stress levels, sleep patterns, and current symptoms. This is built on AG2's new swarm feature run through initiate_swarm_chat() method.

## Features

- **Specialized Mental Wellbeing Support Team**
    - 🧠 **Assessment Agent**: Analyzes emotional state and psychological needs with clinical precision and empathy
    - 🎯 **Action Agent**: Creates immediate action plans and connects users with appropriate resources
    - 🔄 **Follow-up Agent**: Designs long-term support strategies and prevention plans

- **Comprehensive Mental Wellbeing Support**:
  - Detailed psychological assessment
  - Immediate coping strategies
  - Resource recommendations
  - Long-term support planning
  - Crisis prevention strategies
  - Progress monitoring systems

- **Customizable Input Parameters**:
  - Current emotional state
  - Sleep patterns
  - Stress levels
  - Support system information
  - Recent life changes
  - Current symptoms

- **Interactive Results**: 
   - Real-time assessment summaries
   - Detailed recommendations in expandable sections
   - Clear action steps and resources
   - Long-term support strategies

## How to Run

Follow these steps to set up and run the application:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/multi_agent_apps/ai_mental_wellbeing_agent
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create Environment File**:
   Create a `.env` file in the project directory:
   ```bash
   echo "AUTOGEN_USE_DOCKER=0" > .env
   ```
   This disables Docker requirement for code execution in AutoGen.

4. **Set Up OpenAI API Key**:
   - Obtain an OpenAI API key from [OpenAI's platform](https://platform.openai.com)
   - You'll input this key in the app's sidebar when running

5. **Run the Streamlit App**:
   ```bash
   streamlit run ai_mental_wellbeing_agent.py
   ```


## ⚠️ Important Notice

This application is a supportive tool and does not replace professional mental health care. If you're experiencing thoughts of self-harm or severe crisis:

- Call National Crisis Hotline: 988
- Call Emergency Services: 911
- Seek immediate professional help

