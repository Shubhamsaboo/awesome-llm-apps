# Bilibili RAG

Bilibili RAG turns videos from a Bilibili favorites folder into a searchable, source-grounded personal knowledge base. It signs in to Bilibili with a QR code, syncs videos, transcribes audio with DashScope ASR, stores chunks in ChromaDB, and answers questions with retrieved source snippets.

![Home screen](assets/screenshots/home.png)
![Chat screen](assets/screenshots/chat.png)

## Features

- QR-code Bilibili login and favorites folder sync
- Multi-part video ingestion with per-part transcription
- Audio transcription through DashScope ASR with ffmpeg fallback handling
- Local SQLite metadata storage and ChromaDB vector storage
- RAG chat over indexed video transcripts with source snippets
- Markdown export for raw transcripts and AI-organized notes
- FastAPI backend and Next.js frontend
- Docker Compose setup for a local full-stack run

## Tech Stack

- Backend: FastAPI, SQLAlchemy, LangChain
- Frontend: Next.js, TypeScript, Tailwind CSS
- Vector database: ChromaDB
- Database: SQLite
- Models: DashScope ASR, DashScope embeddings, OpenAI-compatible chat models

## Prerequisites

- Python 3.10+
- Node.js 18+
- ffmpeg installed and available on `PATH`
- A DashScope API key for ASR and embeddings

Install ffmpeg:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

## How to Run

1. Clone this repository and enter the app folder:

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/rag_tutorials/bilibili_rag
```

2. Create your environment file:

```bash
cp .env.example .env
```

Set `DASHSCOPE_API_KEY` for ingestion. By default, the same key is also used with Alibaba Cloud DashScope's OpenAI-compatible chat endpoint:

```env
DASHSCOPE_API_KEY=your-dashscope-api-key
LLM_MODEL=qwen3-max
EMBEDDING_MODEL=text-embedding-v4
CHAT_USE_LLM_ROUTER=false
```

To use Nebius Token Factory for chat and other LLM calls, add:

```env
NEBIUS_API_KEY=your-nebius-api-key
LLM_MODEL=your-nebius-chat-model
```

When `NEBIUS_API_KEY` is set and `OPENAI_BASE_URL` is empty, the app uses
`https://api.tokenfactory.nebius.com/v1`. An explicit `OPENAI_BASE_URL` always
takes precedence. Nebius support covers the chat/LLM path only; video ASR and
embeddings remain DashScope-specific, so ingestion still requires
`DASHSCOPE_API_KEY`.

3. Install and start the backend:

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

The backend API docs will be available at `http://localhost:8000/docs`.

4. In a second terminal, start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Docker Run

For a local full-stack deployment:

```bash
cp .env.example .env
# edit .env and set DASHSCOPE_API_KEY
docker compose up --build
```

Then open:

- Frontend: `http://localhost:3000`
- Backend docs: `http://localhost:8000/docs`

Stop the stack:

```bash
docker compose down
```

## Usage Flow

1. Open the web app and scan the Bilibili QR code to sign in.
2. Select a favorites folder.
3. Sync videos into the local database.
4. Index selected videos so audio is transcribed and embedded.
5. Ask questions in the chat panel and inspect retrieved source snippets.
6. Export transcripts or organized notes to Markdown when needed.

## Configuration Notes

- Keep `.env` in this folder, not inside `frontend/`.
- `DASHSCOPE_API_KEY` is used for ASR and embeddings.
- `NEBIUS_API_KEY` selects Nebius Token Factory for OpenAI-compatible chat calls.
- `OPENAI_API_KEY` can be used with an explicit compatible chat endpoint.
- `OPENAI_BASE_URL` overrides the automatically selected chat endpoint.
- `DASHSCOPE_BASE_URL` is only for ASR and should not be used as the chat base URL.
- The app writes runtime data to `data/` and logs to `logs/`; both are ignored by git.
- After changing model or API key settings, restart the backend.

## Troubleshooting

If you see `The api_key client option must be set`, the backend did not load a valid chat API key. Check that `.env` exists in this folder and includes `NEBIUS_API_KEY`, `OPENAI_API_KEY`, or `DASHSCOPE_API_KEY`.

If embedding initialization fails, reinstall backend dependencies with `pip install -r requirements.txt` and restart the backend.

If some Bilibili audio URLs cannot be fetched directly, the app falls back to downloading audio locally with cookies and transcoding it through ffmpeg before ASR.

## Disclaimer

This project is for personal learning and technical research. Use it only with content and platform access you are allowed to process, and follow Bilibili's platform rules and applicable laws.
