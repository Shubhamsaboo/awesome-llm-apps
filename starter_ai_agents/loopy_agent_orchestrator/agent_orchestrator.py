"""
Loopy Agent Orchestrator — demonstrates multi-agent orchestration with a kanban-style workflow.
Uses two specialized agents (Researcher + Builder) coordinated by a Supervisor.
"""

import streamlit as st
from openai import OpenAI
import json

st.set_page_config(
    page_title="Loopy Agent Orchestrator",
    page_icon="🔄",
    layout="wide",
)

st.markdown(
    """
<style>
.stApp { background: #0a0a0a; color: #f5f5f5; }
.stTextInput>div>div>input { background: #1a1a1a !important; color: #f5f5f5 !important; border: 1px solid #333 !important; }
.stTextArea>div>div>textarea { background: #1a1a1a !important; color: #f5f5f5 !important; border: 1px solid #333 !important; }
h1, h2, h3 { color: #2563eb !important; font-weight: 600 !important; }
.block-container { max-width: 1000px; padding-top: 2rem; }
.stMarkdown { color: #d1d5db; }
.stButton>button { background: #2563eb !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 500 !important; }
.stButton>button:hover { background: #1d4ed8 !important; }
.css-1y4p8pa { padding-top: 1rem; }
.agent-card { background: #1a1a1a; border: 1px solid #333; border-radius: 12px; padding: 16px; margin: 8px 0; }
.agent-card h4 { color: #93c5fd; margin: 0 0 8px 0; }
.supervisor-card { background: #1a1a2e; border: 1px solid #2563eb; border-radius: 12px; padding: 16px; margin: 8px 0; }
.supervisor-card h4 { color: #60a5fa; margin: 0 0 8px 0; }
.metric { font-size: 28px; font-weight: 700; color: #2563eb; }
.metric-label { font-size: 13px; color: #9ca3af; }
</style>
""",
    unsafe_allow_html=True,
)

st.title("🔄 Loopy Agent Orchestrator")
st.markdown(
    "A kanban-based multi-agent system where a **Supervisor** delegates tasks to specialized agents, "
    "each working in parallel. This demo orchestrates a **Researcher** and a **Builder** to go "
    "from idea → research → plan → code."
)

# === SIDEBAR CONFIG ===
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Get your key at https://platform.openai.com/api-keys",
    )
    model = st.selectbox(
        "Model", ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"], index=0
    )
    st.markdown("---")
    st.markdown(
        "### 🔄 How it works\n\n"
        "1. **Supervisor** receives your idea\n"
        "2. **Researcher** gathers context and best practices\n"
        "3. **Builder** generates the implementation\n"
        "4. **Supervisor** reviews and delivers the result\n\n"
        "All agents share context through a structured handoff — "
        "no lost context, no duplicated work."
    )
    st.markdown(
        "---\n📖 [Loopy GitHub](https://github.com/arjunkshah/loopy) • "
        "[Docs](https://loopy.yachts)"
    )

# === AGENT FUNCTIONS ===


def researcher_agent(client, model, idea):
    """First agent: researches the idea and gathers context."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior technical researcher. Given a product idea, "
                    "analyze it and deliver:\n"
                    "1. **Market context** — what exists, what's missing\n"
                    "2. **Technical approach** — recommended stack and architecture\n"
                    "3. **Key considerations** — edge cases, scaling, security\n"
                    "Keep it concise and actionable (3-5 sentences per section)."
                ),
            },
            {"role": "user", "content": f"Research this idea: {idea}"},
        ],
        temperature=0.4,
    )
    return response.choices[0].message.content


def builder_agent(client, model, idea, research):
    """Second agent: generates an implementation plan based on research."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior software architect. Based on the idea and research, "
                    "produce a concrete implementation plan:\n"
                    "1. **Architecture** — components and data flow\n"
                    "2. **Implementation steps** — ordered, with file structure\n"
                    "3. **Key code snippets** — the critical 20% that does 80% of the work\n"
                    "Be specific and actionable. Prioritize getting to a working prototype."
                ),
            },
            {
                "role": "user",
                "content": f"Idea: {idea}\n\nResearch:\n{research}",
            },
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


def supervisor_agent(client, model, idea, research, plan):
    """Supervisor: reviews and synthesizes the final output."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a technical lead reviewing a project handoff. "
                    "Synthesize the research and plan into a clear, confident "
                    "executive summary. Include:\n"
                    "1. **One-line pitch**\n"
                    "2. **Feasibility assessment** (green/yellow/red)\n"
                    "3. **Critical path** — the first 3 things to build\n"
                    "4. **Estimated effort** — in engineering days\n"
                    "Be direct. No fluff."
                ),
            },
            {
                "role": "user",
                "content": f"Idea: {idea}\n\nResearch:\n{research}\n\nPlan:\n{plan}",
            },
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


# === MAIN APP ===

idea = st.text_area(
    "💡 Describe your idea",
    placeholder="e.g., A CLI tool that syncs GitHub issues to a local markdown journal",
    height=100,
)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    run_btn = st.button("🔄 Run Agent Orchestrator", use_container_width=True)

if run_btn:
    if not api_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
        st.stop()
    if not idea.strip():
        st.error("Please describe an idea.")
        st.stop()

    client = OpenAI(api_key=api_key)

    # Phase 1: Supervisor accepts the task
    with st.status("🔄 Orchestrating agents...", expanded=True) as status:
        st.markdown(
            '<div class="supervisor-card"><h4>🧠 Supervisor</h4>'
            "<p>Received idea. Routing to Researcher...</p></div>",
            unsafe_allow_html=True,
        )

        # Phase 2: Researcher works
        status.update(label="🔍 Researcher is investigating...")
        research = researcher_agent(client, model, idea)
        st.markdown(
            f'<div class="agent-card"><h4>🔍 Researcher — Context & Analysis</h4>'
            f"<p>{research}</p></div>",
            unsafe_allow_html=True,
        )

        # Phase 3: Builder works
        status.update(label="🏗️ Builder is generating implementation...")
        plan = builder_agent(client, model, idea, research)
        st.markdown(
            f'<div class="agent-card"><h4>🏗️ Builder — Implementation Plan</h4>'
            f"<p>{plan}</p></div>",
            unsafe_allow_html=True,
        )

        # Phase 4: Supervisor reviews
        status.update(label="🧠 Supervisor is reviewing...")
        summary = supervisor_agent(client, model, idea, research, plan)
        st.markdown(
            f'<div class="supervisor-card"><h4>🧠 Supervisor — Final Review</h4>'
            f"<p>{summary}</p></div>",
            unsafe_allow_html=True,
        )

        status.update(
            label="✅ Orchestration complete!",
            state="complete",
        )

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            '<div style="text-align:center"><div class="metric">3</div>'
            '<div class="metric-label">Agents Orchestrated</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            '<div style="text-align:center"><div class="metric">4</div>'
            '<div class="metric-label">Phases Completed</div></div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            '<div style="text-align:center"><div class="metric">~30s</div>'
            '<div class="metric-label">Typical Runtime</div></div>',
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            '<div style="text-align:center"><div class="metric">1</div>'
            '<div class="metric-label">Kanban Board</div></div>',
            unsafe_allow_html=True,
        )

else:
    st.info(
        "👆 Enter your idea above and click **Run Agent Orchestrator** to see Loopy in action.\n\n"
        "The system will:\n"
        "1. **Research** — analyze market context and technical approach\n"
        "2. **Build** — generate architecture and implementation plan\n"
        "3. **Review** — synthesize with feasibility assessment"
    )
