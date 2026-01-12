# Getting Started Guide

Welcome to **Awesome LLM Apps**! This guide will walk you through setting up and running your first LLM application from this repository. Whether you're new to LLMs or just new to this repo, you'll be up and running in no time.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start (5 minutes)](#quick-start-5-minutes)
- [Step-by-Step Setup](#step-by-step-setup)
- [Your First App: AI Travel Agent](#your-first-app-ai-travel-agent)
- [Choosing Your Next App](#choosing-your-next-app)
- [Understanding App Categories](#understanding-app-categories)
- [Prerequisites by App Category](#prerequisites-by-app-category)
- [Working with Different LLM Providers](#working-with-different-llm-providers)
- [Running Local Models](#running-local-models)
- [Common Troubleshooting](#common-troubleshooting)
- [Next Steps](#next-steps)

---

## Prerequisites

Before you begin, make sure you have:

| Requirement | Minimum | Recommended | Check Command |
|-------------|---------|-------------|---------------|
| Python | 3.8+ | 3.10+ | `python --version` |
| pip | Latest | Latest | `pip --version` |
| Git | Any | Latest | `git --version` |
| RAM | 8GB | 16GB | - |
| Storage | 1GB | 10GB (for local models) | - |

<details>
<summary><strong>Installing Python (if needed)</strong></summary>

**macOS:**
```bash
brew install python
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install python3 python3-pip python3-venv
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/) and ensure "Add Python to PATH" is checked during installation.

</details>

---

## Quick Start (5 minutes)

For experienced developers who want to dive right in:

```bash
# 1. Clone the repository
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps

# 2. Validate your environment (optional but recommended)
python scripts/validate_env.py

# 3. Navigate to a starter app
cd starter_ai_agents/ai_travel_agent

# 4. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 5. Install dependencies
pip install -r requirements.txt

# 6. Set your API key
export OPENAI_API_KEY='your-key-here'  # On Windows: set OPENAI_API_KEY=your-key-here

# 7. Run the app
streamlit run travel_agent.py
```

---

## Step-by-Step Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps
```

### Step 2: Create a Virtual Environment

Using a virtual environment keeps your project dependencies isolated:

```bash
# Create the virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

You'll know it's activated when you see `(venv)` at the beginning of your terminal prompt.

### Step 3: Validate Your Environment

Run the environment validation script to check your setup:

```bash
python scripts/validate_env.py
```

This will show you:
- Which LLM providers you have configured
- Which packages are installed
- Any missing dependencies

**Example output:**
```
🔍 Awesome LLM Apps - Environment Validator

LLM Provider Status
==================================================

OpenAI:
  ✓ Ready to use

Anthropic (Claude):
  ✗ API Key: Not configured
    Set one of: ANTHROPIC_API_KEY
    Get key at: https://console.anthropic.com/settings/keys

...

Summary
==================================================
LLM Providers: 1/9 configured
  Ready: OpenAI
```

### Step 4: Get Your API Keys

You'll need at least one LLM provider API key. Here are your options:

| Provider | Free Tier | Sign Up | Best For |
|----------|-----------|---------|----------|
| **OpenAI** | $5 credit | [platform.openai.com](https://platform.openai.com) | Most apps, best compatibility |
| **Google (Gemini)** | Generous free tier | [aistudio.google.com](https://aistudio.google.com) | Cost-effective, multimodal |
| **Anthropic** | $5 credit | [console.anthropic.com](https://console.anthropic.com) | Complex reasoning |
| **Groq** | Free tier | [console.groq.com](https://console.groq.com) | Fast inference |
| **xAI (Grok)** | Free tier | [console.x.ai](https://console.x.ai) | Real-time data |

**Recommendation:** Start with **OpenAI** or **Google Gemini** as they're supported by the most apps.

### Step 5: Set Up Your API Keys

You can set API keys in two ways:

**Option A: Environment Variables (recommended for testing)**
```bash
# macOS/Linux
export OPENAI_API_KEY='sk-your-key-here'

# Windows Command Prompt
set OPENAI_API_KEY=sk-your-key-here

# Windows PowerShell
$env:OPENAI_API_KEY='sk-your-key-here'
```

**Option B: Create a .env File (recommended for development)**

Create a `.env` file in the app directory:
```bash
# .env
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
GOOGLE_API_KEY=your-key-here
```

> **Security Note:** Never commit `.env` files to git. They're already in `.gitignore`.

---

## Your First App: AI Travel Agent

Let's run the AI Travel Agent - a beginner-friendly app that creates personalized travel itineraries.

### Why Start Here?

- 🟢 **Beginner-friendly** - Simple setup with clear output
- 🎯 **Practical** - Creates something useful you can actually use
- 📝 **Well-documented** - Easy to understand and modify
- 🔄 **Has local variant** - Can run without cloud APIs

### Running the App

```bash
# Navigate to the app directory
cd starter_ai_agents/ai_travel_agent

# Install dependencies
pip install -r requirements.txt

# Run the cloud version (requires OpenAI API key)
streamlit run travel_agent.py

# OR run the local version (requires Ollama)
streamlit run local_travel_agent.py
```

### What to Expect

1. Your browser will open to `http://localhost:8501`
2. Enter a destination (e.g., "Tokyo, Japan")
3. Specify trip duration (e.g., "5 days")
4. Click "Generate Itinerary"
5. Get a detailed day-by-day travel plan!

### Understanding the Code

The app has two main components:

```
ai_travel_agent/
├── travel_agent.py        # Main app (uses OpenAI)
├── local_travel_agent.py  # Local variant (uses Ollama)
├── requirements.txt       # Dependencies
└── README.md              # Documentation
```

**Key concepts demonstrated:**
- AI Agent architecture (Researcher + Planner)
- Web search integration (SerpAPI)
- Streamlit UI framework
- Calendar export functionality

---

## Choosing Your Next App

After the Travel Agent, here are recommended paths based on your interests:

### By Interest Area

<details>
<summary><strong>I want to analyze data or documents</strong></summary>

**Start with:**
1. [Chat with PDF](advanced_llm_apps/chat_with_X_tutorials/chat_with_pdf/) - Ask questions about PDF documents
2. [AI Data Analysis Agent](starter_ai_agents/ai_data_analysis_agent/) - Analyze datasets with AI
3. [Basic RAG Chain](rag_tutorials/rag_chain/) - Learn RAG fundamentals

**Prerequisites:** OpenAI or Anthropic API key

</details>

<details>
<summary><strong>I want to build with local/free models</strong></summary>

**Start with:**
1. [Local RAG Agent](rag_tutorials/local_rag_agent/) - RAG without cloud APIs
2. [Llama 3.1 Local RAG](rag_tutorials/llama3.1_local_rag/) - Use Meta's Llama model
3. [Deepseek Local RAG Agent](rag_tutorials/deepseek_local_rag_agent/) - Use Deepseek model

**Prerequisites:** [Ollama](https://ollama.ai) installed

</details>

<details>
<summary><strong>I want to explore multi-agent systems</strong></summary>

**Start with:**
1. [AI Finance Agent Team](advanced_ai_agents/multi_agent_apps/agent_teams/ai_finance_agent_team/) - Multiple agents working together
2. [Multi-Agent Researcher](advanced_ai_agents/multi_agent_apps/multi_agent_researcher/) - Collaborative research
3. [AI Teaching Agent Team](advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/) - Educational agents

**Prerequisites:** Intermediate Python, understanding of agent concepts

</details>

<details>
<summary><strong>I want to work with voice/audio</strong></summary>

**Start with:**
1. [AI Blog to Podcast Agent](starter_ai_agents/ai_blog_to_podcast_agent/) - Convert text to audio
2. [AI Audio Tour Agent](voice_ai_agents/ai_audio_tour_agent/) - Voice-guided experiences
3. [Customer Support Voice Agent](voice_ai_agents/customer_support_voice_agent/) - Voice interactions

**Prerequisites:** ElevenLabs API key (for TTS)

</details>

### By Complexity Level

| Level | Apps | Time to Run | Prerequisites |
|-------|------|-------------|---------------|
| 🟢 **Beginner** | [Starter AI Agents](starter_ai_agents/) | 5-15 min | 1 API key, basic Python |
| 🟡 **Intermediate** | [Single Agent Apps](advanced_ai_agents/single_agent_apps/), [RAG Tutorials](rag_tutorials/) | 15-30 min | 2-3 API keys, some RAG knowledge |
| 🔴 **Advanced** | [Agent Teams](advanced_ai_agents/multi_agent_apps/agent_teams/), [MCP Agents](mcp_ai_agents/) | 30-60+ min | Multiple services, advanced concepts |

---

## Understanding App Categories

### Directory Structure Overview

```
awesome-llm-apps/
├── starter_ai_agents/          # 🟢 Beginner-friendly agents
├── advanced_ai_agents/         # 🟡🔴 Complex agent implementations
│   ├── single_agent_apps/      #    Single-purpose agents
│   ├── multi_agent_apps/       #    Multiple collaborating agents
│   └── autonomous_game_playing_agent_apps/  # Game AI
├── rag_tutorials/              # 🟢🟡 Retrieval-Augmented Generation
├── advanced_llm_apps/          # 🟡 Various LLM applications
│   ├── chat_with_X_tutorials/  #    Chat interfaces for data
│   ├── llm_apps_with_memory_tutorials/  # Memory patterns
│   └── llm_finetuning_tutorials/        # Model fine-tuning
├── voice_ai_agents/            # 🟡 Voice-enabled applications
├── mcp_ai_agents/              # 🔴 Model Context Protocol agents
├── ai_agent_framework_crash_course/    # Framework tutorials
└── scripts/                    # Utility scripts
```

### What Each Category Offers

| Category | What You'll Learn | Example Apps |
|----------|-------------------|--------------|
| **Starter AI Agents** | Agent basics, tool usage, simple architectures | Travel Agent, Finance Agent, Data Analysis |
| **RAG Tutorials** | Retrieval, embeddings, vector stores | Agentic RAG, Hybrid Search, Vision RAG |
| **Chat with X** | Building conversational interfaces | Chat with PDF, GitHub, Gmail, YouTube |
| **Multi-Agent** | Agent collaboration, task delegation | Finance Team, Research Team, Legal Team |
| **Voice Agents** | Speech-to-text, text-to-speech | Audio Tours, Voice Support |
| **MCP Agents** | Model Context Protocol, tool integration | Browser Agent, GitHub Agent, Notion Agent |

---

## Working with Different LLM Providers

Most apps support multiple LLM providers. Here's how to switch between them:

### Provider Comparison

| Provider | Strengths | Common Use Cases | API Key Env Var |
|----------|-----------|------------------|-----------------|
| **OpenAI** | Widely supported, strong performance | Most apps | `OPENAI_API_KEY` |
| **Anthropic** | Excellent reasoning, safety | Complex analysis | `ANTHROPIC_API_KEY` |
| **Google** | Multimodal, generous free tier | Vision, cost-sensitive | `GOOGLE_API_KEY` |
| **Groq** | Very fast inference | Real-time apps | `GROQ_API_KEY` |
| **xAI** | Real-time knowledge | Current events | `XAI_API_KEY` |

### Switching Providers in Code

Many apps use the Agno framework which makes switching easy:

```python
# Using OpenAI
from agno.agent import Agent
from agno.models.openai import OpenAIChat

agent = Agent(model=OpenAIChat(id="gpt-4o"))

# Switch to Anthropic
from agno.models.anthropic import Claude

agent = Agent(model=Claude(id="claude-3-5-sonnet-20241022"))

# Switch to Google
from agno.models.google import Gemini

agent = Agent(model=Gemini(id="gemini-2.0-flash-exp"))
```

---

## Running Local Models

Want to run LLMs on your own machine? Here's how:

### Setting Up Ollama

[Ollama](https://ollama.ai) is the easiest way to run local models.

```bash
# 1. Install Ollama
# macOS:
brew install ollama

# Linux:
curl -fsSL https://ollama.ai/install.sh | sh

# Windows:
# Download from https://ollama.ai/download

# 2. Start Ollama service
ollama serve

# 3. Pull a model (in a new terminal)
ollama pull llama3.1        # Meta's Llama 3.1 (4.7GB)
ollama pull qwen2.5         # Alibaba's Qwen 2.5 (4.4GB)
ollama pull deepseek-r1     # DeepSeek reasoning model

# 4. Test it
ollama run llama3.1 "Hello, how are you?"
```

### Running Local Variants

Many apps have local versions. Look for:
- Files named `*_local.py` or `local_*.py`
- Directories with "local" in the name
- README sections mentioning Ollama

**Example:**
```bash
cd starter_ai_agents/ai_travel_agent

# Instead of:
streamlit run travel_agent.py

# Run local version:
streamlit run local_travel_agent.py
```

### Local Model Requirements

| Model | RAM Required | GPU Recommended | Good For |
|-------|--------------|-----------------|----------|
| `llama3.1:8b` | 8GB | Optional | General use |
| `qwen2.5:7b` | 8GB | Optional | Coding, Chinese |
| `deepseek-r1:7b` | 8GB | Optional | Reasoning |
| `llama3.1:70b` | 64GB | Required | Complex tasks |

---

## Common Troubleshooting

### Installation Issues

<details>
<summary><strong>"pip: command not found"</strong></summary>

Try using `pip3` instead:
```bash
pip3 install -r requirements.txt
```

Or ensure Python is properly installed:
```bash
python -m pip install -r requirements.txt
```

</details>

<details>
<summary><strong>"ModuleNotFoundError: No module named 'xyz'"</strong></summary>

1. Ensure your virtual environment is activated:
   ```bash
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate     # Windows
   ```

2. Reinstall requirements:
   ```bash
   pip install -r requirements.txt
   ```

3. Check if the package name differs from import name:
   ```bash
   pip install python-dotenv  # Package name
   # Imports as: from dotenv import load_dotenv
   ```

</details>

<details>
<summary><strong>"Permission denied" errors</strong></summary>

**macOS/Linux:**
```bash
# Don't use sudo with pip in a virtual environment
# Instead, ensure venv is properly activated

# If needed, fix permissions:
chmod +x venv/bin/activate
```

**Windows:**
- Run Command Prompt as Administrator
- Or check your antivirus isn't blocking Python

</details>

### API Key Issues

<details>
<summary><strong>"Invalid API key" or "Authentication error"</strong></summary>

1. Verify your key is correct (no extra spaces):
   ```bash
   echo $OPENAI_API_KEY  # Should show your key
   ```

2. Check the key is for the right service:
   - OpenAI keys start with `sk-`
   - Anthropic keys start with `sk-ant-`

3. Ensure the key is active in your provider's dashboard

4. Try regenerating the key if issues persist

</details>

<details>
<summary><strong>"Rate limit exceeded" or "Quota exceeded"</strong></summary>

1. **Rate limits**: Add delays between requests or wait a few minutes

2. **Quota exceeded**:
   - Check your usage at provider's dashboard
   - Upgrade your plan or add payment method
   - Switch to a provider with remaining quota

3. **Free tier limits**: Consider upgrading or using local models

</details>

<details>
<summary><strong>API key not being read from .env file</strong></summary>

1. Ensure `.env` file is in the correct directory (same as the script)

2. Check file format (no quotes needed for most tools):
   ```bash
   # Correct
   OPENAI_API_KEY=sk-your-key-here

   # May cause issues
   OPENAI_API_KEY="sk-your-key-here"
   ```

3. Ensure python-dotenv is installed:
   ```bash
   pip install python-dotenv
   ```

</details>

### Runtime Issues

<details>
<summary><strong>Streamlit app won't start</strong></summary>

1. Check if the port is already in use:
   ```bash
   # Use a different port
   streamlit run app.py --server.port 8502
   ```

2. Clear Streamlit cache:
   ```bash
   streamlit cache clear
   ```

3. Check for syntax errors:
   ```bash
   python -m py_compile app.py
   ```

</details>

<details>
<summary><strong>Ollama "connection refused"</strong></summary>

1. Ensure Ollama is running:
   ```bash
   ollama serve
   ```

2. Check if it's using the expected port:
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. Restart Ollama if needed:
   ```bash
   # macOS
   brew services restart ollama

   # Linux (systemd)
   sudo systemctl restart ollama
   ```

</details>

<details>
<summary><strong>App runs but gives poor/wrong results</strong></summary>

1. **Check your model**: Ensure you're using an appropriate model for the task

2. **Verify API key permissions**: Some keys have limited model access

3. **Check input format**: Some apps expect specific input formats

4. **Review the README**: Look for example prompts or usage guidelines

5. **Try a simpler query first**: Test with basic inputs to ensure the app works

</details>

### Getting More Help

If you're still stuck:

1. **Check the app's README** - Most issues are covered there
2. **Search existing issues** - Someone may have had the same problem
3. **Open a new issue** - Use the [question label](https://github.com/Shubhamsaboo/awesome-llm-apps/issues/new)
4. **Join discussions** - Ask in [GitHub Discussions](https://github.com/Shubhamsaboo/awesome-llm-apps/discussions)

---

## Next Steps

Congratulations on running your first LLM app! Here's what to do next:

### Learn More

1. **Understand the code** - Read through the app you just ran
2. **Modify it** - Change prompts, models, or add features
3. **Try another app** - Pick from the [recommendations above](#choosing-your-next-app)

### Level Up Your Skills

| Goal | Recommended Path |
|------|------------------|
| Learn RAG | [Basic RAG Chain](rag_tutorials/rag_chain/) → [Agentic RAG](rag_tutorials/agentic_rag_with_reasoning/) |
| Build agents | [Starter Agents](starter_ai_agents/) → [Single Agents](advanced_ai_agents/single_agent_apps/) → [Agent Teams](advanced_ai_agents/multi_agent_apps/agent_teams/) |
| Go local | [Local RAG](rag_tutorials/local_rag_agent/) → [Llama RAG](rag_tutorials/llama3.1_local_rag/) |
| Learn frameworks | [Google ADK Course](ai_agent_framework_crash_course/google_adk_crash_course/) or [OpenAI SDK Course](ai_agent_framework_crash_course/openai_sdk_crash_course/) |

### Contribute

Found a bug? Have an improvement? Want to add your own app?

- Read the [Contributing Guide](CONTRIBUTING.md)
- Check out [good first issues](https://github.com/Shubhamsaboo/awesome-llm-apps/labels/good%20first%20issue)
- Join the community!

---

## Quick Reference Card

### Essential Commands

```bash
# Clone repo
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git

# Create virtual environment
python -m venv venv && source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Validate environment
python scripts/validate_env.py

# Run Streamlit app
streamlit run app.py

# Run Python script
python script.py

# Pull Ollama model
ollama pull llama3.1
```

### Environment Variables

```bash
# LLM Providers
export OPENAI_API_KEY='sk-...'
export ANTHROPIC_API_KEY='sk-ant-...'
export GOOGLE_API_KEY='...'
export GROQ_API_KEY='gsk_...'
export XAI_API_KEY='xai-...'

# Common Services
export TAVILY_API_KEY='tvly-...'
export SERPER_API_KEY='...'
export ELEVENLABS_API_KEY='...'
```

### Useful Links

- [Repository](https://github.com/Shubhamsaboo/awesome-llm-apps)
- [Contributing Guide](CONTRIBUTING.md)
- [OpenAI Docs](https://platform.openai.com/docs)
- [Anthropic Docs](https://docs.anthropic.com)
- [Streamlit Docs](https://docs.streamlit.io)
- [Ollama](https://ollama.ai)

---

Happy building! 🚀

*If this guide helped you, consider giving the repo a ⭐ star!*
