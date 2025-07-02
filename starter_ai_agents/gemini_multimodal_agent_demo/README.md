# 🎨 Gemini Multimodal Agent Demo

A powerful demonstration of Google's Gemini 2.0 Flash multimodal capabilities, processing images, audio, and video inputs simultaneously to generate unified insights.

## 🌟 Features

- **Multimodal Processing**: Analyze images, audio, and video in a single query
- **Web Search Integration**: Augment analysis with real-time web information using DuckDuckGo
- **Unified Insights**: Generate comprehensive responses that connect all input modalities
- **Streaming Response**: Real-time output generation for better user experience

## 📋 Prerequisites

- Python 3.8+
- Google AI API Key (for Gemini access)
- Sample media files (image, audio, video) for testing

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/starter_ai_agents/gemini_multimodal_agent_demo
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Create a `.env` file or export your Google AI API key:
```bash
export GOOGLE_API_KEY='your-google-ai-api-key'
```

### 4. Prepare Your Media Files

Place your test files in the project directory:
- An image file (or use a URL)
- An audio file (e.g., `sample_audio.mp3`)
- A video file (e.g., `sample_video.mp4`)

### 5. Run the Agent
```bash
python multimodal_ai_agent.py
```

## 🔧 Configuration

Update the file paths in the script:
```python
# Image Input - can be URL or local file
image_url = "https://example.com/sample_image.jpg"

# Audio Input - local file
audio_file = "sample_audio.mp3"

# Video Input - local file
video_file = upload_file("sample_video.mp4")
```

## 📖 How It Works

1. **Initialize Agent**: Creates a Gemini-powered agent with web search capabilities
2. **Upload Media**: Processes image URLs, audio files, and uploads video files
3. **Video Processing**: Waits for video upload to complete before analysis
4. **Multimodal Query**: Sends all inputs with a comprehensive analysis prompt
5. **Unified Response**: Generates insights connecting all media elements with web context

## 💡 Usage Examples

The agent can be used for:
- **Content Analysis**: Understanding relationships between different media elements
- **Story Extraction**: Finding narratives that connect visual and audio content
- **Research Augmentation**: Combining media analysis with current web information
- **Educational Content**: Creating comprehensive summaries from multimedia materials

## 🎯 Example Query Structure

The default query asks the agent to:
1. Describe the visual scene and its significance
2. Extract key messages from audio that relate to visuals
3. Analyze video for insights connecting to other inputs
4. Search web for latest updates on related topics
5. Summarize the overall theme or story

## 🤝 Contributing

Feel free to enhance this demo with:
- Additional media processing capabilities
- Custom analysis prompts
- Output formatting options
- Integration with other AI models

## 📄 License

This project is part of the Awesome LLM Apps repository.

## 🔗 Related Projects

- [AI Data Analysis Agent](../ai_data_analysis_agent)
- [AI Music Generator Agent](../ai_music_generator_agent)
- [AI Medical Imaging Agent](../ai_medical_imaging_agent)