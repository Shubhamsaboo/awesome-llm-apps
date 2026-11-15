"""AI Code Review Agent with Memory: learns a team's conventions from its past review comments.

    1. Learn    read past PR review comments (GitHub REST API or a local JSON file)
    2. Gate     one model call per comment: a durable, code-specific lesson, or a one-off?
    3. Anchor   store each kept lesson with its file, symbol and the file's git blob hash
    4. Recall   for a new diff, rank the lessons on the files and symbols it touches
    5. Fresh    compare the stored blob hash with the file today: current, changed or stale
    6. Review   the model reviews the diff with the ranked lessons and cites the ones it used

The agent code is at the top and the Streamlit app is in `main()`, so you can import
`build_agent` from another script without starting the UI.
"""

import hashlib
import json
import os
import re
import sqlite3
import subprocess
import time
from dataclasses import asdict, dataclass

import httpx
import streamlit as st

DEFAULT_MODELS = {"OpenAI": "gpt-4.1-mini", "Anthropic": "claude-sonnet-5-5"}
SAMPLE_FILE = os.path.join(os.path.dirname(__file__), "sample_review_comments.json")


# --- The model: one function that returns text, or a dict that matches a JSON schema ---

def build_model(provider: str, api_key: str, model: str):
    """The one place that picks the model provider. Returns ask(prompt, schema=None)."""
    if provider == "Anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        def ask(prompt, schema=None):
            args = {"model": model, "max_tokens": 2048, "messages": [{"role": "user", "content": prompt}]}
            if schema:
                args["output_config"] = {"format": {"type": "json_schema", "schema": schema}}
            reply = client.messages.create(**args)
            text = next(block.text for block in reply.content if block.type == "text")
            return json.loads(text) if schema else text
        return ask

    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    def ask(prompt, schema=None):
        args = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        if schema:
            args["response_format"] = {"type": "json_schema",
                                       "json_schema": {"name": "answer", "schema": schema, "strict": True}}
        text = client.chat.completions.create(**args).choices[0].message.content
        return json.loads(text) if schema else text
    return ask


# --- 1. Learn: past review comments become candidate lessons ---

def comments_from_github(repo: str, token: str = "", limit: int = 50) -> list[dict]:
    """The newest inline review comments of a public repo, e.g. repo='psf/requests'."""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"https://api.github.com/repos/{repo}/pulls/comments"
    params = {"sort": "created", "direction": "desc", "per_page": min(limit, 100)}
    rows = httpx.get(url, headers=headers, params=params, timeout=30).raise_for_status().json()
    return [{"body": r["body"], "path": r["path"], "diff_hunk": r.get("diff_hunk") or "",
             "created_at": r["created_at"], "url": r["html_url"]}
            for r in rows if not r["user"]["login"].endswith("[bot]")][:limit]


def comments_from_file(path: str = SAMPLE_FILE) -> list[dict]:
    with open(path) as f:
        return json.load(f)


# --- 2. Gate: keep only durable, code-specific lessons ---

GATE_SCHEMA = {
    "type": "object",
    "properties": {
        "keep": {"type": "boolean"},
        "reason": {"type": "string"},
        "lesson": {"type": "string"},
        "file": {"type": "string"},
        "symbol": {"type": "string"},
    },
    "required": ["keep", "reason", "lesson", "file", "symbol"],
    "additionalProperties": False,
}

GATE_PROMPT = """You decide whether a code review comment teaches a lasting lesson about this codebase.

Keep it when it states a rule that will still matter on the next change to this code: an
invariant, a security or correctness boundary, an API contract, a convention the team enforces.
Drop it when it is a one-off: a typo, a style nit about one line, thanks or approval, a
request to rebase, or anything about the process instead of the code.

If you keep it, rewrite it as one imperative sentence a reviewer could apply to a future diff.
`file` is the file it is about (default: the commented file). `symbol` is the one function,
class or method it is about, written as it appears in the code (e.g. `send`, not `HTTPAdapter.send()`),
or "" if none. If you drop it, leave lesson, file and symbol empty.

Commented file: {path}
Diff hunk:
{hunk}

Comment:
{body}"""


def gate(ask, comment: dict) -> dict:
    hunk = comment.get("diff_hunk", "")[-1500:]
    return ask(GATE_PROMPT.format(path=comment["path"], hunk=hunk, body=comment["body"]), GATE_SCHEMA)


# --- 3. Anchor: a lesson remembers which version of the file it was learned on ---

@dataclass
class Lesson:
    id: str
    text: str
    file: str
    symbol: str
    blob: str          # `git hash-object <file>` when the lesson was learned
    learned_at: float  # unix time
    source: str = ""   # the review comment's URL
    state: str = "current"  # current | changed, re-check | probably stale


def blob_hash(repo_dir: str, path: str) -> str:
    """The git blob hash of the file as it is on disk now; '' when the file is gone."""
    if not os.path.isfile(os.path.join(repo_dir, path)):
        return ""
    out = subprocess.run(["git", "hash-object", path], cwd=repo_dir, capture_output=True, text=True)
    return out.stdout.strip()


def anchor(verdict: dict, comment: dict, repo_dir: str) -> Lesson:
    path = verdict["file"] or comment["path"]
    # The id comes from the comment, so learning the same comments again updates the lessons.
    lesson_id = hashlib.sha1((comment.get("url", "") + comment["body"]).encode()).hexdigest()[:8]
    return Lesson(id=lesson_id, text=verdict["lesson"], file=path,
                  symbol=verdict["symbol"].strip("`() "), blob=blob_hash(repo_dir, path),
                  learned_at=time.time(), source=comment.get("url", ""))


class LessonStore:
    """Where lessons live. Two implementations: SQLite (default) and Loom (optional)."""

    def save(self, lesson: Lesson) -> None: ...
    def list_for_files(self, paths: list[str]) -> list[Lesson]: ...
    def mark(self, lesson: Lesson, state: str) -> None: ...


class SqliteLessonStore(LessonStore):
    def __init__(self, path: str = "lessons.db"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS lessons (id TEXT PRIMARY KEY, text TEXT, file TEXT, "
                        "symbol TEXT, blob TEXT, learned_at REAL, source TEXT, state TEXT)")

    def save(self, lesson):
        self.db.execute("INSERT OR REPLACE INTO lessons VALUES (?,?,?,?,?,?,?,?)", tuple(asdict(lesson).values()))
        self.db.commit()

    def list_for_files(self, paths):
        """Lessons on these files, or on other files in the same directories."""
        dirs = {os.path.dirname(p) for p in paths}
        rows = self.db.execute("SELECT * FROM lessons").fetchall()
        # The columns are in the order of Lesson's fields, so a row builds a Lesson.
        return [Lesson(*r) for r in rows if r[2] in paths or os.path.dirname(r[2]) in dirs]

    def mark(self, lesson, state):
        self.db.execute("UPDATE lessons SET state=? WHERE id=?", (state, lesson.id))
        self.db.commit()


class LoomLessonStore(LessonStore):
    """Each lesson is one Loom memory under `review-lesson/<id>`, with its file in `files`.

    Use it to share lessons across a team and its agents. Talks to Loom's HTTP API:
    every op is `POST /v1/<op>` with a JSON body.
    """

    def __init__(self, url: str = "http://localhost:7777", token: str = "",
                 org: str = "default", namespace: str = "code-review-lessons"):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        self.http = httpx.Client(base_url=url.rstrip("/"), headers=headers, timeout=30)
        self.scope = {"org": org, "namespace": namespace, "agent": "code-review-agent"}

    def _op(self, op: str, **args) -> dict:
        return self.http.post(f"/v1/{op}", json={**self.scope, **args}).raise_for_status().json()

    def save(self, lesson):
        self._op("memory.set", memory_key=f"review-lesson/{lesson.id}", value=asdict(lesson),
                 tags=["review-lesson"], files=[lesson.file])

    def list_for_files(self, paths):
        dirs = {os.path.dirname(p) for p in paths}
        entries = self._op("memory.list", prefix="review-lesson/", limit=1000)["entries"]
        lessons = [Lesson(**e["value"]) for e in entries if isinstance(e.get("value"), dict)]
        return [x for x in lessons if x.file in paths or os.path.dirname(x.file) in dirs]

    def mark(self, lesson, state):
        lesson.state = state
        self.save(lesson)  # a write to the same key adds a new version


def learn(ask, store: LessonStore, comments: list[dict], repo_dir: str) -> list[dict]:
    """Steps 1-3. Returns one row per comment so the UI can show what was kept and dropped."""
    report = []
    for c in comments:
        verdict = gate(ask, c)
        if verdict["keep"]:
            store.save(anchor(verdict, c, repo_dir))
        report.append({"kept": verdict["keep"], "lesson": verdict["lesson"] or c["body"][:120],
                       "file": verdict["file"] or c["path"], "symbol": verdict["symbol"],
                       "reason": verdict["reason"]})
    return report


# --- 4. Recall: which files and symbols does the diff touch? ---

DEFINITION = re.compile(r"^\s*(?:async\s+)?(?:def|class|function|func|fn)\s+([A-Za-z_]\w*)")


def enclosing(repo_dir: str, path: str, line_no: int) -> str:
    """The nearest function or class defined above a line of the file; '' if none."""
    full = os.path.join(repo_dir, path)
    lines = open(full, errors="ignore").read().splitlines()[:line_no] if os.path.isfile(full) else []
    for line in reversed(lines):
        if m := DEFINITION.match(line):
            return m.group(1)
    return ""


def touched(diff: str, repo_dir: str) -> tuple[list[str], set[str]]:
    """The files a unified diff changes, the functions around each change, and every
    identifier on the changed lines."""
    files, words, line_no = [], set(), 0
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            files.append(line[6:].strip())
        elif line.startswith("@@"):
            line_no = int(re.search(r"\+(\d+)", line).group(1))  # first line of the hunk in the new file
        elif line.startswith(("+", "-")) and not line.startswith(("+++", "---")) and files:
            words.update(re.findall(r"[A-Za-z_]\w*", line))
            words.add(enclosing(repo_dir, files[-1], line_no))
            line_no += line.startswith("+")
        elif files:
            line_no += 1  # a context line
    return files, words - {""}


# --- 5. Freshness: is the lesson still about the code as it is today? ---

def freshness(lesson: Lesson, repo_dir: str) -> str:
    now = blob_hash(repo_dir, lesson.file)
    if now and now == lesson.blob:
        return "current"
    path = os.path.join(repo_dir, lesson.file)
    text = open(path, errors="ignore").read() if os.path.isfile(path) else ""
    if lesson.symbol and re.search(rf"\b{re.escape(lesson.symbol)}\b", text):
        return "changed, re-check"
    return "probably stale"


def score(lesson: Lesson, files: list[str], words: set[str]) -> float:
    file_match = 3 if lesson.file in files else 1  # same file, or only the same directory
    symbol_match = 2 if lesson.symbol and lesson.symbol in words else 0
    fresh = {"current": 1, "changed, re-check": 0, "probably stale": -2}[lesson.state]
    age = min((time.time() - lesson.learned_at) / (180 * 86400), 1)  # 0 today, 1 after six months
    return file_match + symbol_match + fresh - age


def recall(store: LessonStore, diff: str, repo_dir: str, k: int = 5) -> list[tuple[float, Lesson]]:
    files, words = touched(diff, repo_dir)
    ranked = []
    for lesson in store.list_for_files(files):
        state = freshness(lesson, repo_dir)
        if state != lesson.state:
            store.mark(lesson, state)
            lesson.state = state
        ranked.append((score(lesson, files, words), lesson))
    return sorted(ranked, key=lambda x: -x[0])[:k]


# --- 6. Review: the model reviews the diff with the lessons and cites the ones it used ---

REVIEW_PROMPT = """You are reviewing a pull request for a team. Below are lessons learned from
the team's past reviews of this code, each with an id and a freshness state. A lesson marked
"changed, re-check" was learned on an older version of the file: check that it still applies
before using it. A lesson marked "probably stale" may be about code that no longer exists.

Lessons:
{lessons}

Diff:
{diff}

Write a short review: the problems in the diff, most important first. Cite each lesson you
used as [L<id>] next to the point it supports, and end with a line "Lessons used: ..." listing
the ids (or "none"). Do not cite a lesson that does not apply to this diff."""


def review(ask, diff: str, ranked: list[tuple[float, Lesson]]) -> str:
    lines = [f"[L{x.id}] ({x.state}; {x.file}{' :: ' + x.symbol if x.symbol else ''}) {x.text}"
             for _, x in ranked]
    return ask(REVIEW_PROMPT.format(lessons="\n".join(lines) or "(none)", diff=diff[:20000]))


def build_agent(provider: str, api_key: str, model: str, store: LessonStore, repo_dir: str):
    """The agent without the UI: learn(comments), recall(diff, k) and review(diff, ranked)."""
    ask = build_model(provider, api_key, model)
    return {
        "learn": lambda comments: learn(ask, store, comments, repo_dir),
        "recall": lambda diff, k=5: recall(store, diff, repo_dir, k),
        "review": lambda diff, ranked: review(ask, diff, ranked),
    }


def git_diff(repo_dir: str) -> str:
    return subprocess.run(["git", "diff"], cwd=repo_dir, capture_output=True, text=True).stdout


# --- The Streamlit app ---

def main() -> None:
    st.set_page_config(page_title="AI Code Review Agent with Memory", page_icon="🔍", layout="wide")
    st.title("🔍 AI Code Review Agent with Memory")
    st.caption("Learns your team's conventions from past review comments and applies them to new diffs.")

    with st.sidebar:
        provider = st.selectbox("Model provider", ["OpenAI", "Anthropic"])
        env_key = os.environ.get(f"{provider.upper()}_API_KEY", "")
        api_key = st.text_input(f"{provider} API key", type="password") or env_key
        model = st.text_input("Model", value=DEFAULT_MODELS[provider])
        repo_dir = st.text_input("Local checkout of the repo", value=os.environ.get("REPO_DIR", "."))
        backend = st.selectbox("Lesson store", ["SQLite", "Loom"], index=int(os.environ.get("LESSON_STORE") == "loom"))
        if backend == "Loom":
            store = LoomLessonStore(os.environ.get("LOOM_URL", "http://localhost:7777"),
                                    os.environ.get("LOOM_API_KEY", ""))
        else:
            store = SqliteLessonStore(os.environ.get("LESSONS_DB", "lessons.db"))
    if not api_key:
        st.info(f"Enter your {provider} API key in the sidebar.")
        return
    agent = build_agent(provider, api_key, model, store, repo_dir)

    learn_tab, review_tab = st.tabs(["1. Learn from past reviews", "2. Review a diff"])
    with learn_tab:
        source = st.radio("Comments from", ["Sample file", "GitHub repo"], horizontal=True)
        if source == "GitHub repo":
            repo = st.text_input("owner/repo", value="psf/requests")
            gh_token = st.text_input("GitHub token (optional for public repos)", type="password")
            limit = st.slider("Comments to read", 5, 100, 20)
        if st.button("Learn"):
            with st.spinner("Reading comments and gating each one..."):
                if source == "Sample file":
                    comments = comments_from_file()
                else:
                    comments = comments_from_github(repo, gh_token, limit)
                report = agent["learn"](comments)
            st.success(f"Kept {sum(r['kept'] for r in report)} of {len(report)} comments as lessons.")
            st.dataframe(report)

    with review_tab:
        def load_git_diff():
            st.session_state.diff = git_diff(repo_dir) or "(no local changes)"
        st.button("Load `git diff` from the checkout", on_click=load_git_diff)
        diff = st.text_area("Or paste a unified diff", height=250, key="diff")
        k = st.slider("Lessons to use (top k)", 1, 10, 5)
        if st.button("Review") and diff.strip():
            ranked = agent["recall"](diff, k)
            st.subheader("Lessons recalled")
            icons = {"current": "🟢", "changed, re-check": "🟡", "probably stale": "🔴"}
            for s, x in ranked:
                st.markdown(f"{icons[x.state]} **L{x.id}** `{x.file}` `{x.symbol}` score {s:.1f} "
                            f"*({x.state})*  \n{x.text}")
            if not ranked:
                st.write("No lessons on these files yet.")
            with st.spinner("Reviewing..."):
                st.subheader("Review")
                st.markdown(agent["review"](diff, ranked))


if __name__ == "__main__":
    main()
