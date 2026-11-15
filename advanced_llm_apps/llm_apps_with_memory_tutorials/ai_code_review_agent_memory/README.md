## 🔍 AI Code Review Agent with Memory

A Streamlit app that learns a team's conventions from its past pull request review comments and applies them to new diffs. Each lesson remembers which version of which file it was learned on, so when the code changes, the agent tells you whether the lesson is still current, needs a re-check, or is probably stale.

### What you learn

- How to turn noisy review comments into a few durable lessons with one structured model call per comment (a gate).
- How to anchor a memory to code with a file path, a symbol and the file's git blob hash.
- How to recall memories for a diff by the files and symbols it touches, with a ranking you can read in five lines.
- How to check a memory's freshness against the code as it is today, and show it to the model and to the reader.

### How it works

```
past review comments ──> 1. Learn ──> 2. Gate (keep / drop) ──> 3. Anchor (file, symbol, blob hash) ──> LessonStore
                                                                                                         │
new diff ──> files + enclosing functions ──> 4. Recall and rank ──> 5. Freshness check ──> 6. Review, citing [L<id>]
```

1. **Learn:** `comments_from_github()` reads a repo's newest inline review comments through the GitHub REST API (a token is optional for public repos). `comments_from_file()` reads `sample_review_comments.json`: sample comments written for this tutorial about [`psf/requests`](https://github.com/psf/requests) v2.32.3.
2. **Gate:** `gate()` asks the model whether a comment states a lasting rule about the code. It returns JSON: `keep`, `reason`, a rewritten `lesson`, the `file` and the `symbol`. Typos, approvals and "please rebase" are dropped.
3. **Anchor:** `anchor()` stores each kept lesson with its file, symbol and `git hash-object <file>` from your local checkout.
4. **Recall and rank:** `touched()` reads the diff for the files it changes, the function around each changed line and the identifiers on it. `score()` adds 3 for the same file (1 for the same directory), 2 for a symbol match, +1 / 0 / -2 for current / changed / stale, and subtracts up to 1 for age. The top k are kept.
5. **Freshness check:** `freshness()` compares the stored blob hash with the file today. Same hash: 🟢 current. Different hash but the symbol is still in the file: 🟡 changed, re-check. Symbol gone: 🔴 probably stale.
6. **Review:** `review()` gives the model the diff and the ranked lessons with their states, and asks it to cite each lesson it used as `[L<id>]`.

### Getting started

1. Clone the repository and install the dependencies (Python 3.10+, and `git` on your PATH):

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_llm_apps/llm_apps_with_memory_tutorials/ai_code_review_agent_memory
pip install -r requirements.txt
```

2. Get a local checkout of the code the comments are about. For the sample comments:

```bash
git clone --depth 1 -b v2.32.3 https://github.com/psf/requests.git /tmp/requests
```

3. Run the app:

```bash
export OPENAI_API_KEY=sk-...     # or ANTHROPIC_API_KEY, or type it in the sidebar
export REPO_DIR=/tmp/requests
streamlit run ai_code_review_agent_memory.py
```

4. In **1. Learn from past reviews**, click **Learn**. The table shows which comments were kept as lessons and why the others were dropped.
5. Edit a file in the checkout, for example change `should_strip_auth` in `src/requests/sessions.py`. In **2. Review a diff**, click **Load `git diff` from the checkout**, then **Review**. The lessons on that file come back ranked, marked 🟡 because the file changed since they were learned, and the review cites them.

Lessons are stored in `lessons.db` (SQLite) next to where you run the app. Set `LESSONS_DB` to use another file. No other services are needed.

### Optional: share lessons with Loom

The SQLite store is one file on one machine. To share lessons across a team and the agents working in the same repo, the app can store them in [Loom](https://github.com/ClickHouse/loom), a self-hosted memory server for agents, through `LoomLessonStore` (about 30 lines over its HTTP API). Each lesson becomes one memory under the key `review-lesson/<id>` with its file path. The technique in this tutorial does not change: gating, anchoring, ranking and freshness all still run in this file.

Start Loom locally with its [quickstart](https://clickhouse.github.io/loom/getting-started/quickstart/), then switch the backend:

```bash
export LESSON_STORE=loom
export LOOM_URL=http://localhost:7777   # the default
export LOOM_API_KEY=...                 # only on an install with sign-in
streamlit run ai_code_review_agent_memory.py
```

### Adapt it

- **Another model:** `build_model()` is the only place that picks the provider; it returns one `ask(prompt, schema=None)` function.
- **Another store:** implement `save`, `list_for_files` and `mark` of `LessonStore`.
- **Use it from a script or CI job:** import `build_agent()`; the Streamlit code is only in `main()`.

### Limits

- `touched()` finds the enclosing function with a regex for `def`, `class`, `function`, `func` and `fn` lines. Other languages need their keyword added.
- A lesson marked 🟡 stays that way until you learn it again on the new version of the file.
- The GitHub reader takes the newest comments only (up to 100) and skips bot accounts.
