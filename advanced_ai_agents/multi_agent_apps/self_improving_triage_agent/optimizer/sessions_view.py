"""Sessions tab: browse traced runs and give human feedback on calls, rounds and sessions.

Reads the local span store written by telemetry.py. Feedback is saved there and
emitted as a `human.feedback` span, so an OTLP collector receives it too.
"""

from datetime import datetime

import streamlit as st

import telemetry

RATING_LABELS = {1: "good", 0: "bad", None: "note"}
ROLE_ORDER = ["generate", "executor.route", "executor.score", "analyst", "mutator"]


def _when(ns) -> str:
    return datetime.fromtimestamp(ns / 1e9).strftime("%b %d %H:%M:%S") if ns else "?"


def _ms(span) -> str:
    if not span.get("end_ns") or not span.get("start_ns"):
        return "running"
    return f"{(span['end_ns'] - span['start_ns']) / 1e6:,.0f} ms"


def _feedback_form(trace_id: str, span_id: str, target: str) -> None:
    """Thumbs + comment for one span. Re-rating adds a new entry; the newest wins.

    The "last rating" line is read after any save, so it is current without a rerun.
    """
    # Keyed by target as well as span: one span can be rated in two roles.
    key = f"{target}-{span_id}"
    with st.form(key=f"fb-{key}", border=False):
        rating = st.feedback("thumbs", key=f"fb-rating-{key}")
        comment = st.text_input(
            "Comment", key=f"fb-comment-{key}",
            placeholder="What was right or wrong? e.g. 'should route to Platform: first error is the DB pool'",
        )
        if st.form_submit_button("Save feedback", icon=":material/rate_review:"):
            if rating is None and not comment.strip():
                st.warning("Pick a thumb or write a comment first.")
            else:
                telemetry.record_feedback(trace_id, span_id, target, rating, comment.strip())
                st.toast("Feedback saved", icon=":material/check:")
    prev = telemetry.store.latest_feedback(trace_id).get(span_id)
    if prev:
        st.caption(f"Your last rating: **{RATING_LABELS.get(prev['rating'], 'note')}**"
                   + (f" — {prev['comment']}" if prev["comment"] else ""))


def _call_detail(call: dict, trace_id: str) -> None:
    a = call["attributes"]
    with st.container(horizontal=True):
        st.badge(a.get("triage.role", "llm"), icon=":material/smart_toy:")
        st.badge(a.get("gen_ai.response.model") or a.get("gen_ai.request.model", ""), color="gray")
        if call["status"] == "ERROR":
            st.badge("error", color="red", icon=":material/error:")
    cols = st.columns(4)
    cols[0].metric("Latency", _ms(call))
    cols[1].metric("Input tokens", a.get("gen_ai.usage.input_tokens", "—"))
    cols[2].metric("Output tokens", a.get("gen_ai.usage.output_tokens", "—"))
    cost = a.get("triage.cost_usd")
    cols[3].metric("Cost (list)", f"${cost:.4f}" if cost is not None else "—")

    if "triage.user_prompt" in a:
        with st.expander("Prompt"):
            st.code(a.get("triage.system_prompt", ""), language="markdown", wrap_lines=True)
            st.code(a["triage.user_prompt"], language="markdown", wrap_lines=True)
        st.markdown("**Response**")
        st.code(a.get("triage.response", ""), language="json", wrap_lines=True)
    else:
        st.caption("Content not recorded (TRIAGE_TRACE_CONTENT=0).")
    for e in call["events"]:
        if e["name"] == "exception":
            st.error(e["attributes"].get("exception.message", "exception"))
    _feedback_form(trace_id, call["span_id"], "call")


@st.fragment
def render() -> None:
    st.subheader("Sessions")
    st.caption("Every optimizer run is one OpenTelemetry trace. Rate calls, rounds or "
               "the whole session; ratings are stored locally and exported as spans.")

    sessions = telemetry.store.sessions()
    if not sessions:
        st.info("No sessions yet. Run the loop or generate scenarios, then come back.")
        return

    by_id = {s["trace_id"]: s for s in sessions}
    tid = st.selectbox(
        "Session", list(by_id), key="sessions-pick",
        format_func=lambda t: (f"{_when(by_id[t]['start_ns'])} · {t[:8]} · {by_id[t]['backend'] or '?'} · "
                               f"{by_id[t]['model'] or '?'} · {by_id[t]['calls']} calls"
                               + (f" · {by_id[t]['errors']} errors" if by_id[t]["errors"] else "")),
    )
    s = by_id[tid]
    spans = [x for x in telemetry.store.spans(tid) if x["name"] != telemetry.FEEDBACK_SPAN]
    latest = telemetry.store.latest_feedback(tid)
    root = next((x for x in spans if x["parent_id"] is None), None)
    calls = [x for x in spans if x["name"] == "llm.call"]

    c = st.columns(5)
    c[0].metric("Backend", s["backend"] or "—")
    c[1].metric("LLM calls", s["calls"])
    c[2].metric("Tokens in / out", f"{s['input_tokens']:,} / {s['output_tokens']:,}")
    if root and "triage.final_score" in root["attributes"]:
        ra = root["attributes"]
        c[3].metric("Score", f"{ra['triage.final_score']}%",
                    delta=f"{ra['triage.final_score'] - ra['triage.baseline_score']:+.1f}")
    c[4].metric("Rated", s["rated"])
    st.caption(f"Trace ID `{tid}` — search for it in your OTLP backend.")

    # A single-call trace (e.g. older "Generate scenarios" runs) has the call as
    # its root; the call's own form below covers it.
    if root and root["name"] != "llm.call":
        with st.expander("Rate this whole session", icon=":material/thumbs_up_down:"):
            _feedback_form(tid, root["span_id"], "session")

    # Group calls under the baseline / round span that issued them.
    groups = [x for x in spans if x["name"] in ("optimizer.baseline", "optimizer.round")]
    groups.sort(key=lambda g: g["start_ns"])
    if not groups:
        groups_by_label = {"All calls": None}
    else:
        groups_by_label = {}
        for g in groups:
            ga = g["attributes"]
            if g["name"] == "optimizer.baseline":
                label = f"Baseline · {ga.get('triage.score', '?')}%"
            else:
                outcome = ("kept" if ga.get("triage.kept")
                           else "unchanged" if ga.get("triage.unchanged") else "discarded")
                label = (f"Round {ga.get('triage.round')} · {outcome} · "
                         f"{ga.get('triage.score_before', '?')}% → {ga.get('triage.score_after', '—')}%")
            groups_by_label[label] = g

    label = st.selectbox("Step", list(groups_by_label), key=f"step-{tid}")
    group = groups_by_label[label]
    if group is not None and group["name"] == "optimizer.round":
        ga = group["attributes"]
        st.markdown(f"**Strategy** `{ga.get('triage.strategy', '?')}` — {ga.get('triage.description', '')}")
        with st.expander("Rate this round's edit", icon=":material/edit_note:"):
            _feedback_form(tid, group["span_id"], "round")

    child_ids = _descendant_ids(spans, group["span_id"]) if group else None
    step_calls = [x for x in calls if child_ids is None or x["span_id"] in child_ids]
    step_calls.sort(key=lambda x: (ROLE_ORDER.index(x["attributes"].get("triage.role"))
                                   if x["attributes"].get("triage.role") in ROLE_ORDER else 99,
                                   x["start_ns"]))
    if not step_calls:
        st.info("No model calls in this step.")
        return

    def call_label(i):
        x = step_calls[i]
        a = x["attributes"]
        mark = {1: " · rated good", 0: " · rated bad"}.get(
            (latest.get(x["span_id"]) or {}).get("rating"), "")
        err = " · ERROR" if x["status"] == "ERROR" else ""
        return f"{i + 1}. {a.get('triage.role', 'llm')} · {_ms(x)}{err}{mark}"

    idx = st.selectbox("Call", range(len(step_calls)), format_func=call_label,
                       key=f"call-{tid}-{label}")
    with st.container(border=True):
        _call_detail(step_calls[idx], tid)


def _descendant_ids(spans: list, ancestor_id: str) -> set:
    children: dict = {}
    for x in spans:
        children.setdefault(x["parent_id"], []).append(x["span_id"])
    out, stack = set(), [ancestor_id]
    while stack:
        for c in children.get(stack.pop(), []):
            out.add(c)
            stack.append(c)
    return out
