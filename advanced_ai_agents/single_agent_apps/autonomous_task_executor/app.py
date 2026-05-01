"""
Streamlit frontend for the Autonomous Task Executor.

Wraps the task_executor pipeline stages (plan → review → execute → verify)
with a visual UI showing progress, per-step results, and verdict display.
"""
from __future__ import annotations

import json
import os
import sqlite3
import uuid

import streamlit as st

import task_executor as te

# ─── Page Config ────────────────────────────────────────────────────────────

st.set_page_config(page_title="Autonomous Task Executor", page_icon="🔍", layout="wide")
st.title("Autonomous Task Executor")
st.caption("Break any task into steps, execute with tools, then adversarially verify the outcome.")

# ─── Sidebar ────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=os.environ.get("OPENAI_API_KEY", ""),
        help="Required. Supports any OpenAI-compatible provider via Base URL.",
    )
    base_url = st.text_input(
        "Base URL (optional)",
        value=os.environ.get("OPENAI_BASE_URL", ""),
        help="For alternate providers (e.g. Ollama, Together, DeepInfra).",
    )
    model = st.selectbox(
        "Model",
        ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1-nano"],
        index=0,
        help="Any model supported by your provider.",
    )
    threshold = st.slider(
        "Confidence threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.75,
        step=0.05,
        help="Minimum verifier confidence to accept a result.",
    )

# ─── Tabs ───────────────────────────────────────────────────────────────────

tab_run, tab_history = st.tabs(["Run Task", "History"])

# ─── Database ───────────────────────────────────────────────────────────────

te.DATA_DIR.mkdir(parents=True, exist_ok=True)


@st.cache_resource
def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(te.DB_PATH), check_same_thread=False)
    te.init_db(conn)
    return conn


conn = get_db()

# ─── Run Tab ────────────────────────────────────────────────────────────────

with tab_run:
    task_desc = st.text_area(
        "Describe your task",
        placeholder="Research the top 3 Python async frameworks and write a comparison to /tmp/async_compare.md",
        height=100,
    )

    if st.button("Run Task", type="primary", disabled=not api_key):
        if not api_key:
            st.error("Enter an OpenAI API key in the sidebar.")
            st.stop()
        if not task_desc.strip():
            st.warning("Enter a task description.")
            st.stop()

        # Configure the executor module
        te.MODEL = model
        te.THRESHOLD = threshold
        os.environ["OPENAI_API_KEY"] = api_key
        if base_url:
            os.environ["OPENAI_BASE_URL"] = base_url
        else:
            os.environ.pop("OPENAI_BASE_URL", None)

        client = te.get_client()
        task_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)",
            (task_id, task_desc, "planning", None, None, None, None, te.now(), None),
        )
        conn.commit()

        # ── Stage 1: Plan ──
        with st.status("Generating plan...", expanded=True) as status:
            try:
                plan = te.generate_plan(client, task_desc)
            except Exception as e:
                st.error(f"Plan generation failed: {e}")
                conn.execute(
                    "UPDATE tasks SET status='failed',finished_at=? WHERE id=?",
                    (te.now(), task_id),
                )
                conn.commit()
                st.stop()

            conn.execute(
                "UPDATE tasks SET plan_json=? WHERE id=?",
                (json.dumps(plan), task_id),
            )
            conn.commit()
            status.update(label="Plan generated", state="complete")

        st.markdown(f"**Goal:** {plan.get('goal', '')}")
        for s in plan.get("steps", []):
            st.markdown(f"- `[{s['type']}]` {s['description']}")

        # ── Stage 2: Review Gate ──
        with st.status("Reviewing plan...", expanded=True) as status:
            review = te.review_plan(client, task_desc, plan)
            approved = review.get("approved", False)
            conf = review.get("confidence", 0)

            if approved:
                status.update(label=f"Plan approved ({conf:.0%})", state="complete")
            else:
                status.update(label=f"Plan rejected ({conf:.0%})", state="error")

        if not approved:
            raw_issues = review.get("issues", ["Plan not approved"])
            reason = "; ".join(
                i.get("issue", str(i)) if isinstance(i, dict) else str(i)
                for i in raw_issues
            )
            st.error(f"Plan rejected: {reason}")
            conn.execute(
                "UPDATE tasks SET status='rejected',verdict='rejected',"
                "reason=?,finished_at=? WHERE id=?",
                (reason, te.now(), task_id),
            )
            conn.commit()
            st.stop()

        for issue in review.get("issues", []):
            st.warning(f"Reviewer note: {issue}")

        if review.get("revised_steps"):
            plan["steps"] = review["revised_steps"]
            st.info("Plan revised by reviewer.")

        # ── Stage 3: Execute Steps ──
        conn.execute("UPDATE tasks SET status='executing' WHERE id=?", (task_id,))
        conn.commit()
        steps = plan.get("steps", [])
        results = []
        ctx_parts: list[str] = []

        for step in steps:
            sid = str(uuid.uuid4())
            step_label = f"Step {step['index']+1}/{len(steps)}: {step['description']}"
            with st.status(step_label, expanded=True) as status:
                conn.execute(
                    "INSERT INTO steps VALUES (?,?,?,?,?,?,?,?,?)",
                    (sid, task_id, step["index"], step["type"],
                     step["description"], None, "running", te.now(), None),
                )
                conn.commit()

                result = te.execute_step(client, conn, step, sid, "\n".join(ctx_parts))
                st.text(result[:2000])

                results.append({
                    "index": step["index"],
                    "description": step["description"],
                    "success_criterion": step.get("success_criterion", ""),
                    "result": result,
                })
                ctx_parts.append(f"Step {step['index']+1}: {result[:800]}")

                conn.execute(
                    "UPDATE steps SET result=?,status='done',finished_at=? WHERE id=?",
                    (result[:4000], te.now(), sid),
                )
                conn.commit()
                status.update(label=step_label, state="complete")

        # ── Stage 4: Adversarial Verification ──
        with st.status("Running adversarial verification...", expanded=True) as status:
            try:
                vdata = te.verify_outcome(client, task_desc, plan, results)
            except Exception as e:
                vdata = {
                    "verdict": "reject",
                    "confidence": 0.0,
                    "overall_reason": f"Verification error: {e}",
                }

            verdict = vdata.get("verdict", "reject")
            confidence = float(vdata.get("confidence", 0))
            reason = vdata.get("overall_reason", "")

            if verdict == "accept" and confidence < threshold:
                verdict = "reject"
                reason = f"Confidence {confidence:.0%} below {threshold:.0%}. " + reason

            if verdict == "accept":
                status.update(label=f"Accepted ({confidence:.0%})", state="complete")
            else:
                status.update(label=f"Rejected ({confidence:.0%})", state="error")

        # ── Verdict Display ──
        if verdict == "accept":
            st.success(f"**ACCEPTED** — Confidence: {confidence:.0%}")
        else:
            st.error(f"**REJECTED** — Confidence: {confidence:.0%}")

        st.markdown(f"**Reason:** {reason}")

        step_verdicts = vdata.get("step_verdicts", [])
        if step_verdicts:
            for sv in step_verdicts:
                icon = "✅" if sv.get("passed") else "❌"
                st.markdown(f"{icon} Step {sv['index']+1}: {sv.get('note', '')}")

        conn.execute(
            "UPDATE tasks SET status=?,verdict=?,confidence=?,reason=?,finished_at=? WHERE id=?",
            (verdict, verdict, confidence, reason, te.now(), task_id),
        )
        conn.commit()
        st.caption(f"Task ID: `{task_id}`")

# ─── History Tab ────────────────────────────────────────────────────────────

with tab_history:
    rows = conn.execute(
        "SELECT id, status, verdict, confidence, created_at, description "
        "FROM tasks ORDER BY created_at DESC LIMIT 20"
    ).fetchall()

    if not rows:
        st.info("No tasks yet. Run one from the **Run Task** tab.")
    else:
        for row in rows:
            tid, status, verdict, conf, created, desc = row
            icon = "✅" if verdict == "accept" else ("❌" if verdict == "reject" else "⏳")
            conf_str = f"{conf:.0%}" if conf is not None else "—"
            with st.expander(f"{icon} {desc[:80]} — {conf_str}", expanded=False):
                st.markdown(f"**ID:** `{tid}`")
                st.markdown(f"**Status:** {status} | **Verdict:** {verdict or '—'} | **Confidence:** {conf_str}")
                st.markdown(f"**Created:** {created}")

                task_steps = conn.execute(
                    "SELECT step_index, step_type, description, status, result "
                    "FROM steps WHERE task_id=? ORDER BY step_index",
                    (tid,),
                ).fetchall()
                if task_steps:
                    for s in task_steps:
                        st.markdown(f"- **Step {s[0]+1}** `[{s[1]}]` {s[2]} — _{s[3]}_")
