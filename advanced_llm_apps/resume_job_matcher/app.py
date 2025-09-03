import streamlit as st
import requests
import fitz  # PyMuPDF for PDF parsing

st.set_page_config(page_title="📄 Resume & Job Matcher", layout="centered")

st.title("📄 Resume & Job Matcher")

st.sidebar.info("""
This app uses a local LLM via **Ollama**.
1. Install Ollama: https://ollama.ai
2. Run a model (e.g., `ollama run llama3`).
3. Upload a Resume + Job Description to get a fit score and suggestions.
""")

# Helper: Extract text from PDF
def extract_pdf_text(file):
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# File uploaders
resume_file = st.file_uploader("Upload Resume (PDF/TXT)", type=["pdf", "txt"])
job_file = st.file_uploader("Upload Job Description (PDF/TXT)", type=["pdf", "txt"])

if st.button("🔍 Match Resume with Job Description"):
    if resume_file and job_file:
        # Extract Resume text
        if resume_file.type == "application/pdf":
            resume_text = extract_pdf_text(resume_file)
        else:
            resume_text = resume_file.read().decode("utf-8")

        # Extract Job text
        if job_file.type == "application/pdf":
            job_text = extract_pdf_text(job_file)
        else:
            job_text = job_file.read().decode("utf-8")

        # Prompt
        prompt = f"""
        You are an AI career assistant.
        
        Resume:
        {resume_text}

        Job Description:
        {job_text}

        Please analyze and return:
        1. A **Fit Score** (0-100%) of how well this resume matches the job.
        2. Key strengths (resume areas that align well).
        3. Specific recommendations to improve the resume to better fit the job.
        Format neatly in Markdown.
        """

        try:
            with st.spinner("⏳ Analyzing Resume vs Job Description..."):
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={"model": "llama3", "prompt": prompt, "stream": False},
                )
                data = response.json()
                output = data.get("response", "⚠️ No response from model.")

            # Show Results
            st.subheader("📌 Match Analysis")
            st.markdown(output)

            # Save in session for download
            st.session_state["resume_match"] = output

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    else:
        st.warning("⚠️ Please upload both Resume and Job Description.")

# Download button
if "resume_match" in st.session_state:
    st.download_button(
        "💾 Download Match Report",
        st.session_state["resume_match"],
        file_name="resume_match_report.md",
        mime="text/markdown"
    )
