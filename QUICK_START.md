# 🚀 Quick Start Guide

Get up and running with Awesome LLM Apps in 5 minutes!

## ⚡ Super Quick Start (3 Steps)

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies for a specific agent
cd starter_ai_agents/ai_travel_agent
pip install -r requirements.txt
```

### 2. Set Up API Keys

Create a `.env` file in the agent directory:

```bash
OPENAI_API_KEY=sk-your-key-here
```

### 3. Run Your First Agent

```bash
streamlit run ai_travel_agent.py
```

🎉 **That's it!** Your AI agent is now running at `http://localhost:8501`

---

## 📚 Detailed Setup Guide

### Prerequisites

- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **Git** ([Download](https://git-scm.com/downloads))
- **API Keys** (at least one):
  - [OpenAI API Key](https://platform.openai.com/api-keys)
  - [Anthropic API Key](https://console.anthropic.com/)
  - [Google AI API Key](https://makersuite.google.com/app/apikey)

### Step-by-Step Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps
```

#### 2. Choose Your Agent

Browse the available agents:

```bash
# Starter agents (beginner-friendly)
ls starter_ai_agents/

# Advanced agents (more complex)
ls advanced_ai_agents/

# RAG tutorials
ls rag_tutorials/

# MCP agents
ls mcp_ai_agents/
```

#### 3. Navigate to Your Chosen Agent

```bash
# Example: AI Travel Agent
cd starter_ai_agents/ai_travel_agent
```

#### 4. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# Verify activation (you should see (venv) in your prompt)
```

#### 5. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Verify installation
pip list
```

#### 6. Configure API Keys

**Option A: Using .env file (Recommended)**

```bash
# Create .env file
# Windows:
copy .env.example .env

# macOS/Linux:
cp .env.example .env

# Edit .env file and add your API keys
# Use notepad, vim, or any text editor
notepad .env  # Windows
nano .env     # macOS/Linux
```

Example `.env` file:
```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
GOOGLE_API_KEY=xxxxxxxxxxxxx
```

**Option B: Using environment variables**

```bash
# Windows (PowerShell):
$env:OPENAI_API_KEY="sk-your-key-here"

# Windows (CMD):
set OPENAI_API_KEY=sk-your-key-here

# macOS/Linux:
export OPENAI_API_KEY=sk-your-key-here
```

#### 7. Run the Agent

```bash
# Run with Streamlit
streamlit run ai_travel_agent.py

# Or run with Python (if it's a CLI app)
python ai_travel_agent.py
```

#### 8. Open in Browser

Your default browser should open automatically to:
```
http://localhost:8501
```

If not, manually open the URL shown in the terminal.

---

## 🎯 Popular Agents to Try

### For Beginners

#### 1. AI Travel Agent
```bash
cd starter_ai_agents/ai_travel_agent
pip install -r requirements.txt
streamlit run ai_travel_agent.py
```
**What it does:** Plans trips, suggests destinations, creates itineraries

#### 2. AI Data Analysis Agent
```bash
cd starter_ai_agents/ai_data_analysis_agent
pip install -r requirements.txt
streamlit run ai_data_analyst.py
```
**What it does:** Analyzes CSV files, creates visualizations, provides insights

#### 3. AI Music Generator Agent
```bash
cd starter_ai_agents/ai_music_generator_agent
pip install -r requirements.txt
streamlit run music_generator_agent.py
```
**What it does:** Generates music based on prompts

### For Advanced Users

#### 1. AI Legal Agent Team
```bash
cd advanced_ai_agents/multi_agent_apps/agent_teams/ai_legal_agent_team
pip install -r requirements.txt
streamlit run legal_agent_team.py
```
**What it does:** Multi-agent team for legal document analysis

**Additional Setup:**
- Qdrant vector database (for document storage)
- See README in the directory for detailed setup

#### 2. AI Finance Agent Team
```bash
cd advanced_ai_agents/multi_agent_apps/agent_teams/ai_finance_agent_team
pip install -r requirements.txt
python finance_agent_team.py
```
**What it does:** Financial analysis and stock research

#### 3. Multi-Agent Researcher
```bash
cd advanced_ai_agents/multi_agent_apps/multi_agent_researcher
pip install -r requirements.txt
streamlit run research_agent.py
```
**What it does:** Conducts comprehensive research using multiple agents

---

## 🛠️ Common Setup Issues

### Issue: `ModuleNotFoundError`

**Solution:**
```bash
# Ensure you're in the correct directory
pwd  # or cd on Windows

# Ensure virtual environment is activated
# You should see (venv) in your prompt

# Reinstall requirements
pip install -r requirements.txt
```

### Issue: `API Key Not Found`

**Solution:**
```bash
# Check if .env file exists
ls -la  # macOS/Linux
dir     # Windows

# Verify .env file contents
cat .env  # macOS/Linux
type .env # Windows

# Ensure no extra spaces or quotes around keys
# Correct:   OPENAI_API_KEY=sk-xxxxx
# Incorrect: OPENAI_API_KEY = "sk-xxxxx"
```

### Issue: `Port Already in Use`

**Solution:**
```bash
# Use a different port
streamlit run app.py --server.port 8502

# Or kill the process using the port
# Windows:
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# macOS/Linux:
lsof -ti:8501 | xargs kill -9
```

### Issue: `Streamlit Not Found`

**Solution:**
```bash
# Install streamlit explicitly
pip install streamlit

# Verify installation
streamlit --version

# If still not found, use python -m
python -m streamlit run app.py
```

---

## 🎓 Learning Path

### Week 1: Basics
1. ✅ Set up environment
2. ✅ Run a starter agent
3. ✅ Understand the code structure
4. ✅ Modify prompts and see results

### Week 2: Customization
1. 📝 Create your own prompts
2. 🎨 Customize the UI
3. ⚙️ Add new features
4. 🧪 Experiment with different models

### Week 3: Advanced
1. 🤖 Build a multi-agent system
2. 📚 Add RAG capabilities
3. 🗄️ Integrate vector databases
4. 🚀 Deploy your agent

---

## 📖 Next Steps

After getting your first agent running:

1. **Read the Agent's README**: Each agent has specific documentation
2. **Explore the Code**: Understand how it works
3. **Modify and Experiment**: Change prompts, add features
4. **Check Other Agents**: Try different types of agents
5. **Join the Community**: Share your creations!

---

## 🔗 Useful Resources

### Documentation
- [Main README](README.md) - Project overview
- [Contributing Guide](CONTRIBUTING.md) - How to contribute
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
- [Bug Fixes](FIXES.md) - Recent fixes and updates

### External Resources
- [Streamlit Docs](https://docs.streamlit.io)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [Anthropic API Docs](https://docs.anthropic.com)
- [Agno Framework Docs](https://docs.agno.com)

### Video Tutorials
- [YouTube Channel](https://youtube.com/@unwindai) - Video tutorials
- [Project Demos](https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/demos)

---

## 💡 Pro Tips

### Tip 1: Use Environment Variables
```python
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
```

### Tip 2: Cache Expensive Operations
```python
import streamlit as st

@st.cache_resource
def load_model():
    return expensive_model_loading()
```

### Tip 3: Handle Errors Gracefully
```python
try:
    result = agent.run(query)
    st.success("✅ Success!")
except Exception as e:
    st.error(f"❌ Error: {str(e)}")
```

### Tip 4: Use Smaller Models for Testing
```python
# For testing (faster, cheaper)
model = OpenAIChat(id="gpt-4o-mini")

# For production (better quality)
model = OpenAIChat(id="gpt-4o")
```

### Tip 5: Monitor API Usage
- Check your API dashboard regularly
- Set up billing alerts
- Use rate limiting in production

---

## 🎯 Quick Commands Reference

```bash
# Virtual Environment
python -m venv venv                    # Create
venv\Scripts\activate                  # Activate (Windows)
source venv/bin/activate               # Activate (macOS/Linux)
deactivate                             # Deactivate

# Package Management
pip install -r requirements.txt        # Install all
pip install package_name               # Install one
pip list                               # List installed
pip freeze > requirements.txt          # Save current

# Streamlit
streamlit run app.py                   # Run app
streamlit run app.py --server.port 8502  # Custom port
streamlit cache clear                  # Clear cache

# Git
git clone <url>                        # Clone repo
git pull                               # Update repo
git status                             # Check status
```

---

## 🆘 Need Help?

- **Issues?** Check [Troubleshooting Guide](TROUBLESHOOTING.md)
- **Questions?** Open a [GitHub Issue](https://github.com/Shubhamsaboo/awesome-llm-apps/issues)
- **Want to Contribute?** Read [Contributing Guide](CONTRIBUTING.md)

---

**Happy Building! 🚀**

Remember: The best way to learn is by doing. Start with a simple agent, understand how it works, then build your own!
