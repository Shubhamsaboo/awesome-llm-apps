# 💬 Streamlit RAG Chatbot (OpenRouter + PDF)

A minimal Retrieval-Augmented Generation (RAG) chatbot built with **Streamlit** and **OpenRouter API**.  
This version supports PDF uploads and uses extracted text as context — no database or storage.

---

## 🚀 Features
- Upload any `.pdf` document as context
- Uses OpenRouter API for LLM responses
- Stores chat history in session only
- No database, no persistence
- Clean modular codebase (`utils/pdf_reader.py`)

---

## 🧰 Tech Stack
- **UI:** Streamlit  
- **LLM Service:** OpenRouter  
- **PDF Parsing:** PyMuPDF  
- **Storage:** None (session memory only)

---

## ⚙️ Setup Instructions

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/streamlit-rag-openrouter.git
cd streamlit-rag-openrouter

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run Streamlit app
streamlit run app.py
