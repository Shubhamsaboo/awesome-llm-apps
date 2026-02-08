# AI Content Factory for AgroDrone Europe

A multi-agent content generation system that creates SEO-optimized content for [agrodroneeurope.com](https://agrodroneeurope.com) — a professional agricultural drone services company in Germany.

## Features

- **Multi-agent pipeline**: Researcher → SEO Writer → Editor working together
- **28 RSS news feeds**: Auto-fetches news from German agriculture, drones, and EU regulation sources
- **AI Topic Planner**: Analyzes current news and suggests content topics
- **6 content types**: Blog posts, landing pages, service descriptions, social media packs, case studies, FAQ sections
- **SEO optimization**: Meta tags, heading structure, keyword integration, internal linking suggestions
- **Bilingual**: German and English content generation
- **Service-focused**: Tailored for crop protection, seeding, NDVI monitoring, and roof cleaning services
- **Two interfaces**: Streamlit UI for interactive use, FastAPI for n8n/automation

## How It Works

```
RSS Feeds (28 sources) → News Fetcher → AI Topic Planner → Researcher → SEO Writer → Editor → Content
```

**Agents:**

1. **Topic Planner** — analyzes RSS news digest and suggests timely content topics
2. **Researcher** — deep-dives into suggested topics using SerpAPI web search
3. **SEO Content Writer** — creates structured, keyword-optimized content
4. **Content Editor** — orchestrates the team, reviews quality, ensures brand consistency

**RSS Feed Categories:**

| Category | Sources | Examples |
|----------|---------|----------|
| Agriculture (DE) | 8 | Proplanta, LWK Niedersachsen |
| Drones (DE) | 6 | Drones Magazin, Droniq, Copting |
| Drone Regulation | 7 | LBA, EASA, dipul.de |
| EU Agriculture | 5 | AgroGo, Eurostat, EFSA |
| AgTech / Precision Ag | 2 | PrecisionAg, Successful Farming |

## Option 1: Streamlit UI

```bash
pip install -r requirements.txt
streamlit run content_factory.py
```

Enter your API keys in the sidebar and configure your content request.

## Option 2: FastAPI + n8n (Autonomous Pipeline)

### Start the API server

```bash
export OPENAI_API_KEY="sk-..."
export SERP_API_KEY="..."

uvicorn content_factory_api:app --host 0.0.0.0 --port 8000
```

Swagger UI: `http://localhost:8000/docs`

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/generate` | Generate content for a given topic |
| `POST` | `/news` | Fetch recent news from RSS feeds |
| `POST` | `/suggest-topics` | AI-powered topic suggestions based on current news |
| `GET` | `/content-types` | List available content types |
| `GET` | `/services` | List available service focus areas |
| `GET` | `/feeds` | List all configured RSS feeds |
| `GET` | `/feed-categories` | List feed category groups |
| `GET` | `/health` | Health check |

### Example: Full autonomous pipeline via curl

```bash
# Step 1: Fetch news
curl -X POST http://localhost:8000/news \
  -H "Content-Type: application/json" \
  -d '{"category": "crop_protection", "max_age_days": 7}'

# Step 2: Get AI topic suggestions
curl -X POST http://localhost:8000/suggest-topics \
  -H "Content-Type: application/json" \
  -d '{"category": "crop_protection", "num_suggestions": 3, "language": "german"}'

# Step 3: Generate content for a suggested topic
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Neue EU-Drohnenverordnung 2025: Was Landwirte wissen muessen",
    "content_type": "blog_post",
    "service_focus": "pflanzenschutz",
    "language": "german",
    "target_keywords": "EU Drohnenverordnung, Agrardrohne Pflanzenschutz"
  }'
```

### n8n Setup

1. Start the API server (see above)
2. In n8n, import `n8n_workflow_example.json`
3. The workflow runs the full autonomous pipeline:

```
Manual Trigger ─┐
                ├→ Fetch RSS News → Has News? → AI Suggest Topics → Split → Generate Content → Save File
Cron (Mon 9AM) ─┘                                                                            → Email Team
```

**Customize in n8n:**
- Change `category` in "Fetch RSS News" to filter by topic (crop_protection, drone_regulation, etc.)
- Change `num_suggestions` in "AI Suggest Topics" for more/fewer articles
- Add **WordPress**, **Google Drive**, **Slack**, or **Telegram** nodes after content generation

### Feed Categories for Filtering

| Key | Includes |
|-----|----------|
| `crop_protection` | Crop protection, general agriculture, fertilizer feeds |
| `seeding` | Agriculture, digital agriculture, precision ag feeds |
| `ndvi_monitoring` | Precision ag, digital ag, agritech, statistics feeds |
| `drone_regulation` | UAV regulation, aviation authority, aviation ops feeds |
| `drones_general` | Drone magazines, drone training, urban air mobility |
| `policy` | Agricultural policy, food safety feeds |
