# LexReviewer — End-to-End Demo

A self-contained, runnable walkthrough of the full LexReviewer workflow.  
No additional setup is needed beyond a running backend — the script generates its own synthetic PDF if you don't supply one.

---

## What the demo does

| Step | API call | What you'll see |
|------|----------|-----------------|
| 0 | `GET /docs` | Backend connectivity check |
| 1 | *(local)* | Generates or loads a PDF |
| 2 | `POST /upload-documents` | Chunks, embeds and indexes the document |
| 3 | `POST /ask` × 3 | Streams answers with agent reasoning & bounding-box citations |
| 4 | `GET /get-history` | Shows the persisted conversation turns |
| 5 | `DELETE /delete-vector` + `/clear-history` | Tears down the demo data |

The built-in synthetic document is a **commercial lease agreement** containing clauses about rent, maintenance, insurance, and termination — good coverage for exercising the retrieval pipeline.

---

## Prerequisites

- **Python 3.10+**
- **OpenAI API key** (`OPENAI_API_KEY`)
- **Unstructured.io API key** (`UNSTRUCTURED_API_KEY`)
- MongoDB and Qdrant — either via Docker (recommended) or self-managed

---

## Quickstart — Docker (recommended)

The fastest path: one command spins up MongoDB, Qdrant, **and** the LexReviewer API.

```bash
# 1. Configure secrets in the project root
cp ../.env.example ../.env
#    → set OPENAI_API_KEY and UNSTRUCTURED_API_KEY in ../.env

# 2. Start all services
docker compose up -d

# 3. Wait for the API to be healthy, then run the demo
pip install -r requirements.txt
python demo.py
```

To stop and clean up:
```bash
docker compose down -v   # -v removes volumes (wipes stored data)
```

---

## Quickstart — Manual

If you prefer to manage MongoDB and Qdrant yourself:

```bash
# 1. Start MongoDB and Qdrant however you prefer, then start the API:
#    (from the project root)
python app.py

# 2. Enter this folder and install the demo dependency
cd demo
pip install -r requirements.txt

# 3. Run the demo
python demo.py
```

Expected runtime: **~60–90 seconds** (most of it is Unstructured.io chunking on first run).  
On subsequent runs the document is already indexed so Step 2 is skipped automatically.

---

## Options

```
python demo.py --help

usage: demo.py [-h] [--url URL] [--pdf PATH]

  --url URL   Base URL of the running backend  (default: http://localhost:8000)
  --pdf PATH  Path to your own PDF to upload.  Omit to use the built-in contract.
```

### Use your own PDF

```bash
python demo.py --pdf /path/to/my_contract.pdf
```

### Point at a remote backend

```bash
python demo.py --url https://my-lexreviewer.example.com
```

---

## Sample output

```
──────────────────────────────────────────────────────────────────────
  Step 0 — Checking backend connectivity
──────────────────────────────────────────────────────────────────────
  ✅  Backend reachable at http://localhost:8000  (status 200)

──────────────────────────────────────────────────────────────────────
  Step 1 — Preparing PDF document
──────────────────────────────────────────────────────────────────────
  ℹ️   No PDF supplied — generating a synthetic commercial lease contract …
  ✅  Generated in-memory PDF  (3,412 bytes)

──────────────────────────────────────────────────────────────────────
  Step 2 — Uploading & indexing the document
──────────────────────────────────────────────────────────────────────
  ℹ️   Uploading document … (this may take ~30 s while Unstructured.io chunks it)
  ✅  Indexed successfully in 28.4s

──────────────────────────────────────────────────────────────────────
  Step 3 — Asking questions (streaming RAG answers)
──────────────────────────────────────────────────────────────────────

  Question 1/3: What is the monthly rent amount and when is it due?
  ··············································
  Answer: The monthly base rent is $8,500, due on the first day of each
  calendar month. A late fee of 5% applies if payment is received after
  the 5th of the month (Section 3).

  Source references returned: 1
    📄 Page 1  bbox=(50.0,480.0)→(562.0,520.0)
...

──────────────────────────────────────────────────────────────────────
  🎉  LexReviewer demo complete!
```

---

## Files

```
demo/
├── demo.py             # The runnable demo script
├── docker-compose.yml  # Spins up MongoDB + Qdrant + LexReviewer API
├── Dockerfile          # Builds the LexReviewer API image
├── requirements.txt    # Single dependency: requests
└── README.md           # This file
```

---

## How it works internally

```
demo.py
  │
  ├─ _build_minimal_pdf()   Pure-Python PDF builder — no external lib required
  │
  ├─ upload_document()      POST /upload-documents  (base64-encodes the PDF)
  ├─ collection_exists()    POST /collection-exists (skip re-upload on reruns)
  ├─ ask_question()         POST /ask               (streams NDJSON, prints live)
  ├─ get_history()          GET  /get-history
  ├─ clear_history()        DELETE /clear-history
  └─ delete_vector()        DELETE /delete-vector
```

The only dependency (`requests`) is used for all HTTP calls.  
`_build_minimal_pdf` constructs a spec-compliant PDF entirely in memory so the demo works without `fpdf2`, `reportlab`, or any other PDF library.