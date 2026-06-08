import base64
from datetime import date, timedelta
from io import BytesIO

import requests
import streamlit as st
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

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


def extract_query(client: OpenAI, topic: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {
                "role": "user",
                "content": (
                    f"Extract the most important 1-2 word search keyword from this sentence for a news search query. "
                    f"Reply with ONLY the keyword(s), nothing else:\n{topic}"
                ),
            }
        ],
    )
    return resp.choices[0].message.content.strip()


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


def select_best_article(client: OpenAI, articles: list[dict], query: str) -> dict:
    numbered = "\n".join(
        f"{i}. {a['title']}: {a.get('description', '')}"
        for i, a in enumerate(articles)
        if a.get("title")
    )
    resp = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {
                "role": "user",
                "content": (
                    f"Given the user's query: \"{query}\"\n\n"
                    "Pick the single best article from this list and reply with ONLY its number (0-indexed).\n\n"
                    "Use the following criteria to rank articles (in order of priority):\n"
                    "1. Relevance — how closely it matches the user's query\n"
                    "2. Newsworthiness — breaking news, major developments, or high societal impact rank higher than opinion pieces or minor updates\n"
                    "3. Recency — more recent articles are preferred when relevance is equal\n"
                    "4. Source credibility — prefer established outlets over blogs or aggregators\n\n"
                    f"Articles:\n{numbered}"
                ),
            }
        ],
    )
    try:
        idx = int(resp.choices[0].message.content.strip())
    except ValueError:
        idx = 0
    return articles[min(idx, len(articles) - 1)]

def news_text_only(article: dict) -> str:
    text = f"Title:{article['title']}  \n\n Description:{article.get('description', '')} \n\n Source Name: {article.get('source', {}).get('name', '')} \n Source URL: {article.get('url', '')}"
    
    return text.strip()

def summarize(client: OpenAI, article: dict) -> str:
    text = news_text_only(article)
    resp = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a headline writer for a top-tier digital news publication. "
                    "Your job is to distill news stories into a single punchy, attention-grabbing sentence. "
                    "Rules you must follow:\n"
                    "- Maximum 15 words\n"
                    "- Lead with the most surprising or impactful detail\n"
                    "- Use active voice and strong verbs\n"
                    "- No filler phrases like 'In a shocking turn' or 'Experts say'\n"
                    "- Output the headline only — no punctuation at the end, no quotes, no extra text"
                ),
            },
            {
                "role": "user",
                "content": f"Write a headline for this news story:\n\n{text}",
            },
        ],
    )
    return resp.choices[0].message.content.strip()

def generate_image(client: OpenAI, summary: str) -> bytes:
    # Image prompt structure follows best practices for photorealistic generation:
    # 1. Subject — what the scene depicts (derived from the news summary)
    # 2. Style & medium — anchors the visual register before adding modifiers
    # 3. Technical specs — lens, lighting, and composition details that push realism
    # 4. Atmosphere — mood cues that reinforce the tone of the story
    # 5. Negative constraints — explicit exclusions to prevent common failure modes
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


def generate_caption(client: OpenAI, news_text: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {
                "role": "system",
                "content": (
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
                ),
            },
            {
                "role": "user",
                "content": f"Write a caption for this news story:\n\n{news_text}",
            },
        ],
    )
    return resp.choices[0].message.content.strip()


# --- Output placeholders ---
# These are declared before generation so the layout stays stable;
# each placeholder is swapped out with real content once generation runs.
st.subheader("News Summary")
summary_placeholder = st.empty()
summary_placeholder.info("Summary will appear here after you click Generate.")

col_image, col_text = st.columns(2)

with col_image:
    st.subheader("Image")
    image_placeholder = st.empty()
    image_placeholder.info("Generated image will appear here.")
    image_dl_placeholder = st.empty()  # reserved for the download button

with col_text:
    st.subheader("Caption")
    caption_placeholder = st.empty()
    caption_placeholder.info("Generated caption will appear here.")

# --- Generation pipeline (only runs when the button is clicked) ---
if generate:
    # Validate required inputs before making any API calls
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

    with st.sidebar:
        pipeline_status = st.status("Running pipeline…", expanded=True)

    with pipeline_status:
        # Step 1: Turn the user's natural-language topic into a tight search query
        st.write("Extracting search query…")
        query = extract_query(client, topic.strip())
        st.write(f"Query: **{query}**")

        # Step 2: Pull recent headlines matching that query from NewsAPI
        st.write(f"Fetching news for *{query}*…")
        try:
            articles = fetch_headlines(news_key, query)
        except Exception as e:
            pipeline_status.update(label="Pipeline failed", state="error")
            st.error(f"NewsAPI error: {e}")
            st.stop()

        if not articles:
            pipeline_status.update(label="Pipeline failed", state="error")
            st.error("No articles found for that topic today. Try a broader keyword.")
            st.stop()

        st.write(f"Found **{len(articles)}** article(s).")

        # Step 3: Pick the single most relevant article using LLM ranking
        st.write("Selecting most relevant article…")
        best = select_best_article(client, articles, topic.strip())
        st.write(f"Selected: *{best.get('title', 'article')}*")

        # Show the raw article text immediately so the user has something to read
        # while the heavier image/caption generation continues below
        summary_placeholder.success(f"{news_text_only(best)}")

        # Step 4: Condense the article into a short summary used by both image and caption
        st.write("Generating summary…")
        summary = summarize(client, best)
        st.write("Summary ready.")

        # Step 5: Generate an image from the summary via gpt-image-1-mini
        st.write("Generating image with gpt-image-1-mini…")
        try:
            img_bytes = generate_image(client, summary)
        except Exception as e:
            pipeline_status.update(label="Pipeline failed", state="error")
            st.error(f"Image generation error: {e}")
            st.stop()

        img_with_text = add_text_overlay(img_bytes, summary)
        st.write("Image ready.")

        with col_image:
            image_placeholder.image(img_with_text, use_container_width=True)
            image_dl_placeholder.download_button(
                label="Download Image",
                data=img_with_text,
                file_name="news_image.png",
                mime="image/png",
                use_container_width=True,
            )

        # Step 6: Write a social-media-ready caption from the news
        st.write("Writing caption…")
        caption = generate_caption(client, news_text_only(best))
        st.write("Caption ready.")

        pipeline_status.update(label="Pipeline complete", state="complete", expanded=False)

    with col_text:
        caption_placeholder.code(caption, language=None, wrap_lines=True)
