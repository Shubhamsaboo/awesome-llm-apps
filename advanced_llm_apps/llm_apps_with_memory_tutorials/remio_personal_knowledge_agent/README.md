## Remio Personal Knowledge Agent

This Streamlit app turns the Remio CLI into a local-first personal knowledge agent. It searches and answers questions over Remio's indexed notes, files, webpages, recordings, emails, messages, images, and other local knowledge sources.

### Features

- Uses Remio's local index and vector retrieval instead of repeatedly scanning raw files
- Supports semantic note search and RAG-style Q&A
- Works with Remio's pre-parsed files, webpages, recordings, notes, emails, messages, and images
- Keeps context prompts smaller by retrieving relevant indexed chunks first
- Detects missing Remio CLI or desktop app and points users to https://remio.ai/

### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_llm_apps/llm_apps_with_memory_tutorials/remio_personal_knowledge_agent
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Install and open the Remio desktop app

Remio CLI depends on the desktop app. Download or open Remio from:

```text
https://remio.ai/
```

Then verify:

```bash
remio doctor
```

4. Run the Streamlit app

```bash
streamlit run remio_personal_knowledge_agent.py
```

### Why Remio for agent memory?

General-purpose agents often waste tokens by reading whole files or repeatedly using shell search over personal folders. Remio pre-parses and indexes personal knowledge locally, then exposes targeted retrieval through the CLI. This lets an agent retrieve only the relevant context before synthesizing an answer.

