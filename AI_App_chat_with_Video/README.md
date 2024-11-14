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

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up FFmpeg**:

   - Install FFmpeg from [FFmpeg.org](https://ffmpeg.org/download.html).
   - Add FFmpeg to your system PATH so the application can call it directly.

4. **Configure YouTube URL Handling (Optional)**:
   - If you plan to enable YouTube URL transcription, add your API key and YouTube download logic in `app.py`.

### Running the Application

To start the Streamlit app, run:

```bash
streamlit run app.py
```

Then open your web browser to `http://localhost:8501` to access the app.

### Using the App

1. **Upload a Video**:
   - In the sidebar, upload a `.mp4`, `.mov`, or `.avi` file.
   - Alternatively, paste a YouTube URL (if enabled).
2. **Process Video**:

   - Click the "Process Video" button to start extracting audio and generating a transcript.
   - Wait for the transcript to be processed (may take a few moments).

3. **Ask Questions**:

   - Once the transcript is ready, type a question about the video in the input box and submit.
   - The app will respond with an answer and suggest follow-up questions.

4. **Explore Chat History**:
   - View all previous questions and answers in the "Chat History" section.
   - Click on any suggested questions to automatically ask follow-up questions based on the video content.

## Troubleshooting

### PermissionError on Temporary Files

If you encounter a `PermissionError` related to temporary files, ensure the code removes or closes files properly by updating `app.py` as needed. Use the `shutil.copy()` method to avoid file access conflicts.

### YouTube URL Handling

If you'd like to enable support for YouTube URLs, implement the YouTube download and transcription code in `app.py`.

## Future Enhancements

- **YouTube URL Support**: Enable transcription and Q&A for YouTube videos.
- **Improved NLP Models**: Experiment with other language models for potentially better answers and suggestions.
- **Enhanced UI**: Add options for customizing chat appearance and managing multiple transcripts.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---
