import streamlit as st
from extract_text import extract_audio_from_video, transcribe_audio
from process_text import process_extracted_text
from langchain_integration import generate_answer_and_suggested_questions
import tempfile
import os
import shutil


# Initialize Streamlit app
def main():
    # Sidebar for video upload options
    st.sidebar.title("Upload Options")
    st.sidebar.write("Choose a video file to upload, or paste a YouTube URL.")

    # File uploader in the sidebar
    uploaded_file = st.sidebar.file_uploader(
        "Choose a video file", type=["mp4", "mov", "avi"]
    )
    youtube_url = st.sidebar.text_input("Or paste a YouTube URL")

    # Title and description
    st.title("Video Q&A Chatbot")
    st.write(
        "Upload a video file or YouTube link, then ask questions about its content in a chat interface!"
    )

    # Session State for storing chat history and processed text
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "processed_text" not in st.session_state:
        st.session_state["processed_text"] = None

    # Step 1: Process video file or YouTube URL on button click
    if (uploaded_file or youtube_url) and st.sidebar.button("Process Video"):
        if uploaded_file:
            # Save the uploaded video to a temporary file
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".mp4"
            ) as temp_video_file:
                temp_video_file.write(uploaded_file.read())
                temp_video_path = temp_video_file.name

            # Copy to a new location to avoid PermissionError
            temp_copy_path = temp_video_path + "_copy.mp4"
            shutil.copy(temp_video_path, temp_copy_path)
            os.remove(temp_video_path)  # Remove original temp file

            # Process the copied video
            try:
                st.write(
                    "Processing video and generating transcript... this may take a moment."
                )
                audio_path = extract_audio_from_video(temp_copy_path)
                extracted_text = transcribe_audio(audio_path)
                st.session_state["processed_text"] = process_extracted_text(
                    extracted_text
                )
                st.write("Transcript ready! Now you can ask questions.")

            finally:
                # Clean up temporary files
                os.remove(temp_copy_path)
                if os.path.exists(audio_path):
                    os.remove(audio_path)

        elif youtube_url:
            st.write("Processing YouTube video...")
            # Here, you would add code to download and transcribe the YouTube video
            # Placeholder for actual YouTube download and transcription logic
            st.write("YouTube processing not implemented yet.")
            st.session_state["processed_text"] = "Sample transcript from YouTube video."

    # Step 4: Q&A interaction - only enabled after processing text
    if st.session_state["processed_text"]:
        question = st.text_input("Ask a question about the video content:")

        if question:
            # Retrieve answer and suggested questions
            qa_response = generate_answer_and_suggested_questions(
                st.session_state["processed_text"], question
            )
            answer = qa_response["answer"]
            suggested_questions = qa_response["suggested_questions"]

            # Append the new question and answer to the chat history
            st.session_state["chat_history"].append(
                {
                    "question": question,
                    "answer": answer,
                    "suggestions": suggested_questions,
                }
            )

        # Display chat history
        st.subheader("Chat History")
        for i, chat in enumerate(st.session_state["chat_history"]):
            st.markdown(f"**Question {i+1}:** {chat['question']}")
            st.markdown(f"*Answer:* {chat['answer']}")

            # Show follow-up questions
            if "suggestions" in chat:
                st.markdown("**Suggested Questions:**")
                for suggestion in chat["suggestions"]:
                    if st.button(suggestion, key=f"{i}-{suggestion}"):
                        # Automatically ask the follow-up question if clicked
                        follow_up_qa_response = generate_answer_and_suggested_questions(
                            st.session_state["processed_text"], suggestion
                        )
                        follow_up_answer = follow_up_qa_response["answer"]
                        follow_up_suggestions = follow_up_qa_response[
                            "suggested_questions"
                        ]

                        # Append follow-up question and answer
                        st.session_state["chat_history"].append(
                            {
                                "question": suggestion,
                                "answer": follow_up_answer,
                                "suggestions": follow_up_suggestions,
                            }
                        )


if __name__ == "__main__":
    main()
