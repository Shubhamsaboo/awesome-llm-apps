# AI Content Creator Agent

A Streamlit application that turns a one-line topic into a finished social media post. You get a real news story from the last 24 hours, a photorealistic image with the headline built into it, and a caption ready to paste into Instagram or LinkedIn. You never open a design tool or write a word of copy.

Type something like "Fed rate decision" and click Generate. About a minute later you have a 1024×1024 image and a finished caption, both built from actual reporting instead of made-up filler. The whole thing runs in your browser and shows each step as it happens.

Under the hood it's five GPT calls and one image model wired into a single pipeline: pull the day's headlines from NewsAPI, rank them by newsworthiness, write a short headline, generate a documentary-style image, composite the headline onto the picture, then draft a caption with a source line and hashtags.

## What it does

1. You type a topic ("Fed rate decision" or "SpaceX launch").
2. GPT extracts a tight 1-2 word search query from it.
3. NewsAPI returns up to 5 recent articles; GPT ranks them by relevance, newsworthiness, recency, and source credibility.
4. The best article is summarised into a ≤15-word punchy headline.
5. `gpt-image-1-mini` generates a 1024×1024 documentary-style image from that headline.
6. The headline is composited onto the image as a bottom-strip text overlay (Impact font if available, fallback to system default).
7. A full caption is written with a hook, context, implication, call to reflection, source line, and 3-5 hashtags.

You can download the finished image straight from the browser.

## Installation

- Python 3.13+
- An [OpenAI API key](https://platform.openai.com/api-keys) with access to `gpt-5-mini` and `gpt-image-1-mini`
- A [NewsAPI key](https://newsapi.org/) (free tier works)

1. Clone this repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps
   cd starter_ai_agents/ai_content_creator_agent
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Once the above setup is complete, stay in the directory and run the following command:

```bash
streamlit run news_to_content.py
```

This will open the streamlit application at http://localhost:8501 .
1. Open the sidebar and paste your OpenAI and NewsAPI keys.
2. Type a topic in the main text area.
3. Click **Generate**.

A status panel in the sidebar shows each pipeline step as it runs. When complete, the image appears on the left and the copyable caption on the right.
