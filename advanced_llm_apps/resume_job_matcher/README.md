# 📄 Resume & Job Matcher

## 🚀 Overview
This app allows you to upload a **Resume** and a **Job Description**, then uses an LLM to:
- ✅ Provide a **Fit Score** (0–100%)
- 💪 Highlight strengths in the resume
- 📝 Suggest improvements tailored to the job

A great tool for job seekers to optimize resumes for each application.

---

## 🛠️ Tech Stack
- **Python**
- **Streamlit** – for UI
- **Ollama + LLM** (e.g., `llama3`) – for analysis
- **PyMuPDF** – for PDF parsing

---

## ⚡ Setup Instructions 
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
2. Install Ollama and run a model (e.g. llama3): `ollama run llama3`
3. Start the app: `streamlit run app.py`
