# AI Personal Learning Agent

A Personal learning assistant built on PraisonAI Framework that explains a particular topic, creates learning plans and roadmaps using multiple specialized AI agents which are self reflective and hierarchical. The system uses OpenAI's GPT-4o to generate comprehensive learning materials, roadmaps, and practice exercises.

## Features

- 🧠 Knowledge Building: Researches and creates comprehensive knowledge bases
- 🗺️ Learning Roadmaps: Generates structured learning paths with time estimates
- 📚 Resource Curation: Finds and validates high-quality learning materials
- ✍️ Practice Materials: Creates progressive exercises and projects
- 🔍 Internet Search Integration: Used a custom InternetSearchTool tool for real-time research
- 📊 Live Terminal Output: Shows real-time agent interactions in terminal - also in streamlit UI

## Agents

1. **KnowledgeBuilder**: Research specialist that gathers and organizes information
2. **RoadmapArchitect**: Curriculum designer that creates structured learning paths
3. **ResourceCurator**: Resource specialist that finds and validates learning materials
4. **PracticeDesigner**: Exercise creator that develops practice materials


## How to Run

1. Clone the repository
  ```bash
   # Clone the repository
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd ai_agent_tutorials/ai_personal_learning_agent

   # Install dependencies
   pip install -r requirements.txt
   ```

## Configuration

1. Get your OpenAI API Key
- Create an account on [OpenAI Platform](https://platform.openai.com/)
- Navigate to API Keys section
- Create a new API key

2. (Optional) Set up environment variables
```bash
export OPENAI_API_KEY='your-api-key-here'
```
This way of using the openai key is fundamental to how PraisonAI is designed - it initializes the OpenAI client at module import time, which means setting the environment variable after import won't help. We need to set the environment variable BEFORE importing PraisonAI. So, export way helps majorly - else if you want to use streamlit, keep the session state openai api key intializations before the imports of praisonAI

## Usage

1. Start the Streamlit app
```bash
streamlit run ai_personal_learning_agent.py
```

2. Use the application
- Enter your OpenAI API key in the sidebar (if not set in environment)
- Type a topic you want to learn about (e.g., "Python Programming", "Machine Learning")
- Click "Generate Learning Plan"
- Wait for the agents to generate your personalized learning plan
- View the results and terminal output in the interface