import streamlit as st
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import requests
from typing import List, Dict

st.set_page_config(page_title="AI Productivity & Focus Agent", layout="wide")

# Session state defaults

if "tasks" not in st.session_state:
    st.session_state.tasks: List[Dict] = []  # each: {id, name, category, deadline, status}
if "logs" not in st.session_state:
    st.session_state.logs: List[Dict] = []   # each: {task_id, start_time_iso, end_time_iso}
if "next_task_id" not in st.session_state:
    st.session_state.next_task_id = 1
if "active_timer" not in st.session_state:
    st.session_state.active_timer = None    # {task_id:int, start_time: datetime}

# Ollama helper
def query_ollama(prompt: str, model: str = "llama3") -> str:
    """
    Calls a local Ollama instance with the actual prompt.
    """
    url = "http://localhost:11434/api/generate"
    payload = {"model": model, "prompt": prompt, "max_length": 512, "stream": False}
    try:
        r = requests.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        # Common possible response shapes:
        for key in ("response", "output", "text"):
            if key in data and isinstance(data[key], str):
                return data[key].strip()
        if "results" in data and isinstance(data["results"], list):
            pieces = []
            for item in data["results"]:
                if isinstance(item, dict):
                    for candidate in ("content", "text", "output"):
                        if candidate in item and isinstance(item[candidate], str):
                            pieces.append(item[candidate].strip())
                elif isinstance(item, str):
                    pieces.append(item.strip())
            if pieces:
                return "\n".join(pieces)
        # fallback: stringify
        return str(data)
    except Exception as e:
        return f"⚠️ Ollama call failed: {e}"

# UI layout
st.title("🧠 AI Productivity & Focus Agent")
col1, col2 = st.columns([2, 1])

with col1:
    menu = st.radio("Menu", ["Add Task", "My Tasks", "Focus Timer", "Insights & AI Suggestions"])

    if menu == "Add Task":
        st.subheader("Add a new task")
        task_name = st.text_input("Task name")
        category = st.selectbox("Category", ["Work", "Study", "Personal", "Other"])
        deadline = st.date_input("Deadline", datetime.date.today())
        if st.button("Add Task"):
            t = {
                "id": st.session_state.next_task_id,
                "name": task_name.strip(),
                "category": category,
                "deadline": str(deadline),
                "status": "pending"
            }
            st.session_state.tasks.append(t)
            st.session_state.next_task_id += 1
            st.success(f"Task added: {t['name']} (id={t['id']})")

    elif menu == "My Tasks":
        st.subheader("Pending tasks")
        pending = [t for t in st.session_state.tasks if t["status"] == "pending"]
        if not pending:
            st.info("No pending tasks. Add one in 'Add Task'.")
        else:
            for t in pending:
                cols = st.columns([6, 2, 2])
                cols[0].write(f"**{t['name']}** — {t['category']} (due {t['deadline']}) — id: {t['id']}")
                if cols[1].button(f"Mark Done {t['id']}", key=f"done_{t['id']}"):
                    t["status"] = "done"
                    st.success(f"Marked done: {t['name']}")
                if cols[2].button(f"Delete {t['id']}", key=f"del_{t['id']}"):
                    st.session_state.tasks = [x for x in st.session_state.tasks if x["id"] != t["id"]]
                    st.success(f"Deleted task id {t['id']}")
            st.markdown("---")
            st.subheader("All tasks (debug)")
            st.write(pd.DataFrame(st.session_state.tasks))

    elif menu == "Focus Timer":
        st.subheader("Focus Timer")
        pending = [t for t in st.session_state.tasks if t["status"] == "pending"]
        if not pending:
            st.info("No pending tasks. Add some first.")
        else:
            selection = st.selectbox("Choose task to focus on", [f"{t['id']}: {t['name']}" for t in pending])
            selected_id = int(selection.split(":")[0])
            if st.session_state.active_timer is None:
                if st.button("Start Focus Session"):
                    st.session_state.active_timer = {"task_id": selected_id, "start_time": datetime.datetime.now()}
                    st.success("Focus started ⏳")
            else:
                at = st.session_state.active_timer
                if st.button("End Session"):
                    start = at["start_time"]
                    end = datetime.datetime.now()
                    st.session_state.logs.append({
                        "task_id": at["task_id"],
                        "start_time_iso": start.isoformat(),
                        "end_time_iso": end.isoformat()
                    })
                    st.session_state.active_timer = None
                    st.success("Session logged ✅")
                else:
                    # show elapsed
                    now = datetime.datetime.now()
                    elapsed = now - at["start_time"]
                    mins = int(elapsed.total_seconds() // 60)
                    secs = int(elapsed.total_seconds() % 60)
                    st.info(f"Active task id {at['task_id']} — elapsed: {mins}m {secs}s")

    elif menu == "Insights & AI Suggestions":
        st.subheader("Insights from your sessions")
        if not st.session_state.logs:
            st.info("No focus sessions logged yet. Complete a session in 'Focus Timer'.")
        else:
            # Build dataframe
            df = pd.DataFrame(st.session_state.logs)
            df["start_time"] = pd.to_datetime(df["start_time_iso"])
            df["end_time"] = pd.to_datetime(df["end_time_iso"])
            df["duration_mins"] = (df["end_time"] - df["start_time"]).dt.total_seconds() / 60.0

            # Map task names
            id_to_name = {t["id"]: t["name"] for t in st.session_state.tasks}
            df["task_name"] = df["task_id"].map(id_to_name)

            # Show table
            st.dataframe(df[["task_id", "task_name", "start_time", "end_time", "duration_mins"]])

            # Plot (matplotlib, single plot)
            fig, ax = plt.subplots()
            summary = df.groupby("task_name")["duration_mins"].sum()
            summary.plot(kind="bar", ax=ax)
            ax.set_ylabel("Total minutes")
            ax.set_title("Time spent per task")
            st.pyplot(fig)

            # Prepare prompt for Ollama
            prompt_summary = summary.to_dict()
            prompt = (
                "You are a productivity coach. The user worked with the following time logs (minutes per task):\n"
                f"{prompt_summary}\n\n"
                "Please provide:\n"
                "1) A concise reflection (2-3 sentences) about the user's productivity.\n"
                "2) 3 practical suggestions to improve focus tomorrow, with one suggestion actionable in <30 minutes.\n"
                "3) A 1-day time-blocked plan (hours) assuming 4 focus blocks available.\n"
            )

            st.markdown("**Ollama's suggestions:**")
            ai_resp = query_ollama(prompt)
            st.write(ai_resp)

            # custom question to AI
            st.markdown("---")
            st.subheader("Ask the AI a custom productivity question")
            custom_q = st.text_input("Your question for the productivity coach (Ollama):")
            if st.button("Ask AI"):
                if custom_q.strip():
                    st.write(query_ollama(custom_q.strip()))
                else:
                    st.warning("Enter a question first.")

with col2:
    st.sidebar.title("Quick controls")
    if st.button("Reset all (clear tasks & logs)"):
        st.session_state.tasks = []
        st.session_state.logs = []
        st.session_state.next_task_id = 1
        st.session_state.active_timer = None
        st.success("Reset done.")
    st.sidebar.markdown("---")
    st.sidebar.write("Status:")
    st.sidebar.write(f"Tasks: {len(st.session_state.tasks)}")
    st.sidebar.write(f"Logs: {len(st.session_state.logs)}")
    if st.session_state.active_timer:
        at = st.session_state.active_timer
        st.sidebar.write(f"Active session: task id {at['task_id']} since {at['start_time'].strftime('%H:%M:%S')}")
    else:
        st.sidebar.write("No active session")

st.markdown("---")
st.caption("Requires Ollama running locally at http://localhost:11434 (model name: e.g., 'llama3').")
