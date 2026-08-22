## 🎯 AI Career Coach with Memory (ADK Multi-Agent)
This Streamlit app implements a multi-agent career coaching assistant built with Google's Agent Development Kit (ADK). A **career orchestrator agent** delegates each question to the right **specialist sub-agent** (resume, interview practice, skills/learning roadmap, or salary), while **Mem0 + Qdrant** remember each candidate's career history across sessions.

The point isn't just routing between specialists — it's that the advice actually changes the longer you use it. Ask "what should I focus on?" in your first session and you get generic advice. Ask the same thing two months later, and the app already knows your target roles, your tech stack, and which interview topics you've struggled with, so the answer is specific to you instead of generic.

### Features
- Root `career_orchestrator` (Google ADK `LlmAgent`) that automatically delegates to `resume_agent`, `interview_agent`, `skills_roadmap_agent`, or `salary_agent` sub-agents based on the question
- Each specialist has its own focused tool (`get_candidate_resume`, `get_practice_question`, `get_learning_resource`, `get_salary_benchmark`) backed by mock data — swap these for real integrations (a real resume/profile store, a real interview question bank, a course catalog, Levels.fyi/Glassdoor-style salary data)
- Mem0 + Qdrant recall relevant past context for the current candidate before the orchestrator routes the message — years of experience, target roles, tech stack, past interview weak spots, and more, depending on what's come up in prior conversations
- Every exchange is written back to Mem0 so the next session (even with a brand-new ADK session) starts with full context
- Sidebar "View my memory" to inspect what's been remembered for a given candidate email
- Runs on a **single Google API key** — no Docker, no Qdrant server, no OpenAI key. Mem0 is configured to use Gemini for both its internal LLM (fact extraction) and its embeddings, and Qdrant runs in embedded on-disk mode (`./qdrant_storage/`), not as a separate service.

### How it works
1. Candidate sends a message.
2. The app queries Mem0 for memories relevant to that message, for that `user_id`.
3. The message plus the retrieved memory context is handed to the ADK `career_orchestrator`.
4. The orchestrator's LLM decides which specialist sub-agent should handle it (resume, interview, skills, or salary) and transfers control.
5. The specialist calls its tool if needed and replies — using the candidate's known profile info (e.g. target role, weak interview areas) when the message itself doesn't spell it out.
6. The candidate's message and the final answer are both written back into Mem0.

### How to get Started?

1. Clone the GitHub repository
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Get a Google API key for Gemini from [Google AI Studio](https://aistudio.google.com/apikey) — you'll paste it into the app's UI at runtime. That's the only credential this app needs.

4. Run the Streamlit App
```bash
streamlit run adk_career_coach_agent_memory.py
```

The first run creates a `qdrant_storage/` folder next to the script — that's Mem0's embedded, on-disk vector store. Delete it if you want to wipe all remembered candidate history.

### Try it out
- *"Can you review my resume for a backend engineer role?"* (as `demo@example.com`) → routes to `resume_agent`, which calls `get_candidate_resume` to fetch the resume on file, then gives feedback tailored to that candidate's actual experience level and skills rather than generic advice.
- *"I have an Amazon system design interview coming up, can we practice?"* → routes to `interview_agent`, pulls a sample question via `get_practice_question`.
- *"I keep failing system design rounds, what should I study?"* → routes to `skills_roadmap_agent`.
- *"What should I expect for a backend engineer role in Seattle?"* → routes to `salary_agent`.
- Ask something open-ended like *"what should I focus on?"* after a few of the above, in a new session — the answer should reference your specific target role and weak areas instead of giving generic advice.

### Using a real Qdrant server instead
The embedded mode above is the default because it needs nothing beyond the one API key. If you'd rather point at a real Qdrant instance (shared across machines, or just persistent/inspectable via Qdrant's dashboard), swap the `vector_store` block in `MEM0_CONFIG` for:
```python
"vector_store": {
    "provider": "qdrant",
    "config": {
        "collection_name": "adk_career_coach",
        "host": "localhost",  # or use "url"/"api_key" for Qdrant Cloud
        "port": 6333,
        "embedding_model_dims": 768,
    },
},
```
and start a server first, either via Docker (`docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage:z qdrant/qdrant`) or the standalone Windows `qdrant.exe` binary from the [Qdrant releases page](https://github.com/qdrant/qdrant/releases).

### Notes / next steps
- This is a sketch: `MOCK_RESUMES`, `MOCK_INTERVIEW_QUESTIONS`, `MOCK_LEARNING_RESOURCES`, and `MOCK_SALARY_DATA` are stand-ins for real data sources (a real resume/profile store, a real question bank, a course catalog, a salary data provider).
- `google-adk`'s API is young and moves fast — if something doesn't match your installed version, check the [ADK docs](https://google.github.io/adk-docs/) for the current `LlmAgent` / `Runner` / `sub_agents` signatures.
- Natural extensions: add a "Negotiation Agent" for when an offer is actually on the table, an application tracker (which companies, which stage), or split `interview_agent` into separate behavioral and system-design specialists.
