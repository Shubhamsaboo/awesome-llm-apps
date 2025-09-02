# 📝 Meeting Minutes Generator (Open Source)

An LLM-powered app that generates professional meeting minutes from Zoom, Microsoft Teams, or Google Meet transcripts.

## ✨ Features
- Upload a transcript file (`.txt` or `.vtt`)
- AI-generated:
  - Concise meeting summary
  - Key decisions made
  - Action items with assignees
- Export as Markdown
- **Runs 100% locally using [Ollama](https://ollama.ai)**

## ⚙️ Installation

1. Install Python 3.8+
2. Create virtual env - python3 -m venv env
3. Activate virtual env - source ./env/bin/activate
4. Install Ollama → https://ollama.ai
5. Pull a model (e.g. LLaMA 3) - `olama pull llama3`
6. Install python dependencies - `pip install -r requirements.txt`
7. Run the app - `streamlit run meeting_minutes_generator.py`
8. Run ollama - `ollama run llama3`
9. Then open http://localhost:8501 in your browser.

🔑 Note:
No API key required.
You can swap "llama3" with any local model supported by Ollama (e.g., mistral, gemma).


Sample transcript file:

```
[00:00] Alice: Good morning everyone, thanks for joining the sprint planning meeting. 
[00:05] Bob: Morning! Let's start with last week’s progress.
[00:12] Charlie: The API integration is complete, and testing went well. 
[00:20] Alice: Great, so we can mark that as done. Any blockers?
[00:28] Bob: We’re still waiting on the final UI designs from the design team. 
[00:35] Alice: Noted. I’ll follow up with them today. 
[00:42] Charlie: For this sprint, we need to prioritize the authentication module. 
[00:50] Bob: Yes, deadline is next Friday. I’ll take ownership of backend tasks. 
[00:58] Alice: Perfect. Charlie, can you handle frontend integration?
[01:05] Charlie: Sure, I’ll do that. 
[01:10] Alice: Action items: Bob works on backend, Charlie on frontend, and I’ll follow up with design. Let’s aim to sync again mid-week.
[01:20] Bob: Sounds good. 
[01:22] Charlie: Agreed. 
[01:25] Alice: Great, thanks everyone!
```
