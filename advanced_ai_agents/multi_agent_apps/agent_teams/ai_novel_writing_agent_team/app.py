"""Streamlit UI for the AI Novel Writing Agent Team.

    streamlit run app.py

Enter an API key in the sidebar, describe the story and the chapter goal, then
watch the five agents work. Every agent turn is a real model call, and the
draft can be sent back for revision when the continuity critic rejects it.
"""

from __future__ import annotations

import json

import streamlit as st

from coordinator import NovelTeam
from tools import StoryBible, count_words

st.set_page_config(page_title="AI Novel Writing Agent Team", layout="wide")

# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
st.sidebar.title("🔑 Model")
api_key = st.sidebar.text_input(
    "API key", type="password",
    help="Any OpenAI-compatible key (OpenAI, DeepSeek, Groq, Qwen, a local server…).",
)
base_url = st.sidebar.text_input(
    "Base URL (optional)", value="",
    help="e.g. https://api.deepseek.com/v1 — leave blank for OpenAI.",
)
model = st.sidebar.text_input("Model", value="gpt-4o-mini")
max_revisions = st.sidebar.slider("Max revision rounds", 0, 3, 2)
show_tool_calls = st.sidebar.checkbox("Show tool calls", value=True)

st.sidebar.divider()
st.sidebar.caption(
    "Five agents share one story bible: **Continuity Librarian** gathers what "
    "is already canon, **Story Architect** builds beats, **Scene Designer** "
    "writes scene cards, **Draft Writer** writes prose, **Continuity Critic** "
    "audits it and can send it back for a rewrite."
)

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
st.title("📖 AI Novel Writing Agent Team")
st.caption(
    "A chapter-at-a-time writing team. Agents record characters, places and "
    "events as they go, so later chapters stay consistent with earlier ones."
)

left, right = st.columns([1, 1])
with left:
    premise = st.text_area(
        "Premise", height=140,
        value=(
            "The last tram of the night, in a city that is quietly being rebuilt "
            "around the people who live in it. A driver who has memorised every "
            "timetable starts noticing a passenger who boards but never appears "
            "on her sheets."
        ),
    )
    goal = st.text_input(
        "Chapter goal", value="She decides whether to report the passenger."
    )
with right:
    genre = st.text_input("Genre", value="literary fiction")
    pov = st.selectbox(
        "Point of view",
        ["third person limited", "first person", "third person omniscient"],
    )
    words = st.slider("Words for this chapter", 300, 3000, 900, step=100)
    style = st.text_input("Style notes (optional)", value="")

run = st.button("▶️ Write the chapter", type="primary", disabled=not api_key)
if not api_key:
    st.info("Add an API key in the sidebar to run the team.")

# --------------------------------------------------------------------------- #
# Run
# --------------------------------------------------------------------------- #
if run:
    from openai import OpenAI

    if "bible" not in st.session_state:
        st.session_state.bible = StoryBible()
    if "chapters" not in st.session_state:
        st.session_state.chapters = []

    bible: StoryBible = st.session_state.bible
    bible.premise = premise
    bible.title = premise[:60]

    client = OpenAI(api_key=api_key, base_url=base_url or None)
    chapter_number = len(st.session_state.chapters) + 1

    status = st.status("Agents working…", expanded=True)
    slot = status.empty()

    def on_event(event) -> None:
        icons = {"running": "…", "done": "✓", "revise": "↻"}
        slot.write(
            f"{icons.get(event.status, '·')} **{event.emoji} {event.name}**"
            + (f" — {event.detail}" if event.detail else "")
        )

    team = NovelTeam(
        client=client, model=model, bible=bible,
        max_revisions=max_revisions, on_event=on_event,
    )
    result = team.run_chapter(
        chapter=chapter_number, goal=goal, target_words=words, pov=pov,
        genre=genre, style=style,
    )
    verdict = str(result.critic.get("verdict", "pass")).lower()
    status.update(
        label=f"Chapter {chapter_number} done — critic: {verdict}"
        + (f", {result.revisions} revision(s)" if result.revisions else ""),
        state="complete",
    )
    st.session_state.chapters.append(result)

    tabs = st.tabs(
        ["📄 Chapter", "🔍 Critic report", "🏛️ Beats", "🎬 Scene cards",
         "📚 Story bible", "🧾 Agent log"]
    )
    with tabs[0]:
        st.markdown(result.draft)
        st.caption(f"{count_words(result.draft)} words")
        st.download_button(
            "Download chapter (.md)", result.draft,
            file_name=f"chapter_{chapter_number:02d}.md",
        )
    with tabs[1]:
        st.json(result.critic)
    with tabs[2]:
        st.json(result.beats)
    with tabs[3]:
        st.json(result.scenes)
    with tabs[4]:
        st.text(bible.recap())
        st.download_button(
            "Download story bible (.json)", bible.to_json(),
            file_name="story_bible.json", mime="application/json",
        )
    with tabs[5]:
        for line in result.timeline_of_steps:
            st.write(line)
        if show_tool_calls:
            for key, agent_result in team.results.items():
                if not agent_result.tools:
                    continue
                with st.expander(f"{agent_result.name} — tool calls"):
                    for trace in agent_result.tools:
                        st.code(
                            f"{trace.name}({json.dumps(trace.args, ensure_ascii=False)})"
                            f"\n-> {trace.result[:400]}"
                        )

st.divider()
st.caption(
    "Keep clicking **Write the chapter** to continue the story: the bible "
    "carries characters, places and events forward, and the librarian briefs "
    "each new chapter on what is already canon."
)
