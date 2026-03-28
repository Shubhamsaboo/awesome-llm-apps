# Self-Improving Agent Skills

Automatically optimize your agent skills using Gemini's reasoning capabilities. Upload a skill, let AI generate test scenarios and evaluation criteria, then watch as your skill improves itself through iterative optimization.

## How It Works

This app implements an automated skill improvement loop inspired by Karpathy's autoresearch methodology:

1. **Upload**: Drop in your skill folder (following [agentskills.io](https://agentskills.io) spec)
2. **Configure**: AI generates test scenarios and evaluation criteria. Edit, add, or regenerate as needed
3. **Optimize**: The system runs your skill, scores outputs, mutates the prompt one change at a time, and keeps improvements
4. **Results**: Download your improved skill with a detailed changelog

The optimization loop:
- Runs the skill against test scenarios
- Scores outputs using binary yes/no evaluation criteria
- Analyzes failure patterns
- Proposes ONE targeted change to the skill prompt
- Tests the change
- Keeps it if score improves, reverts if not
- Repeats until 95%+ pass rate or max rounds reached

## Architecture

```
self-improving-skill/
├── backend/              # FastAPI server + optimization engine
│   ├── app.py           # REST API endpoints + SSE streaming
│   ├── optimizer.py     # Core optimization logic
│   ├── requirements.txt
│   └── .env.example
├── frontend/            # Next.js + React + Tailwind
│   ├── src/
│   │   ├── app/         # Main page + layout
│   │   └── components/  # Upload, Config, Running, Results steps
│   ├── package.json
│   └── *.config.ts
├── example_skills/      # Sample skills to test
│   ├── code-reviewer/
│   └── content-writer/
└── README.md
```

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, google-genai SDK
- **Frontend**: Next.js 15, React 19, Tailwind CSS v4, Recharts
- **AI**: Gemini 2.5 Flash for analysis, execution, scoring, and mutation
- **Real-time**: Server-Sent Events (SSE) for live optimization progress

## Quick Start

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment (optional, can also pass via header)
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run server
python app.py
# Server runs on http://localhost:8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
# App runs on http://localhost:3000
```

### Usage

1. Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)
2. Open http://localhost:3000
3. Upload a skill folder as a .zip file (or try an example)
4. Enter your Gemini API key
5. Review and edit the generated test scenarios and evaluation criteria
6. Click "Start Optimization" and watch the score climb
7. Download your improved skill when complete

## Skill Format

Skills follow the [agentskills.io](https://agentskills.io) specification:

```
my-skill/
├── SKILL.md           # Required: YAML frontmatter + instructions
├── scripts/           # Optional: executable code
├── references/        # Optional: additional docs
└── assets/            # Optional: templates, resources
```

Example SKILL.md:

```markdown
---
name: my-skill
description: What this skill does and when to use it
license: MIT
metadata:
  author: your-name
  version: "1.0"
---

# My Skill

Your skill instructions here...
```

## Example Skills

Two example skills are included:

- **code-reviewer**: Reviews code for security, performance, and best practices
- **content-writer**: Writes marketing copy following style guidelines

Create a zip file from an example:

```bash
cd example_skills
zip -r code-reviewer.zip code-reviewer/
```

Then upload the zip in the app.

## How the Optimization Works

### 1. Analysis Phase
Gemini analyzes your skill and generates:
- 3-5 diverse test scenarios
- 3-6 binary evaluation criteria (yes/no questions)

### 2. Baseline Run
The skill runs against all scenarios. Each output is scored against all evaluation criteria. This establishes the starting score.

### 3. Optimization Loop
For each round:
1. Analyze which evaluation criteria fail most frequently
2. Use Gemini to propose ONE specific change to improve the skill
3. Run the modified skill against all scenarios
4. Compare scores
5. Keep the change if score improved, revert if not
6. Repeat until 95%+ pass rate for 3 consecutive rounds or max rounds reached

### 4. Output
- Improved SKILL.md with all successful changes applied
- Detailed changelog of what changed and why
- Performance comparison (baseline vs final)

## API Endpoints

- `POST /api/upload` - Upload skill zip file
- `POST /api/analyze` - Generate scenarios and evals (requires GEMINI_API_KEY header)
- `POST /api/regenerate` - Regenerate scenarios and evals
- `POST /api/update-config` - Save user's selected/edited config
- `POST /api/start/{session_id}` - Start optimization
- `GET /api/stream/{session_id}` - SSE stream of optimization progress
- `POST /api/stop/{session_id}` - Stop optimization
- `GET /api/download/{session_id}` - Download improved skill

## Configuration

### Backend

Set `GEMINI_API_KEY` in `.env` or pass via request header.

### Frontend

API key is stored in component state (not persisted) and sent with each request.

### Optimization Parameters

In `RunningStep.tsx`, adjust `max_rounds`:

```typescript
body: JSON.stringify({
  max_rounds: 20,  // Default: 20
}),
```

In `optimizer.py`, adjust model:

```python
def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
```

## Development

### Backend Tests

```bash
cd backend
python -c "from optimizer import SkillOptimizer; print('OK')"
```

### Frontend Build

```bash
cd frontend
npm run build
```

### Live Development

Both servers support hot reload. Edit code and see changes immediately.

## Based on Karpathy's Autoresearch

This tool applies Andrej Karpathy's autoresearch methodology (using LLMs to iteratively improve their own prompts) to agent skills. The key insight: rather than manually tweaking prompts, define success criteria and let the AI optimize itself.

Original concept: [https://github.com/karpathy/autoresearch](https://github.com/karpathy/autoresearch)