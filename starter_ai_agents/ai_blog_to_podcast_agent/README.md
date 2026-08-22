## 📰 ➡️ 🎙️ Blog to Podcast Agent
This is a Streamlit-based application that allows users to convert any blog post into a podcast. The app uses OpenAI's GPT-4 model for summarization, Firecrawl for scraping blog content, and ElevenLabs API for generating audio. Users simply input a blog URL, and the app will generate a podcast episode based on the blog.

## Features

- **Blog Scraping**: Scrapes the full content of any public blog URL using Firecrawl API.

- **Summary Generation**: Creates an engaging and concise summary of the blog (within 2000 characters) using OpenAI GPT-4.

- **Podcast Generation**: Converts the summary into an audio podcast using the ElevenLabs voice API.

- **API Key Integration**: Requires OpenAI, Firecrawl, and ElevenLabs API keys to function, entered securely via the sidebar.

## Setup

### Requirements 

1. **API Keys**:
    - **OpenAI API Key**: Sign up at OpenAI to obtain your API key.

    - **ElevenLabs API Key**: Get your ElevenLabs API key from ElevenLabs.

    - **Firecrawl API Key**: Get your Firecrawl API key from Firecrawl.

2. **Python 3.12+**: Ensure you have Python 3.12 or higher installed.

3. **uv**: This project uses [uv](https://docs.astral.sh/uv/) for dependency management. Install it with:
   ```bash
   # macOS / Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

### Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps
   cd starter_ai_agents/ai_blog_to_podcast_agent
   ```

2. Install the dependencies (uv creates the virtual environment for you):
   ```bash
   uv sync
   ```
### Running the App

1. Start the Streamlit app:
   ```bash
   uv run streamlit run blog_to_podcast_agent.py
   ```

2. In the app interface:
    - Enter your OpenAI, ElevenLabs, and Firecrawl API keys in the sidebar.

    - Input the blog URL you want to convert.

    - Click "🎙️ Generate Podcast".

    - Listen to the generated podcast or download it.