"""Research Planner using Gemini Interactions API - demonstrates stateful conversations, model mixing, and background execution."""

import streamlit as st, time, re
from google import genai

def get_text(outputs): return "\n".join(o.text for o in (outputs or []) if hasattr(o, 'text') and o.text) or ""

def parse_tasks(text):
    return [{"num": m.group(1), "text": m.group(2).strip().replace('\n', ' ')} 
            for m in re.finditer(r'^(\d+)[\.\)\-]\s*(.+?)(?=\n\d+[\.\)\-]|\n\n|\Z)', text, re.MULTILINE | re.DOTALL)]

def wait_for_completion(client, iid, timeout=300):
    progress, status, elapsed = st.progress(0), st.empty(), 0
    while elapsed < timeout:
        interaction = client.interactions.get(iid)
        if interaction.status != "in_progress": progress.progress(100); return interaction
        elapsed += 3; progress.progress(min(90, int(elapsed/timeout*100))); status.text(f"⏳ {elapsed}s..."); time.sleep(3)
    return client.interactions.get(iid)

# Setup
st.set_page_config(page_title="Research Planner", page_icon="🔬", layout="wide")
st.title("🔬 AI Research Planner & Executor Agent (Gemini Interactions API) ✨")

for k in ["plan_id", "plan_text", "tasks", "research_id", "research_text", "synthesis_text", "infographic"]:
    if k not in st.session_state: st.session_state[k] = [] if k == "tasks" else None

with st.sidebar:
    api_key = st.text_input("🔑 Google API Key", type="password")
    if st.button("Reset"): [setattr(st.session_state, k, [] if k == "tasks" else None) for k in ["plan_id", "plan_text", "tasks", "research_id", "research_text", "synthesis_text", "infographic"]]; st.rerun()
    st.markdown("""
    ### How It Works
    1. **Plan** → Gemini 3 Flash creates research tasks
    2. **Select** → Choose which tasks to research  
    3. **Research** → Deep Research Agent investigates
    4. **Synthesize** → Gemini 3 Pro writes report + TL;DR infographic
    
    Each phase chains via `previous_interaction_id` for context.
    """)
client = genai.Client(api_key=api_key) if api_key else None
if not client: st.info("👆 Enter API key to start"); st.stop()

# Phase 1: Plan
research_goal = st.text_area("📝 Research Goal", placeholder="e.g., Research B2B HR SaaS market in Germany")
if st.button("📋 Generate Plan", disabled=not research_goal, type="primary"):
    with st.spinner("Planning..."):
        try:
            i = client.interactions.create(model="gemini-3-flash-preview", input=f"Create a numbered research plan for: {research_goal}\n\nFormat: 1. [Task] - [Details]\n\nInclude 5-8 specific tasks.", tools=[{"type": "google_search"}], store=True)
            st.session_state.plan_id, st.session_state.plan_text, st.session_state.tasks = i.id, get_text(i.outputs), parse_tasks(get_text(i.outputs))
        except Exception as e: st.error(f"Error: {e}")

# Phase 2: Select & Research  
if st.session_state.plan_text:
    st.divider(); st.subheader("🔍 Select Tasks & Research")
    selected = [f"{t['num']}. {t['text']}" for t in st.session_state.tasks if st.checkbox(f"**{t['num']}.** {t['text']}", True, key=f"t{t['num']}")]
    st.caption(f"✅ {len(selected)}/{len(st.session_state.tasks)} selected")
    
    if st.button("🚀 Start Deep Research", type="primary", disabled=not selected):
        with st.spinner("Researching (2-5 min)..."):
            try:
                i = client.interactions.create(agent="deep-research-pro-preview-12-2025", input=f"Research these tasks thoroughly with sources:\n\n" + "\n\n".join(selected), previous_interaction_id=st.session_state.plan_id, background=True, store=True)
                i = wait_for_completion(client, i.id)
                st.session_state.research_id, st.session_state.research_text = i.id, get_text(i.outputs) or f"Status: {i.status}"
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")

if st.session_state.research_text:
    st.divider(); st.subheader("📄 Research Results"); st.markdown(st.session_state.research_text)

# Phase 3: Synthesis + Infographic
if st.session_state.research_id:
    if st.button("📊 Generate Executive Report", type="primary"):
        with st.spinner("Synthesizing report..."):
            try:
                i = client.interactions.create(model="gemini-3-pro-preview", input=f"Create executive report with Summary, Findings, Recommendations, Risks:\n\n{st.session_state.research_text}", previous_interaction_id=st.session_state.research_id, store=True)
                st.session_state.synthesis_text = get_text(i.outputs)
            except Exception as e: st.error(f"Error: {e}"); st.stop()
        
        with st.spinner("Creating TL;DR infographic..."):
            try:
                response = client.models.generate_content(
                    model="gemini-3-pro-image-preview",
                    contents=f"Create a whiteboard summary infographic for the following: {st.session_state.synthesis_text}"
                )
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        st.session_state.infographic = part.inline_data.data
                        break
            except Exception as e: st.warning(f"Infographic error: {e}")
        st.rerun()

if st.session_state.synthesis_text:
    st.divider(); st.markdown("## 📊 Executive Report")
    
    # TL;DR Infographic at the top
    if st.session_state.infographic:
        st.markdown("### 🎨 TL;DR")
        st.image(st.session_state.infographic, use_container_width=True)
        st.divider()
    
    st.markdown(st.session_state.synthesis_text)
    st.download_button("📥 Download Report", st.session_state.synthesis_text, "research_report.md", "text/markdown")

st.divider(); st.caption("[Gemini Interactions API](https://ai.google.dev/gemini-api/docs/interactions)")