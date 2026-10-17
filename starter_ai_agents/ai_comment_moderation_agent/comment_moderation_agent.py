import csv
import json
import os
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import pandas as pd
import streamlit as st

API_URL = os.environ.get("TRIO_SPARK_API_URL", "https://platform.machinefi.com/v1/systemone")
MODEL = "trio-spark-v1.3"
PRICE_PER_INPUT_TOKEN = 0.042 / 1_000_000  # USD; output is not metered
SAMPLE = Path(__file__).with_name("sample_comments.csv")

QUESTION = {
    "type": "choice",
    "instructions": "Moderate this comment for a public comment section. Decide whether it can be shown or should be hidden.",
    "criteria": {
        "show": "Fine to show: civil, on-topic, or just critical or opinionated",
        "hide": "Hide: insults, obscenity, harassment, hate or threats",
    },
}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    # Keep the API key on the intended host even if a proxy redirects.
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def p_hide(comment: str, api_key: str) -> tuple[float, int]:
    """One decision: returns P(hide) and the billed input tokens."""
    body = json.dumps({"model": MODEL, "state": comment, "questions": {"moderation": QUESTION}}).encode()
    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
        "Idempotency-Key": str(uuid.uuid4()),
    }
    for attempt in range(6):
        try:
            request = urllib.request.Request(API_URL, data=body, headers=headers, method="POST")
            with urllib.request.build_opener(NoRedirect()).open(request, timeout=45) as response:
                result = json.load(response)
            return result["answers"]["moderation"]["probabilities"]["hide"], result["usage"]["input_tokens"]
        except urllib.error.HTTPError as error:
            if error.code not in (429, 503) or attempt == 5:
                raise RuntimeError(f"{error.code}: {error.read().decode()[:200]}") from None
            time.sleep(1.5 * (attempt + 1))  # the service is busy; back off and retry


def action(p: float, review_at: float, hide_at: float) -> str:
    if p >= hide_at:
        return "🚫 Hide"
    if p >= review_at:
        return "👀 Review"
    return "✅ Show"


st.set_page_config(page_title="AI Comment Moderation Agent", page_icon="🛡️", layout="wide")
st.title("🛡️ AI Comment Moderation Agent")
st.caption(
    "Every comment gets one decision from Trio-Spark, a decision model that returns a probability "
    "for each option instead of generated text. You set the policy; changing it never re-runs the model."
)

with st.sidebar:
    api_key = st.text_input("Trio-Spark API key", type="password", value=os.environ.get("TRIO_SPARK_API_KEY", ""))
    st.markdown("[Get a key](https://platform.machinefi.com/spark#api-keys) (new accounts include free trial decisions)")
    st.divider()
    st.subheader("Policy")
    hide_at = st.slider("Auto-hide when P(hide) ≥", 0.50, 0.99, 0.70, 0.01)
    review_at = st.slider("Send to a human when P(hide) ≥", 0.05, hide_at, min(0.40, hide_at), 0.01)

default = ""
if st.button("Load 30 sample comments"):
    with SAMPLE.open() as f:
        st.session_state.labels = {row["comment"]: row["human_label"] for row in csv.DictReader(f)}
    st.session_state.comments = "\n".join(st.session_state.labels)
comments_text = st.text_area("Comments, one per line", value=st.session_state.get("comments", default), height=220)

if st.button("Moderate", type="primary"):
    comments = [line.strip() for line in comments_text.splitlines() if line.strip()]
    if not api_key:
        st.error("Add your Trio-Spark API key in the sidebar.")
    elif not comments:
        st.error("Paste at least one comment.")
    else:
        rows, progress, started = [], st.progress(0.0), time.perf_counter()
        for i, comment in enumerate(comments):
            try:
                p, tokens = p_hide(comment, api_key)
            except Exception as error:
                st.error(f"Stopped at comment {i + 1}: {error}")
                break
            rows.append({"comment": comment, "p_hide": p, "input_tokens": tokens})
            progress.progress((i + 1) / len(comments), text=f"{i + 1}/{len(comments)} moderated")
        st.session_state.results = rows
        st.session_state.seconds = time.perf_counter() - started

if rows := st.session_state.get("results"):
    df = pd.DataFrame(rows)
    df["action"] = [action(p, review_at, hide_at) for p in df["p_hide"]]
    labels = st.session_state.get("labels", {})
    if labels:
        df["human label"] = [labels.get(c, "") for c in df["comment"]]

    counts = df["action"].value_counts()
    cols = st.columns(5)
    cols[0].metric("Shown", int(counts.get("✅ Show", 0)))
    cols[1].metric("To review", int(counts.get("👀 Review", 0)))
    cols[2].metric("Hidden", int(counts.get("🚫 Hide", 0)))
    cols[3].metric("Time", f"{st.session_state.seconds:.1f} s")
    cols[4].metric("Model cost", f"${df['input_tokens'].sum() * PRICE_PER_INPUT_TOKEN:.5f}")

    st.dataframe(
        df.sort_values("p_hide", ascending=False),
        column_config={"p_hide": st.column_config.ProgressColumn("P(hide)", min_value=0.0, max_value=1.0, format="%.2f")},
        hide_index=True,
        width="stretch",
    )
    st.caption("Move the policy sliders: comments are re-sorted instantly from the stored probabilities.")
