# Content Creator AI Agent

## Introduction

**Content Creator AI Agent** is an AI-powered content creation tool that turns your ideas into ready-to-post social media content. Describe a concept—like a motivational topic, a quote, or a theme—and the app automatically generates either a **multi-clip vertical video (reel)** with stock footage and voiceover, or a **square image with text** over a stock photo. Built with Streamlit, LangChain, and the Pexels API, it’s designed for creators who want to produce basic text + visual media content without manual editing.

---

## Key Features

- **AI-driven content creation** — Uses an LLM agent (GPT-4o-mini) to interpret your prompt and choose the right output format (image or video)
- **Vertical video reels** — Creates 1080×1920 reels from Pexels stock videos, with TTS voiceover, captions, and optional background music
- **Quote images** — Generates 1080×1080 square images with text overlay on Pexels photos
- **Streamlit web UI** — Simple interface to enter prompts, manage API keys, preview outputs, and download results
- **Pexels integration** — Uses Pexels for free stock photos and videos
- **Text-to-speech** — Local TTS (pyttsx3) for voiceover narration
- **One-click cleanup** — Clear temporary data after generation

---

## How It Works

1. **You describe your idea** — Enter a prompt in the Streamlit UI (e.g., *"A motivational reel about staying consistent at the gym"* or *"A quote image about focus and discipline"*).

2. **The LLM agent interprets it** — A LangChain agent powered by GPT-4o-mini reads your prompt and decides which output format fits best:
   - **Quote image** — For single visuals like quotes, posters, or thumbnails
   - **Video reel** — For short vertical videos with multiple clips (3–7 segments)

3. **Low Cost Content generation using Pexels API** — Depending on the choice:
   - **Image**: The agent extracts a caption and search term, fetches a photo from Pexels, overlays the text, and saves a 1080×1080 square image.
   - **Reel**: The agent produces a script with narration lines and Pexels search terms. For each segment, the app downloads stock video, generates TTS voiceover (pyttsx3), adds captions, and optionally mixes in background music. Clips are concatenated into a 1080×1920 vertical reel.

4. **Preview and download** — The generated image or video appears in the app. You can preview it and download it to your device. Temporary files (clips and voiceovers) in the temp_data directory can be cleared with one click.

---

## Setup

### Prerequisites

- **Python 3.10+**
- **Pexels API key** — Get one at [pexels.com/api](https://www.pexels.com/api/)
- **OpenAI API key** — For the LLM agent

### Installation

1. **Clone the GitHub repository**
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/single_agent_apps/ai_content_creator_agent
```

2. **Create a Python virtual environment:**

   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**

   - **Windows (PowerShell):**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt):**
     ```cmd
     venv\Scripts\activate.bat
     ```
   - **macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

5. **Optional:** Add a `background_music.mp3` file in the project root if you want background music in your reels. The app works without it.

### Running the Application

1. With the virtual environment activated, run:

   ```bash
   streamlit run streamlit_app.py
   ```

2. Open the URL shown in the terminal (usually `http://localhost:8501`).

3. In the sidebar, enter your **Pexels API Key** and **OpenAI API Key**.

4. In the main area, describe the content you want (e.g., *"A motivational reel about staying consistent at the gym"* or *"A quote image about focus and discipline"*).

5. Click **Generate Content** and wait for the AI to create your image or reel.

6. Preview and download your content from the app or go to the outputs folder created in the project directory.

**Note:** The script creates `output/` and `temp_data/` in the **current working directory** (cwd), not in the script’s directory. Generated files (`generated_image.jpg`, `generated_reel.mp4`) are saved in `output/`. Run from the project directory only so files and folders appear in the project folder; running from elsewhere creates and updates these folders in that location.

---

## Key Concepts Learned

- **Streamlit** — A simple way to build data and AI apps with minimal code; widgets like `st.text_area` and `st.button` handle user input.
- **LangChain agents** — Agents combine an LLM with tools (e.g., `create_reel`, `create_image`) so the model can decide which tool to call and with what parameters.
- **Pexels API** — Free stock media APIs often require an API key and return JSON with URLs to images/videos.
- **MoviePy** — Python library for video editing; useful for trimming clips, adding audio, and compositing text.
- **TTS (pyttsx3)** — Offline free text-to-speech; good for voiceovers when you don’t want to use cloud services.

---

## Project Structure

```
ai_content_creator_agent/
├── streamlit_app.py    # Web UI and main entry point
├── agent_tools.py      # LangChain agent and tools (create_reel, create_image)
├── helper_functions.py # Pexels API, video/image creation, TTS
├── requirements.txt    # Python dependencies
├── output/             # (Created when generated image or reel needs to be saved) Generated reels and images are stored and fetched from this directory
├── temp_data/          # (Created when clips and voiceovers are created) Temporary clips and voiceover are stored in this directory
└── README.md
```

---

### Pexels Media Disclaimer

Images and videos used to create content in this app are obtained from [Pexels](https://www.pexels.com/). For full terms, attribution guidelines, and usage restrictions, see the [Pexels License](https://www.pexels.com/license/).

### Image and Video Creation Disclaimer

This tutorial is provided as-is. The contributor(s) disclaim any responsibility for images or videos produced by this app. Users assume full responsibility for ensuring their use of any output complies with applicable laws and third-party terms. See the main repository for license details.