#!/usr/bin/env python3
"""
Autonomous Task Executor
========================
Breaks a task into steps, executes each with an LLM agent (file I/O + web
fetch only, no subprocess), then adversarially verifies the outcome.

Pipeline: intake → plan → review gate → execute steps → verify → accept/reject
All tasks, steps, and tool calls are logged to SQLite (~/.task_executor/).

Usage:
    python task_executor.py "Research top 3 Python async frameworks, write
                            comparison to /tmp/async_compare.md"
    python task_executor.py --list-tasks
    python task_executor.py --task-id <prefix>

Requirements:  pip install openai rich httpx
"""
from __future__ import annotations

import argparse, datetime, json, os, sqlite3, sys, uuid
from pathlib import Path
from typing import Any

import httpx
from openai import OpenAI

try:
    from rich.console import Console
    from rich.table import Table
    console = Console()
    HAS_RICH = True
except ImportError:
    console = None  # type: ignore
    HAS_RICH = False

# ─── Config ──────────────────────────────────────────────────────────────────

DATA_DIR   = Path.home() / ".task_executor"
DB_PATH    = DATA_DIR / "tasks.db"
MODEL      = os.environ.get("TASK_EXECUTOR_MODEL", "gpt-4o-mini")
THRESHOLD  = 0.75    # min verifier confidence to accept
MAX_STEPS  = 12
MAX_FETCH  = 50_000  # bytes

# ─── Database ────────────────────────────────────────────────────────────────

DDL = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY, description TEXT NOT NULL, status TEXT NOT NULL,
    plan_json TEXT, verdict TEXT, confidence REAL, reason TEXT,
    created_at TEXT NOT NULL, finished_at TEXT
);
CREATE TABLE IF NOT EXISTS steps (
    id TEXT PRIMARY KEY, task_id TEXT NOT NULL, step_index INTEGER NOT NULL,
    step_type TEXT NOT NULL, description TEXT NOT NULL,
    result TEXT, status TEXT NOT NULL, started_at TEXT, finished_at TEXT
);
CREATE TABLE IF NOT EXISTS tool_calls (
    id TEXT PRIMARY KEY, step_id TEXT NOT NULL, tool_name TEXT NOT NULL,
    args_json TEXT NOT NULL, result_text TEXT, called_at TEXT NOT NULL
);"""

def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(DDL); conn.commit()

def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

# ─── LLM ─────────────────────────────────────────────────────────────────────

def get_client() -> OpenAI:
    base_url = os.environ.get("OPENAI_BASE_URL")
    # Support alternate providers via OPENAI_BASE_URL + OPENAI_API_KEY override
    key = os.environ.get("OPENAI_API_KEY")
    if not key: sys.exit("ERROR: OPENAI_API_KEY not set")
    return OpenAI(api_key=key, base_url=base_url) if base_url else OpenAI(api_key=key)

def chat(client: OpenAI, messages: list[dict], json_mode: bool = False) -> str:
    kw: dict[str, Any] = {"model": MODEL, "messages": messages}
    if json_mode: kw["response_format"] = {"type": "json_object"}
    return client.chat.completions.create(**kw).choices[0].message.content or ""

# ─── Tools ───────────────────────────────────────────────────────────────────

def tool_read_file(path: str) -> str:
    p = Path(path).expanduser()
    try: return p.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError: return f"ERROR: not found: {path}"
    except PermissionError:   return f"ERROR: permission denied: {path}"

def tool_write_file(path: str, content: str) -> str:
    p = Path(path).expanduser()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"OK: wrote {len(content)} chars to {path}"
    except PermissionError: return f"ERROR: permission denied: {path}"

def tool_fetch_url(url: str) -> str:
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as h:
            r = h.get(url, headers={"User-Agent": "task-executor/1.0"})
            r.raise_for_status()
            text = r.text[:MAX_FETCH]
            return text + ("\n[TRUNCATED]" if len(r.text) > MAX_FETCH else "")
    except httpx.HTTPStatusError as e: return f"ERROR: HTTP {e.response.status_code}"
    except Exception as e:             return f"ERROR: {e}"

TOOLS = [
    {"type": "function", "function": {
        "name": "read_file", "description": "Read a local file.",
        "parameters": {"type": "object", "required": ["path"],
            "properties": {"path": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "write_file", "description": "Write or overwrite a local file.",
        "parameters": {"type": "object", "required": ["path", "content"],
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "fetch_url", "description": "HTTP GET, returns text (max 50 KB).",
        "parameters": {"type": "object", "required": ["url"],
            "properties": {"url": {"type": "string"}}}}},
]

def dispatch(name: str, args: dict) -> str:
    if name == "read_file":   return tool_read_file(args["path"])
    if name == "write_file":  return tool_write_file(args["path"], args["content"])
    if name == "fetch_url":   return tool_fetch_url(args["url"])
    return f"ERROR: unknown tool '{name}'"

# ─── UI ──────────────────────────────────────────────────────────────────────

def pr(msg: str, style: str = "") -> None:
    (console.print(msg, style=style) if HAS_RICH else print(msg))  # type: ignore

def section(title: str) -> None:
    (console.rule(f"[bold]{title}") if HAS_RICH else print(f"\n{'─'*60}\n  {title}\n{'─'*60}"))  # type: ignore

# ─── Plan Generation ─────────────────────────────────────────────────────────

PLAN_SYS = f"""You are a task planner. Return ONLY valid JSON:
{{"goal":"<success restatement>","steps":[{{"index":0,"type":"research|write|read|fetch|synthesize|verify","description":"<what>","success_criterion":"<measurable outcome>"}}]}}
Rules: ≤{MAX_STEPS} steps. Each step uses ONLY read_file/write_file/fetch_url. No code execution. success_criterion must be falsifiable."""

def generate_plan(client: OpenAI, task: str) -> dict:
    section("Generating Plan")
    raw = chat(client, [{"role":"system","content":PLAN_SYS},
                        {"role":"user","content":task}], json_mode=True)
    plan = json.loads(raw)
    if not isinstance(plan.get("steps"), list): raise ValueError("Plan missing steps")
    plan["steps"] = plan["steps"][:MAX_STEPS]
    return plan

# ─── Plan Review Gate ─────────────────────────────────────────────────────────

REVIEW_SYS = """You are a strict plan reviewer. Check: clarity, safety (no file deletion/system commands), feasibility (read_file/write_file/fetch_url only), completeness.
Return ONLY valid JSON: {"approved":true/false,"confidence":0.0-1.0,"issues":[],"revised_steps":null}"""

def review_plan(client: OpenAI, task: str, plan: dict) -> dict:
    section("Plan Review Gate")
    raw = chat(client,
               [{"role":"system","content":REVIEW_SYS},
                {"role":"user","content":f"Task:\n{task}\n\nPlan:\n{json.dumps(plan,indent=2)}"}],
               json_mode=True)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"approved": False, "confidence": 0.0,
                "issues": [f"Review produced malformed JSON: {raw[:200]}"],
                "revised_steps": None}

# ─── Step Execution ──────────────────────────────────────────────────────────

STEP_SYS = """You are a step executor with access to: read_file, write_file, fetch_url.
Execute the given step exactly using tools. Report only what tools actually returned."""

def execute_step(client: OpenAI, conn: sqlite3.Connection,
                 step: dict, step_id: str, context: str) -> str:
    msgs: list[dict] = [
        {"role":"system","content":STEP_SYS},
        {"role":"user","content":(
            f"Step {step['index']+1}: {step['description']}\n"
            f"Success: {step.get('success_criterion', 'complete the step as described')}\n"
            f"Prior context:\n{context or '(none)'}")}]
    all_evidence: list[str] = []
    for _ in range(8):
        resp = client.chat.completions.create(model=MODEL, messages=msgs, tools=TOOLS, tool_choice="auto")
        msg  = resp.choices[0].message
        if not msg.tool_calls:
            narrative = msg.content or "(no output)"
            if all_evidence:
                return "Tool calls executed:\n" + "\n".join(all_evidence) + "\n\n" + narrative
            return narrative
        msgs.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ],
        })
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            # Some models (e.g. Llama on DeepInfra) wrap args in an array
            if isinstance(args, list):
                args = args[0] if args else {}
            result = dispatch(tc.function.name, args)
            all_evidence.append(f"[{tc.function.name}({tc.function.arguments[:120]})] → {result[:200]}")
            conn.execute("INSERT INTO tool_calls VALUES (?,?,?,?,?,?)",
                         (str(uuid.uuid4()), step_id, tc.function.name,
                          tc.function.arguments, result[:4000], now()))
            conn.commit()
            msgs.append({"role":"tool","tool_call_id":tc.id,"content":result[:8000]})
    return "(step hit tool-use limit)"

# ─── Adversarial Verifier ────────────────────────────────────────────────────

VERIFY_SYS = """You are a strict adversarial verifier. Your default stance is REJECT. You are looking for reasons to fail the task, not to pass it.

Mandatory rejection rules — if ANY apply, verdict must be "reject":
1. The original task is vague, physically impossible, or logically absurd (e.g. "make the universe compute X", "fix everything", "do magic").
2. The executor rewrote or reinterpreted the task instead of completing it (philosophical answers, metaphors, or reframes are NOT completions).
3. A step's success criterion was not met by concrete tool evidence (file written, URL fetched, data confirmed). "Claimed" results without tool output are failures.
4. The task required capabilities beyond read_file/write_file/fetch_url and was therefore uncompletable.

Confidence scale: 0.0–0.4 = strong evidence of failure, 0.4–0.74 = significant doubts, 0.75+ = strong concrete evidence every step was completed as specified.

Return ONLY valid JSON:
{"verdict":"accept|reject","confidence":0.0-1.0,
 "step_verdicts":[{"index":0,"passed":true,"note":""}],
 "overall_reason":"<paragraph>"}"""

def verify_outcome(client: OpenAI, task: str, plan: dict, results: list[dict]) -> dict:
    section("Adversarial Verification")
    evidence = "\n\n".join(
        f"Step {r['index']+1} ({r['description']}):\n{r['result']}" for r in results)
    raw = chat(client,
               [{"role":"system","content":VERIFY_SYS},
                {"role":"user","content":
                    f"Task:\n{task}\n\nGoal: {plan.get('goal','')}\n\nResults:\n{evidence}"}],
               json_mode=True)
    return json.loads(raw)

# ─── Main Executor ────────────────────────────────────────────────────────────

def run_task(client: OpenAI, conn: sqlite3.Connection, description: str) -> str:
    task_id = str(uuid.uuid4())
    conn.execute("INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)",
                 (task_id, description, "planning", None, None, None, None, now(), None))
    conn.commit()
    section("Task"); pr(description)

    # 1. Plan
    try:
        plan = generate_plan(client, description)
    except Exception as e:
        pr(f"[ERROR] Plan generation failed: {e}", "bold red")
        conn.execute("UPDATE tasks SET status='failed',finished_at=? WHERE id=?", (now(), task_id))
        conn.commit(); return task_id

    conn.execute("UPDATE tasks SET plan_json=? WHERE id=?", (json.dumps(plan), task_id))
    conn.commit()
    pr(f"\nGoal: {plan.get('goal','')}", "bold")
    for s in plan.get("steps", []):
        pr(f"  {s['index']+1}. [{s['type']}] {s['description']}", "dim")

    # 2. Review gate
    review = review_plan(client, description, plan)
    approved = review.get("approved", False)
    pr(f"\nReview: {'APPROVED' if approved else 'REJECTED'} "
       f"({review.get('confidence',0):.0%})")
    for issue in review.get("issues", []):
        pr(f"  • {issue}", "dim")

    if not approved:
        raw_issues = review.get("issues", ["plan not approved"])
        reason = "; ".join(
            i.get("issue", str(i)) if isinstance(i, dict) else str(i)
            for i in raw_issues
        )
        pr("[ERROR] Plan rejected. Aborting.", "bold red")
        conn.execute("UPDATE tasks SET status='rejected',verdict='rejected',"
                     "reason=?,finished_at=? WHERE id=?", (reason, now(), task_id))
        conn.commit(); return task_id

    if review.get("revised_steps"):
        plan["steps"] = review["revised_steps"]

    # 3. Execute steps
    conn.execute("UPDATE tasks SET status='executing' WHERE id=?", (task_id,))
    conn.commit()
    steps, results, ctx_parts = plan.get("steps", []), [], []

    for step in steps:
        sid = str(uuid.uuid4())
        section(f"Step {step['index']+1}/{len(steps)}: {step['description']}")
        conn.execute("INSERT INTO steps VALUES (?,?,?,?,?,?,?,?,?)",
                     (sid, task_id, step["index"], step["type"],
                      step["description"], None, "running", now(), None))
        conn.commit()
        result = execute_step(client, conn, step, sid, "\n".join(ctx_parts))
        pr(result)
        results.append({"index":step["index"],"description":step["description"],
                         "success_criterion":step.get("success_criterion",""),"result":result})
        ctx_parts.append(f"Step {step['index']+1}: {result[:800]}")
        conn.execute("UPDATE steps SET result=?,status='done',finished_at=? WHERE id=?",
                     (result[:4000], now(), sid))
        conn.commit()

    # 4. Verify
    try:
        vdata = verify_outcome(client, description, plan, results)
    except Exception as e:
        vdata = {"verdict":"reject","confidence":0.0,"overall_reason":f"Verification error: {e}"}

    verdict    = vdata.get("verdict", "reject")
    confidence = float(vdata.get("confidence", 0))
    reason     = vdata.get("overall_reason", "")

    if verdict == "accept" and confidence < THRESHOLD:
        verdict = "reject"
        reason  = f"Confidence {confidence:.0%} below {THRESHOLD:.0%}. " + reason

    section("Verdict")
    if verdict == "accept":
        pr(f"ACCEPTED ({confidence:.0%})", "bold green")
    else:
        pr(f"REJECTED ({confidence:.0%})", "bold red")
    pr(f"\n{reason}")
    for sv in vdata.get("step_verdicts", []):
        pr(f"  {'✓' if sv.get('passed') else '✗'} Step {sv['index']+1}: {sv.get('note','')}", "dim")

    conn.execute("UPDATE tasks SET status=?,verdict=?,confidence=?,reason=?,finished_at=? WHERE id=?",
                 (verdict, verdict, confidence, reason, now(), task_id))
    conn.commit()
    return task_id

# ─── CLI ─────────────────────────────────────────────────────────────────────

def list_tasks(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        "SELECT id,status,verdict,confidence,created_at,description FROM tasks "
        "ORDER BY created_at DESC LIMIT 20").fetchall()
    if not rows: pr("No tasks."); return
    if HAS_RICH:
        t = Table(title="Recent Tasks", show_lines=True)
        for col in ("ID","Status","Verdict","Conf","Created","Description"):
            t.add_column(col)
        for r in rows:
            t.add_row(r[0][:8], r[1], r[2] or "—",
                      f"{r[3]:.0%}" if r[3] is not None else "—",
                      r[4][:16], r[5][:60])
        console.print(t)  # type: ignore
    else:
        for r in rows:
            print(f"{r[0][:8]} | {r[1]:10} | {r[2] or '—':8} | {r[4][:16]} | {r[5][:60]}")

def show_task(conn: sqlite3.Connection, prefix: str) -> None:
    row = conn.execute("SELECT * FROM tasks WHERE id LIKE ?", (prefix+"%",)).fetchone()
    if not row: pr(f"No task matching '{prefix}'", "bold red"); return
    pr(f"\nTask: {row[0]}\nStatus: {row[2]} | Verdict: {row[4]} | Conf: {row[5]}")
    pr(f"Description: {row[1]}\nReason: {row[6]}\n")
    for s in conn.execute("SELECT step_index,step_type,description,status,result "
                          "FROM steps WHERE task_id=? ORDER BY step_index", (row[0],)):
        pr(f"  Step {s[0]+1} [{s[1]}]: {s[2]} — {s[3]}", "dim")

def main() -> None:
    global MODEL
    p = argparse.ArgumentParser(description="Autonomous task executor")
    p.add_argument("task", nargs="?", help="Task description")
    p.add_argument("--list-tasks", action="store_true")
    p.add_argument("--task-id", help="Inspect a task by ID prefix")
    p.add_argument("--model", default=MODEL)
    args = p.parse_args()

    MODEL = args.model
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH); init_db(conn)

    if args.list_tasks:   list_tasks(conn); return
    if args.task_id:      show_task(conn, args.task_id); return

    if not args.task:
        try:
            from rich.prompt import Prompt
            task = Prompt.ask("[bold]Describe the task[/bold]")
        except ImportError:
            task = input("Task: ").strip()
        if not task: sys.exit("No task provided.")
    else:
        task = args.task

    client  = get_client()
    task_id = run_task(client, conn, task)
    pr(f"\nTask ID: {task_id}", "dim")
    conn.close()

if __name__ == "__main__":
    main()
