import asyncio
import os

import streamlit as st
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from mem0 import Memory

APP_NAME = "adk_career_coach"
MODEL = "gemini-3.7-flash"

# Mem0 config: Gemini for both the LLM (fact extraction) and the embedder,
# plus an on-disk Qdrant collection -- no Docker/Qdrant server, no OpenAI
# key. Both "llm" and "embedder" read GOOGLE_API_KEY from the environment
# once it's set below. Gemini's embedding model outputs 768-dim vectors, so
# embedder.embedding_dims and vector_store.embedding_model_dims must match.
MEM0_CONFIG = {
    "llm": {
        "provider": "gemini",
        "config": {"model": MODEL, "temperature": 0.2},
    },
    "embedder": {
        "provider": "gemini",
        "config": {"model": "models/gemini-embedding-001", "embedding_dims": 768},
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "adk_career_coach",
            "path": "./qdrant_storage",
            "embedding_model_dims": 768,
            "on_disk": True,
        },
    },
}

# --- Mock backend data the tools read from. Swap for real data sources later. ---
MOCK_INTERVIEW_QUESTIONS = {
    "amazon": {
        "behavioral": "Tell me about a time you had to disagree with a decision your manager made.",
        "system_design": "Design a URL shortener that can handle millions of requests per day.",
    },
    "google": {
        "behavioral": "Describe a project where the requirements changed halfway through.",
        "system_design": "Design a rate limiter for a public API.",
    },
}

MOCK_LEARNING_RESOURCES = {
    "distributed systems": {
        "resource": "Designing Data-Intensive Applications (Martin Kleppmann)",
        "next_step": "Start with the chapters on replication and partitioning, then practice explaining trade-offs out loud.",
    },
    "system design": {
        "resource": "ByteByteGo System Design Interview series",
        "next_step": "Work through one design problem per week and write out the trade-offs, not just the final diagram.",
    },
    "python": {
        "resource": "Fluent Python (Luciano Ramalho)",
        "next_step": "Focus on the chapters covering iterators, generators, and decorators.",
    },
}

MOCK_SALARY_DATA = {
    ("backend engineer", "seattle"): {"low": 140000, "high": 190000, "median": 165000},
    ("backend engineer", "remote"): {"low": 130000, "high": 175000, "median": 152000},
    ("senior backend engineer", "seattle"): {"low": 175000, "high": 230000, "median": 200000},
}

MOCK_RESUMES = {
    "demo@example.com": {
        "years_experience": 4,
        "current_role": "Backend Engineer",
        "skills": ["Python", "PostgreSQL", "REST APIs", "Docker"],
        "bullet_points": [
            "Worked on the payments team maintaining backend services.",
            "Helped onboard new engineers to the codebase.",
        ],
    },
}


def get_candidate_resume(candidate_email: str) -> dict:
    """Fetches the resume on file for a candidate (experience, current role, skills, bullet points)."""
    resume = MOCK_RESUMES.get(candidate_email.strip().lower())
    if resume:
        return {"status": "success", "candidate_email": candidate_email, "resume": resume}
    return {"status": "error", "message": f"No resume on file for {candidate_email}."}


def get_practice_question(company: str, interview_type: str) -> dict:
    """Returns a sample interview question for a given company and interview type (behavioral or system_design)."""
    company_key = company.strip().lower()
    type_key = interview_type.strip().lower().replace(" ", "_")
    question = MOCK_INTERVIEW_QUESTIONS.get(company_key, {}).get(type_key)
    if question:
        return {"status": "success", "company": company, "interview_type": interview_type, "question": question}
    return {"status": "error", "message": f"No sample questions on file for {company} ({interview_type})."}


def get_learning_resource(skill: str) -> dict:
    """Returns a suggested learning resource and next step for a given skill."""
    resource = MOCK_LEARNING_RESOURCES.get(skill.strip().lower())
    if resource:
        return {"status": "success", "skill": skill, **resource}
    return {"status": "error", "message": f"No learning resource on file for '{skill}'."}


def get_salary_benchmark(role: str, location: str) -> dict:
    """Returns a rough salary range for a given role and location."""
    data = MOCK_SALARY_DATA.get((role.strip().lower(), location.strip().lower()))
    if data:
        return {"status": "success", "role": role, "location": location, **data}
    return {"status": "error", "message": f"No salary data on file for {role} in {location}."}


def build_career_orchestrator() -> LlmAgent:
    """Root agent + 4 specialists. ADK routes to a sub-agent based on its description."""
    resume_agent = LlmAgent(
        name="resume_agent",
        model=MODEL,
        description="Reviews a candidate's resume and gives feedback tailored to a target role.",
        instruction=(
            "You help candidates improve their resume. Use the get_candidate_resume tool, "
            "passing the 'Candidate email' given in the message context, to fetch their resume "
            "on file. Then give specific, tailored suggestions based on their years of "
            "experience, current role, and skills versus the target role -- don't just restate "
            "the resume back to them. If the candidate also pastes a specific bullet point or "
            "section they're drafting, give feedback on that text directly, using the fetched "
            "resume as context for consistency and experience level."
        ),
        tools=[get_candidate_resume],
    )

    interview_agent = LlmAgent(
        name="interview_agent",
        model=MODEL,
        description="Runs mock interview practice and gives feedback for a specific company and interview type.",
        instruction=(
            "You help candidates prepare for interviews. Use the get_practice_question tool, "
            "passing the company and interview type (behavioral or system_design). If either "
            "isn't stated, use the target companies/weak areas noted in the candidate's "
            "profile info, or ask a quick clarifying question."
        ),
        tools=[get_practice_question],
    )

    skills_roadmap_agent = LlmAgent(
        name="skills_roadmap_agent",
        model=MODEL,
        description="Identifies skill gaps and suggests what to learn next.",
        instruction=(
            "You help candidates close skill gaps. Use the get_learning_resource tool for "
            "skills the candidate mentions, or for weak areas noted in their profile info if "
            "they ask something open-ended like 'what should I focus on'."
        ),
        tools=[get_learning_resource],
    )

    salary_agent = LlmAgent(
        name="salary_agent",
        model=MODEL,
        description="Gives salary benchmarks and negotiation advice for a role and location.",
        instruction=(
            "You help candidates understand their market value. Use the get_salary_benchmark "
            "tool, passing the role and location. If either isn't stated, use the target roles "
            "noted in the candidate's profile info instead of asking them to repeat it."
        ),
        tools=[get_salary_benchmark],
    )

    career_orchestrator = LlmAgent(
        name="career_orchestrator",
        model=MODEL,
        description="Routes career coaching questions to the right specialist.",
        instruction=(
            "You are the first point of contact for a career coaching app. Read the "
            "candidate's message, including any 'Relevant past information' block included "
            "with it, and decide whether this is about resume feedback, interview practice, "
            "a skill gap/learning roadmap, or salary/negotiation. Delegate to the matching "
            "specialist. If it's genuinely unclear, ask a clarifying question yourself "
            "instead of guessing."
        ),
        sub_agents=[resume_agent, interview_agent, skills_roadmap_agent, salary_agent],
    )
    return career_orchestrator


async def ensure_session(session_service, user_id, session_id):
    await session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)


async def call_agent(runner, user_id, session_id, message_text) -> str:
    content = types.Content(role="user", parts=[types.Part(text=message_text)])
    final_text = ""
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = event.content.parts[0].text
    return final_text


def run_agent_sync(runner, user_id, session_id, message_text) -> str:
    return asyncio.run(call_agent(runner, user_id, session_id, message_text))


@st.cache_resource
def get_memory() -> Memory:
    # Embedded/on-disk Qdrant only allows one open client per storage path
    # per process (it takes a file lock) -- cache_resource makes this a
    # single instance shared by every browser session on this server,
    # instead of one per session, which would crash the 2nd concurrent
    # user with "Storage folder ... already accessed by another instance".
    return Memory.from_config(MEM0_CONFIG)


@st.cache_resource
def get_runner():
    career_orchestrator = build_career_orchestrator()
    session_service = InMemorySessionService()
    runner = Runner(agent=career_orchestrator, app_name=APP_NAME, session_service=session_service)
    return runner, session_service


def format_memories(memories: dict) -> str:
    results = (memories or {}).get("results") or []
    if not results:
        return ""
    lines = "\n".join(f"- {m['memory']}" for m in results if "memory" in m)
    return f"Relevant past information:\n{lines}\n" if lines else ""


# --- Streamlit app ---
st.title("🎯 AI Career Coach (ADK Multi-Agent + Memory)")
st.caption(
    "An orchestrator agent routes your question to a resume, interview, skills, "
    "or salary specialist (Google ADK), while Mem0 + Qdrant remember your career "
    "history across sessions."
)

google_api_key = st.text_input(
    "Enter Google API Key (for Gemini)",
    type="password",
    value=os.getenv("GOOGLE_API_KEY", ""),
)

if google_api_key:
    os.environ["GOOGLE_API_KEY"] = google_api_key

    memory = get_memory()
    runner, session_service = get_runner()

    st.sidebar.title("Candidate")
    previous_user_id = st.session_state.get("previous_user_id")
    user_id = st.sidebar.text_input("Your email", value="demo@example.com")

    if user_id != previous_user_id:
        st.session_state.messages = []
        st.session_state.previous_user_id = user_id
        st.session_state.pop("session_ready", None)

    if st.sidebar.button("View my memory"):
        memories = memory.get_all(filters={"user_id": user_id})
        results = (memories or {}).get("results") or []
        if results:
            for mem in results:
                st.sidebar.write(f"- {mem['memory']}")
        else:
            st.sidebar.info("No memory on file for you yet.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask about your resume, an interview, a skill, or salary...")

    if prompt and user_id:
        session_id = f"session-{user_id}"
        if not st.session_state.get("session_ready"):
            asyncio.run(ensure_session(session_service, user_id, session_id))
            st.session_state.session_ready = True

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Long-term memory: pull what Mem0 knows about this candidate before routing.
        relevant_memories = memory.search(query=prompt, filters={"user_id": user_id}, top_k=5)
        context = format_memories(relevant_memories)
        full_message = f"Candidate email: {user_id}\n{context}\nCandidate says: {prompt}"

        with st.chat_message("assistant"):
            with st.spinner("Routing to the right specialist..."):
                answer = run_agent_sync(runner, user_id, session_id, full_message)
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

        # Write this exchange back to long-term memory for future sessions.
        # Only the candidate's own message goes in: one memory.add() call
        # instead of two (half the extraction latency/cost, since infer=True
        # runs an LLM call per add()), and the fact store stays candidate
        # facts only -- the coach's own advice text never gets treated as a
        # fact about the candidate.
        memory.add(prompt, user_id=user_id, metadata={"role": "user"})
    elif not user_id:
        st.error("Please enter your email to start chatting.")
else:
    st.warning("Please enter your Google API key to continue.")
