# AG2 Adaptive Research Team

A Streamlit app that blends agent teamwork with agent-enabled routing and fallback, built entirely on AG2.

## What This Shows

- **Agent teamwork**: explicit roles and sequential handoffs
- **Agent-enabled routing**: a clear decision step with local-doc vs web fallback
- **AG2-first implementation**: no Microsoft AutoGen dependency; installs via `ag2[openai]`

## Features

- Local document upload (PDF, TXT, MD)
- Routing decision based on document coverage
- Optional web fallback via SearxNG
- Verifier step to check evidence sufficiency
- Final synthesis with citations

## How To Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the app:

```bash
streamlit run app.py
```

3. Provide your OpenAI API key in the sidebar and ask a question.

## How It Works

1. **Triage Agent** decides whether the question should be answered from local docs or the web.
2. **Local/Web Research Agent** collects evidence.
3. **Verifier Agent** checks evidence strength.
4. **Synthesizer Agent** produces the final answer with citations.

## Optional Add-ons (AG2 0.11)

- **AG-UI protocol integration** for richer UI rendering
- **OpenTelemetry tracing** for debugging multi-agent workflows

These are optional and not required to run this example.

## Notes

- Default model used is `gpt-5-nano`. You can change it in the sidebar before running a query.
- Web fallback uses the SearxNG public instance at `https://searxng.site/search`. This instance may be rate-limited.
