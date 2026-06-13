import base64
import json
import os
from datetime import date, timedelta
from io import BytesIO
from typing import Any

os.environ["AGNO_TELEMETRY"] = "false"

import requests
import streamlit as st
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.run.agent import (
    RunCompletedEvent,
    ToolCallCompletedEvent,
    ToolCallStartedEvent,
)
from agno.tools import tool
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel

st.set_page_config(page_title="AI Content Creator Agent", layout="wide")

with st.sidebar:
    st.header("Settings")
    openai_key = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="sk-...",
        help="Your OpenAI API key is used to generate content.",
    )
    news_key = st.text_input(
        "NewsAPI API Key",
        type="password",
        placeholder="Enter NewsAPI key...",
        help="Your NewsAPI API key is used to fetch news.",
    )

st.title("AI Content Creator Agent")

topic = st.text_area(
    "Message",
    placeholder="What would you like to generate content for?",
    height=120,
    label_visibility="collapsed",
)

generate = st.button("Generate", type="primary", use_container_width=True)

HEADLINE_INSTRUCTIONS = (
    "You are a headline writer for a top-tier digital news publication. "
    "Your job is to distill news stories into a single punchy, attention-grabbing sentence. "
    "Rules you must follow:\n"
    "- Maximum 15 words\n"
    "- Lead with the most surprising or impactful detail\n"
    "- Use active voice and strong verbs\n"
    "- No filler phrases like 'In a shocking turn' or 'Experts say'\n"
    "- Output the headline only — no punctuation at the end, no quotes, no extra text"
)

CAPTION_INSTRUCTIONS = (
    "You are a social media editor at a major news publication. "
    "You write Instagram/LinkedIn captions that inform, provoke thought, and drive engagement. "
    "Your captions follow this exact structure:\n"
    "1. Hook (1 sentence) — an arresting fact or question that stops the scroll\n"
    "2. Context (2-3 sentences) — the key details a reader needs to understand why this matters\n"
    "3. Implication (1 sentence) — what this means for the reader or society going forward\n"
    "4. Call to reflection (1 sentence) — an open question or provocative statement to spark comments\n"
    "5. Source line — 'Source: [publication name]'\n"
    "6. Hashtags — 3 to 5 specific, relevant hashtags on the final line\n\n"
    "Style rules:\n"
    "- Active voice, short sentences, no jargon\n"
    "- Never start with 'In a world' or similar clichés\n"
    "- No emojis unless they add meaning\n"
    "- Output the caption only — no preamble, no commentary"
)

RESEARCHER_INSTRUCTIONS = (
    "You are a news researcher. Given a user topic:\n"
    "1. Derive a tight 1-2 word search keyword.\n"
    "2. Call the search_news tool with that keyword.\n"
    "3. If no articles are returned, try one broader keyword and search again.\n"
    "4. Pick the single best article and return structured output with its 0-based index.\n\n"
    "Rank articles using these criteria (in order):\n"
    "1. Relevance — how closely it matches the user's query\n"
    "2. Newsworthiness — breaking news and major developments over opinion or minor updates\n"
    "3. Recency — prefer more recent articles when relevance is equal\n"
    "4. Source credibility — prefer established outlets over blogs or aggregators"
)


class SelectedArticle(BaseModel):
    index: int
    keyword: str
    reason: str


def fetch_headlines(api_key: str, query: str) -> list[dict]:
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    resp = requests.get(
        "https://newsapi.org/v2/everything",
        params={
            "q": query,
            "from": yesterday,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 5,
            "apiKey": api_key,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("articles", [])


def news_text_only(article: dict) -> str:
    text = (
        f"Title:{article['title']}  \n\n Description:{article.get('description', '')} "
        f"\n\n Source Name: {article.get('source', {}).get('name', '')} "
        f"\n Source URL: {article.get('url', '')}"
    )
    return text.strip()


def generate_image(client: OpenAI, summary: str) -> bytes:
    image_prompt = (
        f"Scene depicting: {summary}. "
        "Medium: documentary photojournalism. "
        "Shot on a 35mm lens, natural ambient light, shallow depth of field, high resolution. "
        "Composition: rule of thirds, candid moment, no staged or stock-photo feel. "
        "Mood: grounded, authentic, and newsworthy. "
        "Exclude: text overlays, headlines, watermarks, logos, newspaper imagery, illustrations, CGI, or cartoon elements."
    )
    resp = client.images.generate(
        model="gpt-image-1-mini",
        prompt=image_prompt,
        size="1024x1024",
    )
    b64 = resp.data[0].b64_json
    return base64.b64decode(b64)


def add_text_overlay(img_bytes: bytes, text: str) -> bytes:
    img = Image.open(BytesIO(img_bytes)).convert("RGBA")
    w, h = img.size

    text = text.upper()

    max_strip_h = int(h * 0.4)
    margin = int(w * 0.05)
    max_width = w - 2 * margin
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))

    font_size = max(42, w // 12)
    font = None
    lines: list[str] = []

    while font_size >= 12:
        _font = None
        for font_name in ["impact.ttf", "ariblk.ttf", "arialbd.ttf", "arial.ttf"]:
            try:
                _font = ImageFont.truetype(font_name, size=font_size)
                break
            except OSError:
                continue
        if _font is None:
            _font = ImageFont.load_default()

        words = text.split()
        _lines: list[str] = []
        current_line = ""
        for word in words:
            test = f"{current_line} {word}".strip() if current_line else word
            bbox = probe.textbbox((0, 0), test, font=_font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test
            else:
                if current_line:
                    _lines.append(current_line)
                current_line = word
        if current_line:
            _lines.append(current_line)

        _padding = int(margin * 1.2)
        if int(font_size * 1.25) * len(_lines) + _padding * 2 <= max_strip_h:
            font, lines = _font, _lines
            break
        font_size -= 2

    if font is None:
        font, lines = _font, _lines

    line_h = int(font_size * 1.25)
    padding = int(margin * 1.2)
    strip_h = line_h * len(lines) + padding * 2

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for i in range(strip_h):
        alpha = int(150 + (i / strip_h) * 95)
        draw.line([(0, h - strip_h + i), (w, h - strip_h + i)], fill=(0, 0, 0, alpha))

    total_text_h = line_h * len(lines)
    y_start = h - strip_h + (strip_h - total_text_h) // 2

    stroke_r = max(2, font_size // 18)
    stroke_offsets = [
        (dx, dy)
        for dx in range(-stroke_r, stroke_r + 1)
        for dy in range(-stroke_r, stroke_r + 1)
        if dx != 0 or dy != 0
    ]

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (w - text_w) // 2
        y = y_start + i * line_h

        for dx, dy in stroke_offsets:
            draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 255))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))

    combined = Image.alpha_composite(img, overlay).convert("RGB")
    out = BytesIO()
    combined.save(out, format="PNG")
    return out.getvalue()


def make_search_news_tool(news_key: str, articles_store: list[dict]):
    @tool(
        name="search_news",
        description="Search recent English news headlines for a 1-2 word keyword from the last 24 hours.",
    )
    def search_news(query: str) -> str:
        articles = fetch_headlines(news_key, query)
        articles_store.clear()
        articles_store.extend(articles)
        if not articles:
            return "No articles found for that query."
        return "\n".join(
            f"{i}. {a['title']}: {a.get('description', '')}"
            for i, a in enumerate(articles)
            if a.get("title")
        )

    return search_news


def parse_selected_article(content: Any) -> SelectedArticle:
    if isinstance(content, SelectedArticle):
        return content
    if isinstance(content, BaseModel):
        return SelectedArticle(**content.model_dump())
    if isinstance(content, dict):
        if "index" in content and "keyword" in content:
            return SelectedArticle(**content)
        if "content" in content:
            return parse_selected_article(content["content"])
    if isinstance(content, str):
        return SelectedArticle.model_validate_json(content)
    raise ValueError(f"Could not parse research output: {type(content)}")


def build_agents(openai_key: str, news_key: str, articles_store: list[dict]) -> tuple[Agent, Agent, Agent]:
    model = OpenAIChat(id="gpt-5-mini", api_key=openai_key)
    search_news = make_search_news_tool(news_key, articles_store)

    researcher = Agent(
        name="Researcher",
        model=model,
        tools=[search_news],
        output_schema=SelectedArticle,
        instructions=RESEARCHER_INSTRUCTIONS,
    )
    headline_writer = Agent(
        name="Headline Writer",
        model=model,
        instructions=HEADLINE_INSTRUCTIONS,
    )
    caption_writer = Agent(
        name="Caption Writer",
        model=model,
        instructions=CAPTION_INSTRUCTIONS,
    )
    return researcher, headline_writer, caption_writer


def run_agent_streamed(agent: Agent, prompt: str, status_label: str) -> Any:
    st.write(f"{status_label}…")
    result = None
    for event in agent.run(prompt, stream=True, stream_events=True):
        if isinstance(event, ToolCallStartedEvent):
            tool_name = event.tool.tool_name if event.tool else "tool"
            st.write(f"Calling `{tool_name}`…")
        elif isinstance(event, ToolCallCompletedEvent):
            tool_name = event.tool.tool_name if event.tool else "tool"
            st.write(f"`{tool_name}` finished.")
        elif isinstance(event, RunCompletedEvent):
            result = event.content
    if result is None:
        response = agent.run(prompt)
        result = response.content
    return result


def agent_text(content: Any) -> str:
    if isinstance(content, BaseModel):
        return str(content)
    return str(content).strip()


# --- Output placeholders ---
st.subheader("News Summary")
summary_placeholder = st.empty()
summary_placeholder.info("Summary will appear here after you click Generate.")

col_image, col_text = st.columns(2)

with col_image:
    st.subheader("Image")
    image_placeholder = st.empty()
    image_placeholder.info("Generated image will appear here.")
    image_dl_placeholder = st.empty()

with col_text:
    st.subheader("Caption")
    caption_placeholder = st.empty()
    caption_placeholder.info("Generated caption will appear here.")

# --- Generation pipeline (only runs when the button is clicked) ---
if generate:
    if not openai_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
        st.stop()
    if not news_key:
        st.error("Please enter your NewsAPI key in the sidebar.")
        st.stop()
    if not topic.strip():
        st.error("Please enter a query to generate content for.")
        st.stop()

    client = OpenAI(api_key=openai_key)
    articles_store: list[dict] = []
    researcher, headline_writer, caption_writer = build_agents(openai_key, news_key, articles_store)

    with st.sidebar:
        pipeline_status = st.status("Running pipeline…", expanded=True)

    with pipeline_status:
        try:
            st.write("Researching news…")
            research_output = run_agent_streamed(researcher, topic.strip(), "Researcher running")
            selection = parse_selected_article(research_output)

            if not articles_store:
                pipeline_status.update(label="Pipeline failed", state="error")
                st.error("No articles found for that topic today. Try a broader keyword.")
                st.stop()

            st.write(f"Keyword: **{selection.keyword}**")
            st.write(f"Found **{len(articles_store)}** article(s).")

            idx = min(max(selection.index, 0), len(articles_store) - 1)
            article = articles_store[idx]
            news_text = news_text_only(article)
            st.write(f"Selected: *{article.get('title', 'article')}*")
            summary_placeholder.success(news_text)

            headline = agent_text(
                run_agent_streamed(
                    headline_writer,
                    f"Write a headline for this news story:\n\n{news_text}",
                    "Writing headline",
                )
            )
            st.write("Headline ready.")

            st.write("Generating image with gpt-image-1-mini…")
            try:
                img_bytes = generate_image(client, headline)
                image_with_text = add_text_overlay(img_bytes, headline)
            except Exception as exc:
                pipeline_status.update(label="Pipeline failed", state="error")
                st.error(f"Image generation error: {exc}")
                st.stop()
            st.write("Image ready.")

            with col_image:
                image_placeholder.image(image_with_text, use_container_width=True)
                image_dl_placeholder.download_button(
                    label="Download Image",
                    data=image_with_text,
                    file_name="news_image.png",
                    mime="image/png",
                    use_container_width=True,
                )

            caption = agent_text(
                run_agent_streamed(
                    caption_writer,
                    f"Write a caption for this news story:\n\n{news_text}",
                    "Writing caption",
                )
            )
            st.write("Caption ready.")

            pipeline_status.update(label="Pipeline complete", state="complete", expanded=False)

        except (ValueError, json.JSONDecodeError) as exc:
            pipeline_status.update(label="Pipeline failed", state="error")
            st.error(f"Research error: {exc}")
            st.stop()
        except Exception as exc:
            pipeline_status.update(label="Pipeline failed", state="error")
            st.error(f"Pipeline error: {exc}")
            st.stop()

    with col_text:
        caption_placeholder.code(caption, language=None, wrap_lines=True)
