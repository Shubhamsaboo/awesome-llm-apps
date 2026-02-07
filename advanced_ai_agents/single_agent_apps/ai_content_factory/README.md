# AI Content Factory for AgroDrone Europe

A multi-agent content generation system that creates SEO-optimized content for [agrodroneeurope.com](https://agrodroneeurope.com) — a professional agricultural drone services company in Germany.

## Features

- **Multi-agent pipeline**: Researcher → SEO Writer → Editor working together
- **6 content types**: Blog posts, landing pages, service descriptions, social media packs, case studies, FAQ sections
- **SEO optimization**: Meta tags, heading structure, keyword integration, internal linking suggestions
- **Bilingual**: German and English content generation
- **Service-focused**: Tailored for crop protection, seeding, NDVI monitoring, and roof cleaning services
- **Two interfaces**: Streamlit UI for interactive use, FastAPI for n8n/automation

## How It Works

The app uses three AI agents coordinated by Agno:

1. **Researcher** — searches the web for industry data, trends, and competitor insights using SerpAPI
2. **SEO Content Writer** — creates structured, keyword-optimized content using research findings
3. **Content Editor** — orchestrates the team, reviews quality, and ensures brand consistency

## Option 1: Streamlit UI

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
streamlit run content_factory.py
```

3. Enter your API keys in the sidebar and configure your content request.

## Option 2: FastAPI + n8n Integration

### Start the API server

```bash
# Set API keys as environment variables (or pass them in each request)
export OPENAI_API_KEY="sk-..."
export SERP_API_KEY="..."

# Start the server
uvicorn content_factory_api:app --host 0.0.0.0 --port 8000
```

The API docs are available at `http://localhost:8000/docs` (Swagger UI).

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/generate` | Generate content |
| `GET` | `/content-types` | List available content types |
| `GET` | `/services` | List available service focus areas |
| `GET` | `/health` | Health check |

### Example API Request

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Vorteile der Drohnen-Pflanzenschutz für deutsche Landwirte",
    "content_type": "blog_post",
    "service_focus": "pflanzenschutz",
    "language": "german",
    "target_keywords": "Drohne Pflanzenschutz, Agrardrohne"
  }'
```

### n8n Setup

1. Start the API server (see above)
2. In n8n, import the workflow from `n8n_workflow_example.json`
3. Configure the **Set Content Parameters** node with your topics
4. The workflow supports:
   - **Manual trigger** — run on demand
   - **Cron schedule** — auto-generate content weekly (Mon 9AM by default)
   - **Email notification** — sends the generated content to your team
   - **File export** — saves content as Markdown files

### n8n Workflow Structure

```
Manual Trigger ─┐
                ├→ Set Content Parameters → HTTP Request (API) → If Success → Save File
Cron Schedule ──┘                                                           → Send Email
```

You can extend the workflow with additional n8n nodes:
- **WordPress node** — auto-publish blog posts
- **Google Sheets** — log generated content to a spreadsheet
- **Slack/Telegram** — notify your team on new content
- **Google Drive** — store content files in the cloud
