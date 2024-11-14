# Video Q&A Chatbot

This Streamlit application allows users to upload a video file or provide a YouTube URL, and then ask questions about the video's content in a chat-like interface. The app processes the video, extracts audio, transcribes it into text, and uses a language model to answer questions and suggest follow-up queries based on the video transcript.

## Features

- **Video Upload**: Users can upload a `.mp4`, `.mov`, or `.avi` file, or provide a YouTube URL.
- **Audio Extraction & Transcription**: Automatically extracts audio from the video and transcribes it into text.
- **Q&A Chat Interface**: Users can type questions related to the video content and receive answers. Suggested follow-up questions are also provided for deeper exploration.
- **Chat History**: Displays a history of all questions and answers in the session, with clickable suggestions for follow-up questions.

## Project Structure

- `app.py`: Main application file for Streamlit, which includes the user interface and app logic.
- `extract_text.py`: Contains the functions `extract_audio_from_video` and `transcribe_audio` to handle audio extraction and transcription.
- `process_text.py`: Processes the extracted text to clean and prepare it for the language model.
- `langchain_integration.py`: Contains the `generate_answer_and_suggested_questions` function that interfaces with the language model to answer questions and generate follow-up suggestions.

## Getting Started

### Prerequisites

- **Python 3.8+**
- **Streamlit**: For the web interface
- **FFmpeg**: For audio extraction from video files (make sure `ffmpeg` is installed and accessible in your PATH)
- **Other Python Libraries**: Install required libraries with the command below

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/video-qa-chatbot.git
   cd video-qa-chatbot
   ```
