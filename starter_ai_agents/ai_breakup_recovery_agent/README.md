
# 💔 Breakup Recovery Agent Team

This is an AI-powered application designed to help users emotionally recover from breakups by providing support, guidance, and emotional outlet messages from a team of specialized AI agents. The app is built using **Streamlit** and **Agno**, leveraging **Gemini 2.0 Flash (Google Vision Model)   **.

## 🚀 Features

- 🧠 **Multi-Agent Team:** 
    - **Therapist Agent:** Offers empathetic support and coping strategies.
    - **Closure Agent:** Writes emotional messages users shouldn't send for catharsis.
    - **Routine Planner Agent:** Suggests daily routines for emotional recovery.
    - **Brutal Honesty Agent:** Provides direct, no-nonsense feedback on the breakup.
- 📷 **Chat Screenshot Analysis:**
    - Upload screenshots for chat analysis.
- 🔑 **API Key Management:**
    - Store and manage your Gemini API keys securely via Streamlit's sidebar.
- ⚡ **Parallel Execution:** 
    - Agents process inputs in coordination mode for comprehensive results.
- ✅ **User-Friendly Interface:** 
    - Simple, intuitive UI with easy interaction and display of agent responses.

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit (Python)
- **AI Models:** Gemini 2.0 Flash (Google Vision Model)
- **Image Processing:** PIL (for displaying screenshots)
- **Text Extraction:** Google's Gemini Vision model to analyze chat screenshots
- **Environment Variables:** API keys managed with `st.session_state` in Streamlit

---

## 📦 Installation

1. **Clone the Repository:**
   ```bash
   git clone <repository_url>
   cd breakup-recovery-agent-team
   ```

2. **Create a Virtual Environment (Optional but Recommended):**
   ```bash
   conda create --name <env_name> python=<version>
   conda activate <env_name>
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Streamlit App:**
   ```bash
   streamlit run app.py
   ```

---

## 🔑 Environment Variables

Make sure to provide your **Gemini API key** in the Streamlit sidebar:

- GEMINI_API_KEY=your_google_gemini_api_key

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
    - Uses **Gemini 2.0 Flash (Google Vision Model)** and DuckDuckGo tools for insights.
  
- **Closure Agent**
    - Generates unsent emotional messages for emotional release.
    - Ensures heartfelt and authentic messages.

- **Routine Planner Agent**
    - Creates a daily recovery routine with balanced activities.
    - Includes self-reflection, social interaction, and healthy distractions.

- **Brutal Honesty Agent**
    - Offers direct, objective feedback on the breakup.
    - Uses factual language with no sugar-coating.

---


## 📄 License

This project is licensed under the **MIT License**.

---
