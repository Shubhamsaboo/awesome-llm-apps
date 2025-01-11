# AI Personal Learning Agent

A Personal learning Roadmap Architect assistant built on Phidata Framework that explains a particular topic, creates learning plans and roadmaps using multiple specialized AI agents which are hierarchical. The system uses OpenAI's GPT-4o to generate comprehensive learning materials, roadmaps, and practice exercises. This uses streamlit for UI.

## Demo


https://github.com/user-attachments/assets/67e81377-d80e-4221-b1f2-e25cffb71c93



## Features

- 🧠 Knowledge Building: Researches and creates comprehensive knowledge bases
- 🗺️ Learning Roadmaps: Generates structured learning paths with time estimates
- 📚 Resource Curation: Finds and validates high-quality learning materials
- ✍️ Practice Materials: Creates progressive exercises and projects
- 🔍 Internet Search Integration: Used a DuckDuckGo tool for real-time research
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

## Configuration - IMPORTANT STEP

1. Get your OpenAI API Key
- Create an account on [OpenAI Platform](https://platform.openai.com/)
- Navigate to API Keys section
- Create a new API key

2. Get your Composio API Key
- Create an account on [Composio Platform](https://composio.ai/)
- [IMPORTANT] - For you to use the app, you need to make new connection ID with google docs and composio.Follow the below two steps to do so:  
- composio add googledocs (IN THE TERMINAL) -> Create a new connection -> Select OAUTH2 -> Select Google Account and Done.
- In the composio account website, go to apps, select google docs tool, and click create integration (violet button) and click Try connecting default’s googldocs button and we are done. (https://app.composio.dev/app/googledocs )

## Usage

1. Start the Streamlit app
```bash
streamlit run ai_personal_learning_agent.py
```

2. Use the application
- Enter your OpenAI API key in the sidebar (if not set in environment)
- Enter your Composio API key in the sidebar 
- Type a topic you want to learn about (e.g., "Python Programming", "Machine Learning")
- Click "Generate Learning Plan"
- Wait for the agents to generate your personalized learning plan
- View the results and terminal output in the interface
