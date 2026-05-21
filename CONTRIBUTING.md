# Contributing to Awesome LLM Apps

Thank you for your interest in contributing. This guide explains how to submit a new template, fix a bug, or improve an existing example.

## What makes a good contribution

Every template in this repo is **self-contained and runnable**. Before you submit, ask:

1. Can someone clone just my directory and run it in 3 commands?
2. Are all dependencies listed in `requirements.txt` with version pins?
3. Does my README explain what the app does, what keys are needed, and how to run it?

## Submitting a new template

### Directory structure

Place your template under the appropriate top-level category:

```
<category>/
  your_template_name/
    README.md            # Required
    requirements.txt     # Required, with pinned versions
    your_app.py          # Main application file
    .env.example         # Required if any API keys are needed
```

**Categories:**
- `starter_ai_agents/` - Single-purpose beginner-friendly agents
- `advanced_ai_agents/single_agent_apps/` - Production-quality single agents
- `advanced_ai_agents/multi_agent_apps/` - Multi-agent systems and teams
- `mcp_ai_agents/` - Agents using Model Context Protocol
- `rag_tutorials/` - Retrieval-augmented generation examples
- `voice_ai_agents/` - Voice and speech agents
- `advanced_llm_apps/` - Advanced LLM application patterns
- `ai_agent_framework_crash_course/` - Framework-specific tutorials

### requirements.txt

Pin your dependencies to exact versions or minimum bounds:

```
# Good - reproducible installs
streamlit==1.44.1
agno>=2.2.10
openai>=1.102.0

# Bad - breaks when upstream releases change
streamlit
openai
```

Do **not** list Python standard library modules (`asyncio`, `uuid`, `json`, `os`, etc.) in requirements.txt. They ship with Python and listing them can install unrelated PyPI packages.

### API key handling

Use `st.sidebar.text_input` for Streamlit apps or `os.environ.get()` with a `.env.example` file for non-Streamlit apps.

Never hardcode API key values, even as placeholders like `"your_api_key_here"`. Instead:

```python
# Streamlit pattern (preferred for Streamlit apps)
api_key = st.sidebar.text_input("OpenAI API Key", type="password")

# Environment variable pattern (non-Streamlit)
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Set OPENAI_API_KEY in your environment or .env file")
```

### README template

Every template directory needs a README with at minimum:

```markdown
# Template Name

Brief description of what this app does.

## Features
- Feature 1
- Feature 2

## Getting Started

### Prerequisites
- Python 3.10+
- API keys: OpenAI (required), Firecrawl (optional)

### Installation
pip install -r requirements.txt

### Running
streamlit run app.py
```

## Fixing a bug or improving an existing template

1. Fork the repo and create a branch: `git checkout -b fix/template-name-description`
2. Make your change in the specific template directory
3. Test that the template still runs end-to-end
4. Open a pull request with a clear description of what you fixed and why

## Pull request checklist

Before opening your PR, verify:

- [ ] The template runs successfully with `pip install -r requirements.txt` followed by the run command
- [ ] `requirements.txt` has pinned or bounded versions for all dependencies
- [ ] No standard library modules in `requirements.txt`
- [ ] No hardcoded API keys or secrets anywhere in the code
- [ ] A `.env.example` file exists if the app needs API keys
- [ ] The README explains prerequisites, installation, and how to run
- [ ] The code follows the existing style in the repo (Streamlit sidebar for keys, clean imports)

## Code style

- Use meaningful variable and function names
- Keep files focused - one main application file per template
- Add comments for non-obvious logic
- Follow PEP 8 for Python code

## Questions?

Open an issue or start a discussion. For detailed tutorials on building LLM apps, visit [Unwind AI](https://www.theunwindai.com).
