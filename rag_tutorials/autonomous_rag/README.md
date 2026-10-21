# 🤖 AutoRAG: Autonomous RAG with GPT-4o and Vector Database

**🎓 FREE Step-by-Step Tutorial**

**👉 [Click here to follow our complete step-by-step tutorial](https://www.theunwindai.com/p/build-autonomous-rag-app-using-gpt-4o-and-vector-database) and learn how to build this from scratch with detailed code walkthroughs, explanations, and best practices.**

This Streamlit application implements an Autonomous Retrieval-Augmented Generation (RAG) system using OpenAI's GPT-4o model and PgVector database. It allows users to upload PDF documents, add them to a knowledge base, and query the AI assistant with context from both the knowledge base and web searches.
Features

### Freatures 
- Chat interface for interacting with the AI assistant
- PDF document upload and processing
- Knowledge base integration using PostgreSQL and Pgvector
- Web search capability using DuckDuckGo
- Persistent storage of assistant data and conversations

### How to get Started?

1. Clone the GitHub repository
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/rag_tutorials/autonomous_rag
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Ensure PgVector Database is running:
The app expects PgVector to be running on [localhost:5532](http://localhost:5532/). Adjust the configuration in the code if your setup is different.

```bash
docker run -d \
  -e POSTGRES_DB=ai \
  -e POSTGRES_USER=ai \
  -e POSTGRES_PASSWORD=ai \
  -e PGDATA=/var/lib/postgresql/data/pgdata \
  -v pgvolume:/var/lib/postgresql/data \
  -p 5532:5432 \
  --name pgvector \
  phidata/pgvector:16
```

4. Run the Streamlit App
```bash
streamlit run autorag.py
```

### Option: Use Neon (free cloud Postgres + pgvector, no Docker)

`autorag_neon.py` runs the same app against a hosted [Neon](https://neon.tech) database with Gemini for the LLM and embeddings.

1. Create a free Neon project and copy the connection string from **Connect**.
2. Enable pgvector: in the Neon dashboard open **SQL Editor**, select your database (e.g. `neondb`) and run:
```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify it is enabled
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
```
   The app also runs `CREATE EXTENSION IF NOT EXISTS vector` on startup, so this step is optional when connecting as the database owner (e.g. `neondb_owner`); run it manually if you use a role without permission to create extensions.
3. Copy `.env.example` to `.env` and fill in `NEON_DATABASE_URL` and `GEMINI_API_KEY`.
4. Run it (the `ai` schema and tables are created automatically on first run):
```bash
pip install -r requirements.txt
streamlit run autorag_neon.py
```