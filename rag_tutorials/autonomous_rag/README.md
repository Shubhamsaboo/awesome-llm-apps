## 🤖 AutoRAG: Autonomous RAG with GPT-4o and Vector Database
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
