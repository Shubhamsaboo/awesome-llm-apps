"""
Multi-Agent Task Orchestrator with Anti-Duplication

A Streamlit app that routes tasks to specialized AI agents,
prevents duplicate work with SQLite tracking, and verifies
results through quality gates before marking tasks done.

Supports: OpenAI (GPT-4o), Anthropic (Claude), or Demo mode.
"""

import streamlit as st
import sqlite3
import json
import hashlib
import os
from datetime import datetime
from difflib import SequenceMatcher

# --- Database Setup ---

DB_PATH = "task_registry.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            agent TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            result TEXT,
            hash TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def task_hash(description: str) -> str:
    normalized = description.lower().strip()
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def check_duplicate(description: str, threshold: float = 0.55) -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Exact hash match
    h = task_hash(description)
    c.execute("SELECT id, description, agent, status FROM tasks WHERE hash = ?", (h,))
    exact = c.fetchone()
    if exact:
        conn.close()
        return {"type": "exact", "id": exact[0], "description": exact[1],
                "agent": exact[2], "status": exact[3]}

    # Fuzzy similarity match
    c.execute("SELECT id, description, agent, status FROM tasks WHERE status != 'failed'")
    for row in c.fetchall():
        ratio = SequenceMatcher(None, description.lower(), row[1].lower()).ratio()
        if ratio >= threshold:
            conn.close()
            return {"type": "similar", "id": row[0], "description": row[1],
                    "agent": row[2], "status": row[3], "similarity": f"{ratio:.0%}"}

    conn.close()
    return None


def claim_task(description: str, agent: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO tasks (description, agent, status, hash) VALUES (?, ?, 'in_progress', ?)",
        (description, agent, task_hash(description))
    )
    task_id = c.lastrowid
    conn.commit()
    conn.close()
    return task_id


def complete_task(task_id: int, result: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "UPDATE tasks SET status = 'done', result = ?, completed_at = ? WHERE id = ?",
        (result, datetime.now().isoformat(), task_id)
    )
    conn.commit()
    conn.close()


def get_all_tasks() -> list:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, description, agent, status, created_at FROM tasks ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows


# --- Agent Routing ---

AGENTS = {
    "code-architect": {
        "keywords": ["code", "implement", "function", "class", "bug", "fix", "refactor", "api", "endpoint"],
        "system": "You are a senior software architect. Write clean, tested, production-ready code. Include error handling and type hints.",
    },
    "security-reviewer": {
        "keywords": ["security", "vulnerability", "audit", "cve", "xss", "injection", "auth", "token", "password"],
        "system": "You are a security specialist. Identify vulnerabilities, suggest fixes with code examples, and reference relevant CWE/CVE IDs.",
    },
    "researcher": {
        "keywords": ["research", "compare", "analyze", "benchmark", "evaluate", "best", "alternative", "difference"],
        "system": "You are a technical researcher. Provide structured comparisons with pros/cons tables, cite sources, and give clear recommendations.",
    },
    "doc-writer": {
        "keywords": ["document", "readme", "explain", "tutorial", "guide", "comment", "docstring", "wiki"],
        "system": "You are a technical writer. Create clear, well-structured documentation with examples, diagrams (Mermaid), and step-by-step instructions.",
    },
    "test-engineer": {
        "keywords": ["test", "coverage", "unittest", "pytest", "spec", "assertion", "mock", "fixture", "ci"],
        "system": "You are a test engineer. Write comprehensive test suites with edge cases, use pytest conventions, and aim for >90% coverage.",
    },
}


def route_task(description: str) -> str:
    desc_lower = description.lower()
    scores = {}
    for agent_name, config in AGENTS.items():
        score = sum(1 for kw in config["keywords"] if kw in desc_lower)
        scores[agent_name] = score

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "code-architect"  # default
    return best


# --- LLM Integration ---

def call_llm(system_prompt: str, user_prompt: str, provider: str) -> str:
    if provider == "demo":
        return f"[Demo Mode] Agent would process: {user_prompt[:100]}...\n\nThis is a simulated response. Connect an API key for real results."

    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", st.session_state.get("openai_key", "")))
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=2000,
        )
        return response.choices[0].message.content

    if provider == "anthropic":
        from anthropic import Anthropic
        client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", st.session_state.get("anthropic_key", "")))
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text

    return "Unknown provider"


# --- Quality Gate ---

def quality_check(task_description: str, result: str) -> dict:
    checks = {
        "non_empty": len(result.strip()) > 20,
        "addresses_task": any(
            word in result.lower()
            for word in task_description.lower().split()[:5]
        ),
        "has_structure": any(marker in result for marker in ["```", "- ", "1.", "##", "|"]),
        "no_refusal": not any(
            phrase in result.lower()
            for phrase in ["i cannot", "i'm unable", "as an ai"]
        ),
    }
    passed = sum(checks.values())
    total = len(checks)
    verdict = "VERIFIED" if passed == total else "INCOMPLETE" if passed >= 2 else "FAILED"
    return {"checks": checks, "passed": passed, "total": total, "verdict": verdict}


# --- Streamlit UI ---

def main():
    st.set_page_config(page_title="Multi-Agent Task Orchestrator", layout="wide")
    st.title("Multi-Agent Task Orchestrator")
    st.caption("Route tasks to specialized agents with anti-duplication and quality gates")

    init_db()

    # Sidebar: provider config
    with st.sidebar:
        st.header("Configuration")
        provider = st.selectbox("LLM Provider", ["demo", "openai", "anthropic"])

        if provider == "openai":
            st.session_state["openai_key"] = st.text_input("OpenAI API Key", type="password")
        elif provider == "anthropic":
            st.session_state["anthropic_key"] = st.text_input("Anthropic API Key", type="password")

        st.divider()
        st.subheader("Available Agents")
        for name, config in AGENTS.items():
            with st.expander(name):
                st.write(f"**Keywords:** {', '.join(config['keywords'])}")

    # Main area: task input
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("New Task")
        task_desc = st.text_area("Describe your task:", height=100,
                                  placeholder="e.g., Write a rate limiter middleware for Express.js")

        if st.button("Submit Task", type="primary", disabled=not task_desc):
            # Step 1: Anti-duplication check
            duplicate = check_duplicate(task_desc)
            if duplicate:
                st.warning(
                    f"Duplicate detected ({duplicate['type']}): "
                    f"Task #{duplicate['id']} - {duplicate['description'][:60]}... "
                    f"(status: {duplicate['status']})"
                )
            else:
                # Step 2: Route to agent
                agent = route_task(task_desc)
                st.info(f"Routed to **{agent}**")

                # Step 3: Claim in registry
                task_id = claim_task(task_desc, agent)
                st.success(f"Task #{task_id} claimed by {agent}")

                # Step 4: Execute
                with st.spinner(f"Agent '{agent}' working..."):
                    system = AGENTS[agent]["system"]
                    result = call_llm(system, task_desc, provider)

                # Step 5: Quality gate
                qg = quality_check(task_desc, result)
                if qg["verdict"] == "VERIFIED":
                    complete_task(task_id, result)
                    st.success(f"Quality Gate: {qg['verdict']} ({qg['passed']}/{qg['total']} checks)")
                else:
                    st.warning(f"Quality Gate: {qg['verdict']} ({qg['passed']}/{qg['total']} checks)")

                # Show result
                st.subheader("Result")
                st.markdown(result)

                # Show quality details
                with st.expander("Quality Gate Details"):
                    for check, passed in qg["checks"].items():
                        icon = "check" if passed else "x"
                        st.write(f":{icon}: **{check.replace('_', ' ').title()}**")

    with col2:
        st.subheader("Task Registry")
        tasks = get_all_tasks()
        if tasks:
            for t in tasks[:10]:
                status_icon = {"done": "white_check_mark", "in_progress": "hourglass_flowing_sand",
                               "pending": "inbox_tray", "failed": "x"}.get(t[3], "question")
                st.write(f":{status_icon}: **#{t[0]}** {t[1][:40]}...")
                st.caption(f"{t[2]} | {t[3]} | {t[4]}")
        else:
            st.info("No tasks yet. Submit one above!")


if __name__ == "__main__":
    main()
