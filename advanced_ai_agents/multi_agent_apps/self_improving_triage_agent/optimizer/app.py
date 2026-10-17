"""Streamlit UI for the self-improving triage agent.

Run:  streamlit run optimizer/app.py
"""

import asyncio
import difflib
import json
import os
import shutil
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from triage_optimizer import TriageOptimizer  # noqa: E402  (first litellm import; keep before copilot)
import copilot  # noqa: E402
import sessions_view  # noqa: E402
import telemetry  # noqa: E402
from triage_optimizer import CLAUDE_CODE_PREFIX  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_PATH = os.path.join(ROOT, "SKILL.md")
GOLDEN_PATH = os.path.join(ROOT, "references", "golden_set.json")

COPILOT = "GitHub Copilot"
CLAUDE_CODE = "Claude Code"
API_KEY = "API key"
BACKENDS = [COPILOT, CLAUDE_CODE, API_KEY]
# Aliases resolve to the latest model of each family on your Claude Code plan.
CLAUDE_CODE_MODELS = ["sonnet", "opus", "haiku"]

KEY_MODELS = {
    "OpenAI": ["gpt-4o-mini", "gpt-4o"],
    "Anthropic": ["anthropic/claude-sonnet-5"],
    "Google": ["gemini/gemini-2.0-flash", "gemini/gemini-2.5-pro"],
}

st.set_page_config(page_title="Self-Improving Triage Agent", page_icon="🔀", layout="wide")


def _load(path, default):
    try:
        with open(path) as f:
            return f.read() if path.endswith(".md") else json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


@st.cache_data(ttl=600, show_spinner="Loading your Copilot models…")
def _copilot_models():
    return copilot.list_models()


telemetry.init()
golden = _load(GOLDEN_PATH, {"teams": [], "scenarios": [], "evals": []})

st.title("🔀 Self-Improving Triage Agent")
st.caption(
    "Three agents hill-climb your `SKILL.md` until it routes non-prod issues to "
    "the right team. Only score-improving edits survive."
)

# -- Sidebar -----------------------------------------------------------------
with st.sidebar:
    st.header("Model")
    backend = st.segmented_control(
        "Backend", BACKENDS, default=COPILOT, required=True, key="backend",
        help="Copilot for cheap local experiments; Claude Code to compare against "
             "your Claude Code login. Every run is traced in the Sessions tab.",
    )
    api_key = None
    if backend == COPILOT:
        signed_in = copilot.is_signed_in()
        if signed_in:
            st.success("Signed in to GitHub Copilot", icon=":material/check_circle:")
        else:
            st.warning("Not signed in. In a terminal run:\n\n`python scripts/copilot_login.py`")
        options = _copilot_models() if signed_in else []
        model = st.selectbox("Model", options, key="copilot-model") if options else None
        custom = st.text_input("…or a model ID", placeholder="github_copilot/<model-id>",
                               key="copilot-custom")
        model = custom.strip() or model
        has_credential = bool(signed_in and model)
    elif backend == CLAUDE_CODE:
        cli = shutil.which(os.environ.get("TRIAGE_CLAUDE_BIN", "claude"))
        if cli:
            st.success("Using your Claude Code login", icon=":material/check_circle:")
        else:
            st.warning("`claude` not found on PATH. Install Claude Code and sign in.")
        alias = st.selectbox("Model", CLAUDE_CODE_MODELS, key="claude-code-model")
        model = CLAUDE_CODE_PREFIX + alias
        st.caption("Runs headless `claude -p` with no tools, settings, MCP or "
                   "CLAUDE.md, so only the skill under test shapes the answer. "
                   "Calls use your Claude Code plan's limits.")
        has_credential = bool(cli)
    else:
        provider = st.selectbox("Provider", list(KEY_MODELS), key="key-provider")
        model = st.selectbox("Model", KEY_MODELS[provider], key="key-model")
        api_key = st.text_input(f"{provider} API key", type="password", key="key-value")
        has_credential = bool(api_key)

    st.header("Loop")
    max_rounds = st.slider("Max rounds", 3, 25, 10)
    patience = st.slider("Stop after N rounds with no gain", 2, 10, 4)
    concurrency = st.slider("Parallel scenario calls", 1, 8, 4)

    st.header("Teams")
    teams_raw = st.text_area(
        "One per line", value="\n".join(golden.get("teams", [])), height=180,
        help="The allowed routing labels. Must match your golden set.",
    )
    teams = [t.strip() for t in teams_raw.splitlines() if t.strip()]

tab_skill, tab_data, tab_run, tab_out, tab_sessions = st.tabs(
    ["1 · Skill", "2 · Golden set", "3 · Run", "4 · Results", "5 · Sessions"]
)

# -- 1. Skill ----------------------------------------------------------------
with tab_skill:
    st.subheader("Starting skill")
    skill_md = st.text_area(
        "SKILL.md", value=_load(SKILL_PATH, ""), height=460, label_visibility="collapsed"
    )
    st.session_state["skill_md"] = skill_md

    with st.expander("No golden set yet? Generate scenarios from the skill"):
        st.caption(
            "Self-generated labels measure the model's opinion of correct routing, "
            "not your org's. Use this to bootstrap, then correct the labels by hand."
        )
        if st.button("Generate scenarios"):
            if not has_credential:
                st.error("Pick a model and sign in or add an API key in the sidebar.")
            elif not teams:
                st.error("Add your teams in the sidebar.")
            else:
                with st.spinner("Generating…"):
                    opt = TriageOptimizer(model=model, api_key=api_key)
                    gen = asyncio.run(opt.analyze_skill(skill_md, teams))
                st.session_state["gen"] = gen
                st.success(f"Generated {len(gen.get('scenarios', []))} scenarios. See tab 2.")

# -- 2. Golden set -----------------------------------------------------------
with tab_data:
    st.subheader("Golden set")
    st.caption("The optimizer can only get as good as these labels.")

    src = st.session_state.get("gen", golden)
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown("**Scenarios** — issue text + expected routing")
        scen_txt = st.text_area(
            "scenarios", value=json.dumps(src.get("scenarios", []), indent=2),
            height=420, label_visibility="collapsed",
        )
    with c2:
        st.markdown("**Evals** — what counts as correct")
        eval_txt = st.text_area(
            "evals", value=json.dumps(src.get("evals", []), indent=2),
            height=420, label_visibility="collapsed",
        )

    try:
        scenarios = json.loads(scen_txt)
        evals = json.loads(eval_txt)
        st.session_state["scenarios"] = scenarios
        st.session_state["evals"] = evals

        unknown = {s.get("expected_team") for s in scenarios} - set(teams)
        if unknown - {None}:
            st.warning(f"Labels not in the team list: {sorted(unknown - {None})}")
        else:
            st.success(f"{len(scenarios)} scenarios · {len(evals)} evals ready.")

        counts: dict = {}
        for s in scenarios:
            counts[s.get("expected_team", "?")] = counts.get(s.get("expected_team", "?"), 0) + 1
        st.caption("Label balance: " + " · ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON — {e}")

# -- 3. Run ------------------------------------------------------------------
with tab_run:
    st.subheader("Run the loop")
    ready = bool(has_credential and st.session_state.get("scenarios") and teams)
    if not ready:
        st.info("Need a model with a credential, a team list, and a golden set.")

    if st.button("Start optimization", type="primary", disabled=not ready):
        chart = st.empty()
        board = st.empty()
        events: list = []

        async def run():
            opt = TriageOptimizer(model=model, api_key=api_key, concurrency=concurrency)

            async def on_event(ev):
                events.append(ev)
                if ev["type"] == "baseline":
                    board.info(f"Baseline: **{ev['data']['score']}%** "
                               f"({ev['data']['passed']}/{ev['data']['total']} routed correctly)")
                elif ev["type"] == "round_result":
                    d = ev["data"]
                    rows = [f"Baseline · {events[0]['data']['score']}%"]
                    rows += [
                        f"Round {e['data']['round']} · {e['data']['score']}% · "
                        f"{'✅ kept' if e['data']['kept'] else '❌ discarded'} · "
                        f"{e['data']['description']}"
                        for e in events if e["type"] == "round_result"
                    ]
                    board.markdown("\n\n".join(rows))
                    hist = [events[0]["data"]["score"]] + [
                        e["data"]["score"] for e in events if e["type"] == "round_result"
                    ]
                    chart.line_chart({"routing accuracy %": hist})

            return await opt.optimize(
                skill_md=st.session_state["skill_md"],
                context={"teams": teams},
                scenarios=st.session_state["scenarios"],
                evals=st.session_state["evals"],
                max_rounds=max_rounds,
                patience=patience,
                callback=on_event,
            )

        with st.spinner("Optimizing — each round re-scores every scenario…"):
            try:
                st.session_state["result"] = asyncio.run(run())
            except Exception as e:  # surfaced rather than swallowed: usually auth/quota
                st.error(f"Optimization failed: {e}")

        if res := st.session_state.get("result"):
            delta = res["final_score"] - res["baseline_score"]
            st.success(f"{res['baseline_score']}% → {res['final_score']}% ({delta:+.1f} pts). See tab 4.")

# -- 4. Results --------------------------------------------------------------
with tab_out:
    res = st.session_state.get("result")
    if not res:
        st.info("Run the loop first.")
    else:
        a, b, c, d = st.columns(4)
        a.metric("Baseline", f"{res['baseline_score']}%")
        b.metric("Final", f"{res['final_score']}%",
                 delta=f"{res['final_score'] - res['baseline_score']:+.1f}")
        kept = sum(1 for m in res["mutation_log"] if m["kept"])
        c.metric("Mutations kept", f"{kept}/{len(res['mutation_log'])}")
        d.metric("Still failing", len(res["remaining_failures"]))

        st.line_chart({"routing accuracy %": res["score_history"]})

        st.subheader("Diff")
        diff = "\n".join(difflib.unified_diff(
            res["original_skill_md"].splitlines(),
            res["improved_skill_md"].splitlines(),
            fromfile="SKILL.md (before)", tofile="SKILL.md (after)", lineterm="",
        ))
        st.code(diff or "No change.", language="diff")
        st.download_button("Download improved SKILL.md", res["improved_skill_md"],
                           file_name="SKILL.md", mime="text/markdown", type="primary")

        st.subheader("What each strategy earned")
        stats = res.get("strategy_stats", {})
        if stats:
            st.dataframe(
                [{"strategy": k, "tried": v["total"], "kept": v["kept"]} for k, v in stats.items()],
                hide_index=True,
            )

        st.subheader("Round log")
        for m in res["mutation_log"]:
            icon = "✅" if m["kept"] else "❌"
            with st.expander(
                f"{icon} Round {m['round']} · {m['score_before']}% → {m['score_after']}% · "
                f"{m['description']}"
            ):
                st.markdown(f"**Strategy** `{m['strategy_type']}` → `{m['target_section']}`")
                st.markdown(f"**Diagnosis** {m['diagnosis']}")
                st.markdown(f"**Rationale** {m['reasoning']}")

        if res["remaining_failures"]:
            st.subheader("Still mis-routed")
            st.caption("These need a better rule, a clearer roster entry, or a corrected label.")
            for f in res["remaining_failures"]:
                st.markdown(
                    f"- **{f['name']}** — expected `{f['expected_team']}`, "
                    f"got `{f['predicted_team']}`  \n  ↳ _{f['agent_reasoning']}_"
                )


# -- 5. Sessions -------------------------------------------------------------
with tab_sessions:
    sessions_view.render()
