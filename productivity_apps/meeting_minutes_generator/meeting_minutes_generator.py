import streamlit as st
import requests

# Title
st.title("📝 Meeting Minutes Generator (Open Source)")

st.sidebar.info("""
This app uses a local LLM via Ollama.
1. Install Ollama: https://ollama.ai
2. Run a model (e.g., `ollama run llama3`).
3. Upload your Zoom/Teams/Meet transcript to generate minutes.
""")

# File uploader
uploaded_file = st.file_uploader("Upload Transcript File (.txt or .vtt)", type=["txt", "vtt"])

if uploaded_file is not None:
    transcript_text = uploaded_file.read().decode("utf-8")

    if st.button("Generate Meeting Minutes"):
        try:
            prompt = f"""
            You are an AI assistant that generates professional meeting minutes.

            Transcript:
            {transcript_text}

            Please provide:
            1. A concise meeting summary
            2. Key decisions made
            3. Action items with assignees (if available)
            Format neatly in Markdown.
            """

            with st.spinner("⏳ Generating meeting minutes..."):
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={"model": "llama3", "prompt": prompt, "stream": False},
                )
                data = response.json()
                output = data.get("response", "⚠️ No response from model.")

            # Display results
            st.subheader("📌 AI-Generated Meeting Minutes")
            st.markdown(output)

            # Save for download
            st.session_state["meeting_minutes"] = output

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Download button if results exist
if "meeting_minutes" in st.session_state:
    st.download_button(
        "💾 Download Meeting Minutes",
        st.session_state["meeting_minutes"],
        file_name="meeting_minutes.md",
        mime="text/markdown"
    )
