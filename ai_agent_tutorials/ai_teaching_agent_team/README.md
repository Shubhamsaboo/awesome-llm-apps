# 👨‍🏫 AI Teaching Agent Team

A Streamlit application that brings together a team of specialized AI teaching agents who collaborate like a professional teaching faculty. Each agent acts as a specialized educator: a curriculum designer, learning path expert, resource librarian, and practice instructor - working together to create a complete educational experience through Google Docs.

## 🪄 Meet your AI Teaching Agent Team 

#### 🧠 Professor Agent
- Creates fundamental knowledge base in Google Docs
- Organizes content with proper headings and sections
- Includes detailed explanations and examples
- Output: Comprehensive knowledge base document with table of contents

#### 🗺️ Academic Advisor Agent
- Designs learning path in a structured Google Doc
- Creates progressive milestone markers
- Includes time estimates and prerequisites
- Output: Visual roadmap document with clear progression paths

#### 📚 Research Librarian Agent
- Compiles resources in an organized Google Doc
- Includes links to academic papers and tutorials
- Adds descriptions and difficulty levels
- Output: Categorized resource list with quality ratings

#### ✍️ Teaching Assistant Agent
- Develops exercises in an interactive Google Doc
- Creates structured practice sections
- Includes solution guides
- Output: Complete practice workbook with answers


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
- **IMPORTANT** - For you to use the app, you need to make new connection ID with google docs and composio.Follow the below two steps to do so:  
  - composio add googledocs (IN THE TERMINAL)
  - Create a new connection 
  - Select OAUTH2 
  - Select Google Account and Done.
  - On the composio account website, go to apps, select google docs tool, and [click create integration](https://app.composio.dev/app/googledocs) (violet button) and click Try connecting default’s googldocs button and we are done. 

3. Sign up and get the [SerpAPI Key](https://serpapi.com/)

## How to Use? 

1. Start the Streamlit app
```bash
streamlit run teaching_agent_team.py
```

2. Use the application
- Enter your OpenAI API key in the sidebar (if not set in environment)
- Enter your Composio API key in the sidebar 
- Type a topic you want to learn about (e.g., "Python Programming", "Machine Learning")
- Click "Generate Learning Plan"
- Wait for the agents to generate your personalized learning plan
- View the results and terminal output in the interface
