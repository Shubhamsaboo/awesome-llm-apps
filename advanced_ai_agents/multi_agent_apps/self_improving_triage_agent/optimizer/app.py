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
import skill_paths  # noqa: E402  (locates agent_skills/triage-issue)
from skill_optimizer import CLAUDE_CODE_PREFIX, SkillOptimizer, split_holdout  # noqa: E402  (imports LiteLLM safely)
import sessions_view  # noqa: E402
import telemetry  # noqa: E402
from rca_scorer import RcaScorer, generation_cases  # noqa: E402
from routing_scorer import RoutingScorer, generate_scenarios  # noqa: E402

SKILL_PATH = skill_paths.SKILL_MD
GOLDEN_PATH = skill_paths.ROUTING_GOLDEN
RCA_GOLDEN_PATH = skill_paths.RCA_GOLDEN
RUBRIC_PATH = skill_paths.RCA_RUBRIC
ROUTING = "Team assignment"
RCA = "RCA evaluation"
OUTCOME_ICONS = {"kept": "✅", "discarded": "❌", "inconclusive": "⚠️",
                 "skipped": "⏭️", "unchanged": "➖"}

CLAUDE_CODE = "Claude Code"
API_KEY = "API key"
BACKENDS = [API_KEY, CLAUDE_CODE]
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
    except (OSError, json.JSONDecodeError) as exc:
        st.error(f"Could not load {os.path.basename(path)}: {exc}")
        return default


def _records(text: str, label: str) -> list:
    records = json.loads(text)
    if not isinstance(records, list) or not records:
        raise ValueError(f"{label} must be a non-empty JSON array.")
    ids = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError(f"Each entry in {label} must be an object.")
        ident = record.get("id")
        if not isinstance(ident, (str, int)) or isinstance(ident, bool) or ident == "":
            raise ValueError(f"Each entry in {label} needs a string or integer id.")
        if ident in ids:
            raise ValueError(f"Duplicate id in {label}: {ident}")
        ids.add(ident)
    return records


telemetry.init()
golden = _load(GOLDEN_PATH, {"teams": [], "scenarios": [], "evals": []})
rca_golden = _load(RCA_GOLDEN_PATH, {"cases": []})
rubric = _load(RUBRIC_PATH, {})

st.title("🔀 Self-Improving Triage Agent")
st.caption(
    "Evaluate and improve your skill against separate golden sets for team assignment "
    "and evidence-grounded RCA. Only score-improving edits survive."
)

# -- Sidebar -----------------------------------------------------------------
with st.sidebar:
    mode = st.segmented_control(
        "Evaluation", [ROUTING, RCA], default=ROUTING, required=True, key="evaluation-mode",
    )
    is_rca = mode == RCA
    mode_key = "rca" if is_rca else "routing"
    result_key = f"{mode_key}_result"
    score_label = "RCA objective %" if is_rca else "routing accuracy %"
    st.header("Model")
    backend = st.segmented_control(
        "Backend", BACKENDS, default=API_KEY, required=True, key="backend",
        help="Use a provider API key for LiteLLM, or compare against your Claude Code login. "
             "Every run is traced in the Sessions tab.",
    )
    api_key = None
    if backend == CLAUDE_CODE:
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
    min_gain = st.slider(
        "Minimum gain to keep an edit (points)", 0.0, 20.0, 5.0, 0.5, key="min-gain",
        help="An edit must raise the objective by at least this much. On small golden "
             "sets one flipped case moves the score a lot, so 0 keeps lucky runs.",
    )
    holdout_pct = st.slider(
        "Hold out from optimization (%)", 0, 50, 25, 5, key="holdout-pct",
        help="These cases never decide which edit is kept. They are scored for the "
             "starting and final skill only, so overfitting shows up as a drop.",
    )

    teams_raw = st.session_state.get("team_text", "\n".join(golden.get("teams", [])))
    if is_rca:
        st.header("RCA scoring")
        profiles = list(rubric.get("profiles", {}))
        if not profiles:
            st.error("The RCA rubric has no scoring profiles.")
            st.stop()
        profile = st.selectbox(
            "Profile", profiles, index=profiles.index(rubric["default_profile"]),
            key="rca-profile",
        )
        judge_runs = st.slider("Judge runs per case", 1, 5, 1, key="rca-judge-runs")
        st.caption(rubric["profiles"][profile]["description"])
    else:
        st.header("Teams")
        teams_raw = st.text_area(
            "One per line", value=teams_raw, height=180, key="routing-teams",
            help="The allowed routing labels. Must match your golden set.",
        )
        st.session_state["team_text"] = teams_raw
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

    with st.expander("Generate team-assignment scenarios from the skill"):
        st.caption(
            "Self-generated labels measure the model's opinion of correct routing, "
            "not your org's. Use this to bootstrap, then correct the labels by hand."
        )
        if st.button("Generate scenarios", disabled=is_rca):
            if not has_credential:
                st.error("Pick a model and sign in or add an API key in the sidebar.")
            elif not teams:
                st.error("Add your teams in the sidebar.")
            else:
                with st.spinner("Generating…"):
                    opt = SkillOptimizer(model=model, api_key=api_key)
                    gen = asyncio.run(generate_scenarios(opt, skill_md, teams))
                st.session_state["routing_scenarios_text"] = json.dumps(gen.get("scenarios", []), indent=2)
                st.session_state["routing_evals_text"] = json.dumps(gen.get("evals", []), indent=2)
                st.success(f"Generated {len(gen.get('scenarios', []))} scenarios. See tab 2.")

# -- 2. Golden set -----------------------------------------------------------
scenarios, evals, scorer = [], [], None
data_valid = False
with tab_data:
    st.subheader(f"{mode} golden set")
    st.caption("The optimizer can only get as good as these labels.")

    if is_rca:
        st.caption(
            "Loaded from agent_skills/triage-issue/references/rca-golden-set.json. The "
            "skill writes a fresh RCA from each case's evidence or ticket and intake. "
            "The documented root cause is shown only to the judge, never the RCA writer. "
            "Stored sample RCAs and human scores are for judge calibration, not "
            "generation targets."
        )
        initial_cases = generation_cases(rca_golden)
        scen_txt = st.text_area(
            "RCA cases",
            value=st.session_state.get("rca_cases_text", json.dumps(initial_cases, indent=2)),
            height=420, key="rca-cases-editor",
        )
        st.session_state["rca_cases_text"] = scen_txt
        scorer = RcaScorer(rubric, profile=profile, judge_runs=judge_runs)
        with st.expander("RCA evaluation rubric"):
            st.json(rubric)
    else:
        st.caption("Loaded from agent_skills/triage-issue/references/golden_set.json: "
                   "tickets and their expected owning teams.")
        c1, c2 = st.columns([3, 2])
        with c1:
            st.markdown("**Scenarios** — issue text + expected routing")
            scen_txt = st.text_area(
                "scenarios",
                value=st.session_state.get("routing_scenarios_text", json.dumps(golden.get("scenarios", []), indent=2)),
                height=420, label_visibility="collapsed",
            )
            st.session_state["routing_scenarios_text"] = scen_txt
        with c2:
            st.markdown("**Evals** — what counts as correct")
            eval_txt = st.text_area(
                "evals",
                value=st.session_state.get("routing_evals_text", json.dumps(golden.get("evals", []), indent=2)),
                height=420, label_visibility="collapsed",
            )
            st.session_state["routing_evals_text"] = eval_txt

    try:
        scenarios = _records(scen_txt, "RCA cases" if is_rca else "Scenarios")
        if is_rca:
            for case in scenarios:
                expected = case.get("expected_correctness")
                if expected not in {"correct", "partially_correct", "insufficient_evidence"}:
                    raise ValueError(
                        f"Case {case['id']}: expected_correctness must be correct, "
                        "partially_correct, or insufficient_evidence for a generated RCA."
                    )
                if not isinstance(case.get("evidence"), (dict, type(None))):
                    raise ValueError(f"Case {case['id']}: evidence must be an object or null.")
                if not case.get("evidence") and not (
                    isinstance(case.get("ticket"), str) and case["ticket"].strip()
                ):
                    raise ValueError(f"Case {case['id']}: supply an evidence bundle or ticket.")
                if case.get("intake") is not None and not isinstance(case["intake"], dict):
                    raise ValueError(f"Case {case['id']}: intake must be an object.")
                if expected != "insufficient_evidence" and not (
                    isinstance(case.get("true_root_cause"), str) and case["true_root_cause"].strip()
                ):
                    raise ValueError(f"Case {case['id']}: supply the documented true_root_cause.")
            st.success(f"{len(scenarios)} RCA cases ready · profile: {profile}.")
        else:
            evals = _records(eval_txt, "Evals")
            for scenario in scenarios:
                if not isinstance(scenario.get("input"), str) or not scenario["input"].strip():
                    raise ValueError(f"Scenario {scenario['id']}: supply non-empty input text.")
                if scenario.get("expected_team") not in teams:
                    raise ValueError(f"Scenario {scenario['id']}: expected_team must be in the team list.")
            scorer = RoutingScorer(teams, evals)
            st.success(f"{len(scenarios)} scenarios · {len(evals)} evals ready.")
            counts: dict = {}
            for scenario in scenarios:
                team = scenario["expected_team"]
                counts[team] = counts.get(team, 0) + 1
            st.caption("Label balance: " + " · ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
        data_valid = True
    except (ValueError, TypeError) as e:
        st.error(f"Invalid golden set — {e}")

# -- 3. Run ------------------------------------------------------------------
with tab_run:
    st.subheader(f"Run {mode.lower()}")
    if is_rca:
        st.caption(
            "Correctness and quality are reported separately. Optimization uses "
            "60% correctness + 40% quality; invented citations or lower grounding veto an edit."
        )
    ready = bool(has_credential and data_valid and skill_md.strip())
    if not ready:
        st.info("Need a model with a credential, a non-empty skill, and a valid golden set.")

    evaluate = st.button("Evaluate skill", disabled=not ready,
                         help="Score the current skill once, without proposing edits.")
    optimize = st.button("Start optimization", type="primary", disabled=not ready)
    if evaluate or optimize:
        st.session_state.pop(result_key, None)
        chart = st.empty()
        board = st.empty()
        events: list = []
        history: list = []

        async def run():
            opt = SkillOptimizer(model=model, api_key=api_key, concurrency=concurrency)
            # Evaluate scores every case; optimization holds some out so the
            # final skill is also measured on cases that never steered it.
            train, held = (scenarios, []) if evaluate else split_holdout(scenarios, holdout_pct / 100)

            async def on_event(ev):
                events.append(ev)
                if ev["type"] == "baseline":
                    history.append(ev["data"]["score"])
                    outcome = "target verdicts matched" if is_rca else "routed correctly"
                    held_note = f" · {len(held)} held out" if held else ""
                    board.info(f"Baseline: **{ev['data']['score']}%** "
                               f"({ev['data']['passed']}/{ev['data']['total']} {outcome}{held_note})")
                elif ev["type"] == "round_result":
                    d = ev["data"]
                    rows = [f"Baseline · {events[0]['data']['score']}%"]
                    rows += [
                        f"Round {e['data']['round']} · {e['data']['score']}% · "
                        f"{OUTCOME_ICONS.get(e['data']['outcome'], '')} {e['data']['outcome']} · "
                        f"{e['data']['description']}"
                        for e in events if e["type"] == "round_result"
                    ]
                    board.markdown("\n\n".join(rows))
                    history.append(d["score"] if d["kept"] else history[-1])
                    chart.line_chart({score_label: history})

            return await opt.optimize(
                st.session_state["skill_md"], scorer, train, holdout=held,
                max_rounds=0 if evaluate else max_rounds,
                patience=patience, min_gain=min_gain, callback=on_event,
            )

        with st.spinner("Evaluating skill…" if evaluate else "Optimizing — each round re-scores every scenario…"):
            try:
                st.session_state[result_key] = asyncio.run(run())
            except Exception as e:  # surfaced rather than swallowed: usually auth/quota
                st.error(f"{mode} run failed: {e}")

        if res := st.session_state.get(result_key):
            delta = res["final_score"] - res["baseline_score"]
            st.success(f"{res['baseline_score']}% → {res['final_score']}% ({delta:+.1f} pts). See tab 4.")

# -- 4. Results --------------------------------------------------------------
with tab_out:
    res = st.session_state.get(result_key)
    if not res:
        st.info(f"Evaluate or optimize {mode.lower()} first.")
    else:
        a, b, c, d = st.columns(4)
        a.metric("Baseline", f"{res['baseline_score']}%")
        b.metric("Final", f"{res['final_score']}%",
                 delta=f"{res['final_score'] - res['baseline_score']:+.1f}")
        kept = sum(1 for m in res["mutation_log"] if m["kept"])
        c.metric("Mutations kept", f"{kept}/{len(res['mutation_log'])}")
        d.metric("Still failing", len(res["remaining_failures"]))

        st.line_chart({score_label: res["score_history"]})

        if res.get("parse_errors"):
            st.warning(f"{res['parse_errors']} model replies could not be parsed while scoring "
                       "the final skill and were counted as failures. Rerun before trusting "
                       "the score.", icon=":material/warning:")
        if h := res.get("holdout"):
            a, b = st.columns(2)
            a.metric(f"Held-out cases ({h['total']}), start", f"{h['baseline']}%")
            b.metric("Held-out cases, final", f"{h['final']}%",
                     delta=f"{h['final'] - h['baseline']:+.1f}")
            if h["regressed"]:
                st.warning("The edits lowered the score on held-out cases: they likely fit "
                           "the training cases rather than generalize. Review before adopting.",
                           icon=":material/trending_down:")
        if is_rca:
            a, b, c = st.columns(3)
            a.metric("Correctness", f"{res['correctness_pct']}%")
            b.metric("Quality", f"{res['quality_pct']}%")
            grounding = res["grounding_pct"]
            c.metric("Grounding", f"{grounding}%" if grounding is not None else "N/A")
            if res["fabricated"]:
                st.error(f"{len(res['fabricated'])} cases contain fabricated citations. Not safe to hand off.")
            if res["overconfident"]:
                st.warning(f"{len(res['overconfident'])} cases concluded without sufficient evidence.")
            st.subheader("RCA reports and scores")
            st.download_button(
                "Download RCA evaluation", json.dumps(res["case_results"], indent=2),
                file_name="rca-evaluation.json", mime="application/json",
            )
            for case in res["case_results"]:
                with st.expander(
                    f"{case['case_id']} · {case['correctness']} · quality {case['quality']}%"
                ):
                    st.caption(f"Expected: {case['expected_correctness']}")
                    st.markdown(case["rca"])
                    st.json({key: value for key, value in case.items() if key != "rca"})

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
            with st.expander(
                f"{OUTCOME_ICONS.get(m['outcome'], '')} Round {m['round']} · {m['outcome']} · "
                f"{m['score_before']}% → {m['score_after']}% · {m['description']}"
            ):
                st.markdown(f"**Strategy** `{m['strategy_type']}` → `{m['target_section']}`")
                st.markdown(f"**Diagnosis** {m['diagnosis']}")
                st.markdown(f"**Rationale** {m['reasoning']}")
                if m["outcome"] == "inconclusive":
                    st.caption(f"Not kept: {m['parse_errors']} unparseable model replies "
                               "while scoring this edit.")

        if res["remaining_failures"]:
            if is_rca:
                st.subheader("RCA checks still failing")
                for failure in res["remaining_failures"]:
                    with st.expander(failure["case_id"]):
                        st.json(failure)
            else:
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
