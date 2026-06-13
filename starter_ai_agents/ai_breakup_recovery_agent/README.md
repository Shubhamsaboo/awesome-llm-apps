# 💔 Breakup Recovery Agent Team

### 🎓 FREE Step-by-Step Tutorial 
**👉 [Click here to follow our complete step-by-step tutorial](https://www.theunwindai.com/p/build-an-ai-breakup-recovery-agent-team-f29b) and learn how to build this from scratch with detailed code walkthroughs, explanations, and best practices.**

This is an AI-powered application designed to help users emotionally recover from breakups by providing support, guidance, and emotional outlet messages from a team of specialized AI agents. The app is built using **Streamlit** and **Agno**, leveraging **OpenAI's GPT-4o (Vision Model)**.

## 🚀 Features

- 🧠 **Multi-Agent Team:** 
    - **Therapist Agent:** Offers empathetic support and coping strategies.
    - **Closure Agent:** Writes emotional messages users shouldn't send for catharsis.
    - **Routine Planner Agent:** Suggests daily routines for emotional recovery.
    - **Brutal Honesty Agent:** Provides direct, no-nonsense feedback on the breakup.
- 📷 **Chat Screenshot Analysis:**
    - Upload screenshots for chat analysis.
- 🔑 **API Key Management:**
    - Store and manage your OpenAI API keys securely via Streamlit's sidebar.
- ⚡ **Parallel Execution:** 
    - Agents process inputs in coordination mode for comprehensive results.
- ✅ **User-Friendly Interface:** 
    - Simple, intuitive UI with easy interaction and display of agent responses.

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit (Python)
- **AI Models:** OpenAI GPT-4o (Vision Model)
- **Image Processing:** PIL (for displaying screenshots)
- **Text Extraction:** OpenAI's GPT-4o to analyze chat screenshots
- **Environment Variables:** API keys managed with `st.session_state` in Streamlit

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

4. **Run the Streamlit App:**
   ```bash
   streamlit run ai_breakup_recovery_agent.py
   ```

---

## 🔑 Environment Variables

Make sure to provide your **OpenAI API key** in the Streamlit sidebar:

- OPENAI_API_KEY=your_openai_api_key

---

## 🛠️ Usage

1. **Enter Your Feelings:** 
    - Describe how you're feeling in the text area.
2. **Upload Screenshot (Optional):**
    - Upload a chat screenshot (PNG, JPG, JPEG) for analysis.
3. **Execute Agents:**
    - Click **"Get Recovery Support"** to run the multi-agent team.
4. **View Results:**
    - Individual agent responses are displayed.
    - A final summary is provided by the Team Leader.

---

## 🧑‍💻 Agents Overview

- **Therapist Agent**
    - Provides empathetic support and coping strategies.
    - Uses **OpenAI GPT-4o** and DuckDuckGo tools for insights.
  
- **Closure Agent**
    - Generates unsent emotional messages for emotional release.
    - Ensures heartfelt and authentic messages.

- **Routine Planner Agent**
    - Creates a daily recovery routine with balanced activities.
    - Includes self-reflection, social interaction, and healthy distractions.

- **Brutal Honesty Agent**
    - Offers direct, objective feedback on the breakup.
    - Uses factual language with no sugar-coating.