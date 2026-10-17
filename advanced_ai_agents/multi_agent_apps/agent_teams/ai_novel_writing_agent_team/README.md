# 📖 AI Novel Writing Agent Team

Five LLM agents write a novel one chapter at a time and keep it consistent.

Long-form fiction does not fail because the model can't write a sentence — it
fails because nothing remembers what was already written. This example gives
the team a **shared story bible**: agents record characters, places and plot
events as they invent them, later agents read from it, and a dedicated critic
audits each chapter against it before the chapter is accepted.

## Features

- **Multi-Agent System** (each agent is a real model call with its own
  temperature and tools)
  - 📚 **Continuity Librarian** — reads the story bible and briefs the team on
    what is already canon (`bible_recap`, `bible_search`)
  - 🏛️ **Story Architect** — turns the chapter goal into 3–6 beats that each
    change something
  - 🎬 **Scene Designer** — converts beats into scene cards with concrete
    sensory anchors and a word budget
  - ✍️ **Draft Writer** — writes the finished prose and records new entities and
    events into the bible as it goes (`record_entity`, `record_event`,
    `text_stats`)
  - 🔍 **Continuity Critic** — audits the draft against the bible for
    contradictions, skipped beats, characters knowing things they were never
    told, and repeated phrasing (`bible_dump`, `repetition_check`)

- **Shared Story Bible** — an in-memory store of entities (characters, places,
  objects, factions) and chapter-by-chapter timeline events. Because every
  agent reads *and writes* it, chapter 3 cannot silently contradict chapter 1.

- **Revision loop, not a straight line** — when the critic returns
  `verdict: "revise"`, the coordinator feeds its `fix_instructions` back to the
  Draft Writer and re-drafts (configurable number of rounds). Only a clean
  verdict ends the chapter.

- **Tool use is real** — the agents call the tools above through standard
  OpenAI function calling; the drafter typically fires dozens of
  `record_entity` / `record_event` / `text_stats` calls per chapter.

- **Any OpenAI-compatible model** — OpenAI, DeepSeek, Groq, Qwen, a local
  server: set `OPENAI_BASE_URL` and `--model`.

## How It Works

```
chapter goal
    │
    ▼
📚 Librarian ──► continuity brief ─┐
                                   ▼
                          🏛️ Architect ──► beats (JSON)
                                   │
                                   ▼
                          🎬 Designer ──► scene cards (JSON)
                                   │
                                   ▼
                          ✍️ Drafter ──► draft prose ──► story bible
                                   │            ▲
                                   ▼            │ fix instructions
                          🔍 Critic ── verdict ─┘  (revise → re-draft)
                                   │
                                 pass
                                   ▼
                          accepted chapter + updated bible
```

## Requirements

- `openai>=1.40.0`
- `streamlit>=1.33.0` (for the web UI)

Plus an API key for any OpenAI-compatible endpoint.

## How to Run

### 1. Command line (makes real model calls)

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/multi_agent_apps/agent_teams/ai_novel_writing_agent_team
pip install -r requirements.txt

export OPENAI_API_KEY=sk-...
python novel_team.py \
  --premise "The last tram of the night, in a city being rebuilt around the people who live in it. A driver notices a passenger who boards but never appears on her timetable." \
  --goal "She decides whether to report the passenger." \
  --chapters 2 --words 900 --out out
```

Each chapter is written by all five agents; the script prints progress, the
draft and the critic's verdict, then writes `out/chapter_01.md`,
`chapter_01_beats.json`, `chapter_01_scenes.json`, `chapter_01_critic.json` and
`story_bible.json`.

Using a different provider:

```bash
export OPENAI_BASE_URL=https://api.deepseek.com/v1
export OPENAI_MODEL=deepseek-chat
python novel_team.py --premise "..." --goal "..."
```

Want to see the agent line-up and prompts **without** spending a token?

```bash
python novel_team.py --dry-run     # prints the plan only, calls nothing
```

### 2. Web UI

```bash
streamlit run app.py
```

Enter your API key in the sidebar, describe the story and the chapter goal, and
press **Write the chapter**. You get tabs for the chapter, the critic's report,
the beats, the scene cards, the story bible and the agent log (including every
tool call). Pressing the button again continues the story — the bible carries
forward.

## Usage

1. Enter the API key (and optionally a base URL and model) in the sidebar.
2. Fill in the premise, the chapter goal, genre, POV and word budget.
3. Run, then inspect the critic's report: `verdict: "revise"` means the chapter
   was sent back and rewritten before you saw it.

## Notes

- Everything the team needs is in this folder — no other repository, service or
  dataset is required.
- `test_team.py` exercises the coordinator offline with a scripted stub client:
  it asserts that a `revise` verdict actually triggers a rewrite and that the
  agents' tool calls mutate the story bible. Run it with
  `python test_team.py` (no API key needed).
- Cost scales with chapter length and revision rounds; a ~900-word chapter is
  roughly six to ten model calls.
