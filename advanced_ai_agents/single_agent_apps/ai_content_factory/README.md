# AI Content Factory for AgroDrone Europe

A full-stack content production pipeline for [agrodroneeurope.com](https://agrodroneeurope.com) with **human-in-the-loop review**, **image generation**, **social media automation**, **voiceover**, and **vertical video assembly**.

## Pipeline Overview

```
RSS Feeds (28 sources)
    │
    ▼
┌─────────────────┐     ┌──────────────┐     ┌──────────────────────┐
│ 1. Fetch News   │────▶│ 2. HUMAN     │────▶│ 3. Generate Content  │
│    (auto-queue) │     │    REVIEW    │     │    + DALL-E Image    │
└─────────────────┘     │    (news)    │     └──────────────────────┘
                        └──────────────┘                │
                                                        ▼
                                              ┌──────────────────┐
                                              │ 4. HUMAN REVIEW  │
                                              │    (content)     │
                                              └────────┬─────────┘
                                                       │
                                          ┌────────────┴────────────┐
                                          ▼                         ▼
                                ┌──────────────────┐    ┌───────────────────────┐
                                │ 5. Publish to    │    │ 6. Social Media       │
                                │    Website       │    │    - Posts (4 platforms)│
                                └──────────────────┘    │    - Voiceover (TTS)  │
                                                        │    - Vertical Video   │
                                                        └───────────┬───────────┘
                                                                    ▼
                                                        ┌───────────────────────┐
                                                        │ 7. HUMAN REVIEW       │
                                                        │    (social media)     │
                                                        └───────────┬───────────┘
                                                                    ▼
                                                        ┌───────────────────────┐
                                                        │ 8. Post to Platforms  │
                                                        │    LinkedIn, Insta,   │
                                                        │    Facebook, TikTok   │
                                                        └───────────────────────┘
```

## Features

- **28 RSS feeds** — German agriculture, drones, EU regulation, LBA, EASA
- **3 review queues** — News, Content, Social Media (all human-verified)
- **AI agents** — Topic Planner, Researcher, SEO Writer, Content Editor, Social Media Manager
- **DALL-E 3 images** — Auto-generated website banners and social media verticals
- **OpenAI TTS voiceover** — 6 voice choices, for video narration
- **Vertical video** — ffmpeg assembly (image + voiceover → 9:16 MP4)
- **Social media pack** — LinkedIn, Instagram, Facebook, TikTok/Reels scripts
- **n8n integration** — Full workflow with form-based human review
- **SQLite persistence** — All queues survive restarts

## Files

```
ai_content_factory/
├── content_factory.py        # Streamlit UI (standalone)
├── content_factory_api.py    # FastAPI v2 (for n8n)
├── rss_feeds.py              # 28 RSS feed configurations
├── news_fetcher.py           # RSS fetcher + AI Topic Planner
├── review_queue.py           # SQLite review queues (news, content, social)
├── media_generator.py        # DALL-E images, TTS voiceover, ffmpeg video
├── n8n_workflow_example.json # Ready-to-import n8n workflow
├── requirements.txt
└── README.md
```

## Quick Start

```bash
pip install -r requirements.txt

export OPENAI_API_KEY="sk-..."
export SERP_API_KEY="..."

# Start API server
uvicorn content_factory_api:app --host 0.0.0.0 --port 8000
```

Swagger UI: `http://localhost:8000/docs`

## API Endpoints (v2)

### 1. News

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/news/fetch` | Fetch RSS news and auto-queue for review |
| `POST` | `/suggest-topics` | AI topic suggestions from current news |

### 2. Review Queue — News

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/queue/news` | List news awaiting review |
| `POST` | `/queue/news/{id}/review` | Approve or reject a news item |

### 3. Content Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/generate` | Generate content + image → add to review queue |

### 4. Review Queue — Content

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/queue/content` | List content awaiting review |
| `POST` | `/queue/content/{id}/review` | Approve or reject content |
| `POST` | `/queue/content/{id}/publish` | Mark content as published |

### 5. Media

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/media/image` | Generate DALL-E 3 image |
| `POST` | `/media/voiceover` | Generate OpenAI TTS audio |

### 6. Social Media

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/social/generate` | Generate social pack (posts + image + voiceover + video) |

### 7. Review Queue — Social Media

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/queue/social` | List social posts awaiting review |
| `POST` | `/queue/social/{id}/review` | Approve or reject social post |
| `POST` | `/queue/social/{id}/publish` | Mark as published |

### Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/content-types` | List content types |
| `GET` | `/services` | List service focus areas |
| `GET` | `/feeds` | List all 28 RSS feeds |
| `GET` | `/feed-categories` | Feed category groups |
| `GET` | `/health` | Health check |

## n8n Setup

1. Start the API server
2. Import `n8n_workflow_example.json` into n8n
3. The workflow includes:
   - **Cron trigger** (Mon/Wed/Fri 8AM)
   - **Form Trigger** for human review (approve/reject with notes)
   - **Content generation** with auto DALL-E image
   - **Social media branch** with voiceover generation
   - **Sticky notes** explaining each step and customization options

### Extending the n8n workflow

After the social media review step, connect platform-specific nodes:

| Platform | n8n Node | Content Fields |
|----------|----------|---------------|
| LinkedIn | LinkedIn node | `post_text` + `image_url` |
| Instagram | HTTP Request (Meta Graph API) | `post_text` + `image_url` |
| Facebook | Facebook node | `post_text` + `image_url` |
| TikTok/Reels | HTTP Request (TikTok API) | `video_url` |
| WordPress | WordPress node | `content_markdown` + `image_url` |

## Example: Full pipeline via curl

```bash
# Step 1: Fetch news → auto-queue
curl -X POST http://localhost:8000/news/fetch \
  -H "Content-Type: application/json" \
  -d '{"category": "crop_protection", "max_age_days": 7, "auto_queue": true}'

# Step 2: Review news (approve news_id=1)
curl -X POST http://localhost:8000/queue/news/1/review \
  -H "Content-Type: application/json" \
  -d '{"status": "approved", "reviewer_notes": "Relevant for Pflanzenschutz"}'

# Step 3: Generate content (with image)
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "Neue EU-Drohnenverordnung", "content_type": "blog_post", "service_focus": "pflanzenschutz", "language": "german", "news_id": 1, "generate_image": true}'

# Step 4: Review content (approve content_id=1)
curl -X POST http://localhost:8000/queue/content/1/review \
  -H "Content-Type: application/json" \
  -d '{"status": "approved"}'

# Step 5: Publish to website
curl -X POST http://localhost:8000/queue/content/1/publish

# Step 6: Generate social media pack
curl -X POST http://localhost:8000/social/generate \
  -H "Content-Type: application/json" \
  -d '{"content_id": 1, "generate_image": true, "generate_voiceover": true, "generate_video": false, "voice": "nova"}'

# Step 7: Review social media (approve sm_id=1)
curl -X POST http://localhost:8000/queue/social/1/review \
  -H "Content-Type: application/json" \
  -d '{"status": "approved"}'
```

## Video Generation

For vertical video assembly, install ffmpeg:

```bash
# Ubuntu/Debian
apt install ffmpeg

# macOS
brew install ffmpeg
```

Then set `generate_video: true` in the `/social/generate` request. The system creates a 9:16 MP4 from the DALL-E image + TTS voiceover.
