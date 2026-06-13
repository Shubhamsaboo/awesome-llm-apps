# 💔 Breakup Recovery Agent Team

### 🎓 FREE Step-by-Step Tutorial 
**👉 [Click here to follow our complete step-by-step tutorial](https://www.theunwindai.com/p/build-an-ai-breakup-recovery-agent-team-f29b) and learn how to build this from scratch with detailed code walkthroughs, explanations, and best practices.**

This is an AI-powered application designed to help users emotionally recover from breakups by providing support, guidance, and emotional outlet messages from a team of specialized AI agents. The app is built using **Streamlit** and **Agno**, leveraging **Claude models via Anthropic API**.

## 🚀 Features

- 🧠 **Multi-Agent Team:** 
    - **Therapist Agent:** Offers empathetic support and coping strategies.
    - **Closure Agent:** Writes emotional messages users shouldn't send for catharsis.
    - **Routine Planner Agent:** Suggests daily routines for emotional recovery.
    - **Brutal Honesty Agent:** Provides direct, no-nonsense feedback on the breakup.
- 📷 **Chat Screenshot Analysis:**
    - Upload screenshots for chat analysis.
- 🔑 **JWT Authentication:**
    - Secure authentication via JWT tokens from configured infrastructure.
- ⚡ **Parallel Execution:** 
    - All 4 sub-agents run concurrently with asyncio (~2-3s latency).
- ✅ **User-Friendly Interface:** 
    - Simple, intuitive UI with easy interaction and display of agent responses.

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit (Python)
- **AI Models:** Claude via Anthropic API (configurable)
- **Image Processing:** PIL (for displaying screenshots)
- **Async Execution:** asyncio for parallel agent processing
- **Environment Variables:** Loaded from `.env` file (python-dotenv)

---

## 📦 Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps
   cd starter_ai_agents/ai_breakup_recovery_agent
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   ```bash
   # Copy template
   cp .env.example .env
   
   # Edit .env with your values
   nano .env
   ```

4. **Run the Streamlit App:**
   ```bash
   streamlit run ai_breakup_recovery_agent.py
   ```

---

## 🔑 Environment Variables

Create a `.env` file (copy from `.env.example`) and fill in your own values (required):

- `MY_LLM_MODEL` — LLM model alias
- `MY_LLM_ENDPOINT` — AI Gateway endpoint
- `MY_TOKEN_FILE` — Path to JWT token file
- `MY_TOKEN_REFRESH_SCRIPT` — Path to token refresh script

See `.env.example` for template.

---

## 🛠️ Usage

1. **Enter Your Feelings:** 
    - Describe how you're feeling in the text area.
2. **Upload Screenshots (Optional):**
    - Upload chat screenshots (PNG, JPG, JPEG) for context analysis.
3. **Execute Agents:**
    - Click **"Get Recovery Plan"** to run all 4 agents in parallel.
4. **View Results:**
    - Consolidated recovery roadmap synthesized from all agents.

---

## 🧑‍💻 Agents Overview

- **Therapist Agent**
    - Provides empathetic support and coping strategies.
    - Analyzes both text and image inputs for emotional context.
  
- **Closure Agent**
    - Generates unsent emotional messages for emotional release.
    - Ensures heartfelt and authentic messages.

- **Routine Planner Agent**
    - Creates a daily recovery routine with balanced activities.
    - Includes self-reflection, social interaction, and healthy distractions.

- **Brutal Honesty Agent**
    - Offers direct, objective feedback on the breakup.
    - Uses factual language with no sugar-coating.