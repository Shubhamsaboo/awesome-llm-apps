
# 💔 Breakup Recovery Agent Team

This is an AI-powered application designed to help users emotionally recover from breakups by providing support, guidance, and emotional outlet messages from a team of specialized AI agents. The app is built using **Streamlit** and **Agno**, leveraging **OpenAI's GPT models**.

## 🚀 Features

- 🧠 **Multi-Agent Team:** 
    - **Therapist Agent:** Offers empathetic support and coping strategies.
    - **Closure Agent:** Writes emotional messages users shouldn't send for catharsis.
    - **Routine Planner Agent:** Suggests daily routines for emotional recovery.
    - **Brutal Honesty Agent:** Provides direct, no-nonsense feedback on the breakup.
- 📷 **Chat Screenshot Analysis:** (Planned)
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
- **AI Models:** OpenAI GPT-4o (via Agno)
- **Image Processing:** PIL (for displaying screenshots)
- **Text Extraction:** EasyOCR (planned feature for extracting text from screenshots)
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

Make sure to provide your **OpenAI API key** in the Streamlit sidebar:

- `OpenAI API Key` → Add your API key in the sidebar form.

---

## 🛠️ Usage

1. **Enter Your Feelings:** 
    - Describe how you're feeling in the text area.
2. **Upload Screenshot (Optional):**
    - Upload a chat screenshot (PNG, JPG, JPEG) for analysis (planned feature).
3. **Execute Agents:**
    - Click **"Get Recovery Support"** to run the multi-agent team.
4. **View Results:**
    - Individual agent responses are displayed.
    - A final summary is provided by the Team Leader.

---

## 🧑‍💻 Agents Overview

- **Therapist Agent**
    - Provides empathetic support and coping strategies.
    - Uses **OpenAI GPT-4o-mini** and DuckDuckGo tools for insights.
  
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

## 🔥 Future Enhancements

- ✅ **Text Extraction from Screenshots:** 
    - Use EasyOCR to extract text from uploaded screenshots for chat analysis.
- ✅ **Improved Image Analysis:** 
    - Integrate image analysis tools for detecting visual patterns in chat screenshots.

---

## 📄 License

This project is licensed under the **MIT License**.

---
