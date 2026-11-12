"""Tests for SkillOptimizer guards, pluggable scorers, min_gain, and holdouts."""

import asyncio
import json

import pytest

from adk_optimizer import (
    PARSE_ERROR,
    BaseScorer,
    CallableScorer,
    ExecutorScorer,
    Scorer,
    SkillOptimizer,
    _coerce_scorer,
    _normalize_score_result,
    is_parse_error,
    parse_json,
    split_holdout,
)


SKILL_V0 = "---\nname: demo\ndescription: demo skill\n---\n# Demo\nInitial instructions.\n"
SKILL_V1 = "---\nname: demo\ndescription: demo skill\n---\n# Demo\nImproved v1.\n"
SKILL_V2 = "---\nname: demo\ndescription: demo skill\n---\n# Demo\nImproved v2.\n"

SCENARIOS = [
    {"id": 1, "description": "s1", "input": "request 1"},
    {"id": 2, "description": "s2", "input": "request 2"},
]
EVALS = [
    {"id": 1, "name": "e1", "question": "check 1?"},
    {"id": 2, "name": "e2", "question": "check 2?"},
]


def run(coro):
    return asyncio.run(coro)


# -- 1. parse_json & _ask_json -----------------------------------------------


def test_parse_json_direct_fenced_and_raw_decode():
    assert parse_json('{"ok": true, "n": 3}') == {"ok": True, "n": 3}
    assert parse_json("[1, 2, 3]") == [1, 2, 3]

    fenced = 'Here is your output:\n```json\n{"results": [{"eval_id": 1, "passed": true}]}\n```\nDone.'
    assert parse_json(fenced) == {"results": [{"eval_id": 1, "passed": True}]}

    plain_fence = "```\n[10, 20]\n```"
    assert parse_json(plain_fence) == [10, 20]

    trailing = 'Sure! {"a": 1, "b": [2, 3]} — hope this helps!'
    assert parse_json(trailing) == {"a": 1, "b": [2, 3]}

    leading_bracket_noise = 'Note [section 1]: {"answer": "yes"} extra text'
    assert parse_json(leading_bracket_noise) == {"answer": "yes"}


@pytest.mark.parametrize("bad", ["", "   ", "not json at all", "{unclosed", "NaN", None])
def test_parse_json_raises_value_error_on_unparseable(bad):
    with pytest.raises(ValueError):
        parse_json(bad)


def test_ask_json_parse_errors_and_non_dict_guards(monkeypatch):
    opt = SkillOptimizer(api_key="test-key")
    replies = iter([
        "completely unparseable",
        "completely unparseable",
        "completely unparseable",
        '["unexpected", "list"]',
        '"unexpected string"',
        "123",
        '{"valid": true}',
    ])

    async def fake_ask(agent, prompt):
        return next(replies)

    monkeypatch.setattr(opt, "_ask", fake_ask)

    # No fallback -> raises ValueError
    with pytest.raises(ValueError):
        run(opt._ask_json(opt.executor, "p"))

    # Dict fallback -> returns copy with PARSE_ERROR=True without mutating fallback
    fallback = {"results": []}
    res = run(opt._ask_json(opt.executor, "p", fallback=fallback))
    assert is_parse_error(res)
    assert res == {"results": [], PARSE_ERROR: True}
    assert fallback == {"results": []}
    assert not is_parse_error(fallback)

    # Non-dict fallback -> returned as-is
    list_fb = ["fallback"]
    assert run(opt._ask_json(opt.executor, "p", fallback=list_fb)) == ["fallback"]

    # Non-dict JSON shapes when dict fallback is expected -> marked parse error
    for _ in range(3):
        non_dict_res = run(opt._ask_json(opt.executor, "p", fallback=fallback))
        assert is_parse_error(non_dict_res)
        assert fallback == {"results": []}

    # Valid dict -> not a parse error
    ok_res = run(opt._ask_json(opt.executor, "p", fallback=fallback))
    assert ok_res == {"valid": True}
    assert not is_parse_error(ok_res)


# -- 2. Malformed judge replies in ExecutorScorer / _score_skill -------------


@pytest.mark.parametrize(
    "judge_reply",
    [
        '{"results": ["x"]}',
        '{"results": null}',
        '"bad"',
        "not valid json",
        '{"no_results_key": 1}',
    ],
)
def test_score_skill_handles_malformed_judge_replies_fail_closed(monkeypatch, judge_reply):
    opt = SkillOptimizer(api_key="test-key")

    async def fake_ask(agent, prompt):
        if prompt.startswith("Execute this skill:"):
            return "generated skill output"
        return judge_reply

    monkeypatch.setattr(opt, "_ask", fake_ask)

    res = run(opt._score_skill(SKILL_V0, SCENARIOS, EVALS))
    assert res["passed"] == 0
    assert res["total"] == 4  # 2 scenarios * 2 evals
    assert res["pass_rate"] == 0.0
    assert res["parse_errors"] == 2  # 1 per scenario
    assert len(res["details"]) == 4
    assert len(res["failures"]) == 4
    assert all(
        d["passed"] is False
        and d["reason"] == "no verdict returned"
        and d.get("parse_error") is True
        for d in res["details"]
    )


def test_score_skill_rejects_non_bool_passed_and_missing_verdicts(monkeypatch):
    opt = SkillOptimizer(api_key="test-key")
    judge_replies = iter([
        # Scenario 1: eval 1 has string "true" (invalid), eval 2 has True (valid)
        json.dumps({
            "results": [
                {"eval_id": 1, "passed": "true", "reason": "string bool"},
                {"eval_id": 2, "passed": True, "reason": "real bool"},
            ]
        }),
        # Scenario 2: eval 1 passes cleanly, eval 2 verdict omitted
        json.dumps({
            "results": [
                {"eval_id": 1, "passed": True, "reason": "good"},
            ]
        }),
    ])

    async def fake_ask(agent, prompt):
        if prompt.startswith("Execute this skill:"):
            return "output"
        return next(judge_replies)

    monkeypatch.setattr(opt, "_ask", fake_ask)

    res = run(opt._score_skill(SKILL_V0, SCENARIOS, EVALS))
    assert res["total"] == 4
    assert res["passed"] == 2
    assert res["pass_rate"] == 50.0
    assert res["parse_errors"] == 2  # both scenarios had partial/malformed verdicts
    reasons = {(d["scenario_id"], d["eval_id"]): (d["passed"], d["reason"]) for d in res["details"]}
    assert reasons[(1, 1)] == (False, "no verdict returned")
    assert reasons[(1, 2)] == (True, "real bool")
    assert reasons[(2, 1)] == (True, "good")
    assert reasons[(2, 2)] == (False, "no verdict returned")
    parse_flags = {(d["scenario_id"], d["eval_id"]): d.get("parse_error") for d in res["details"]}
    assert parse_flags[(1, 1)] is True
    assert parse_flags[(2, 2)] is True
    assert parse_flags[(1, 2)] is None
    assert parse_flags[(2, 1)] is None


@pytest.mark.parametrize(
    "bad_eval_id",
    [[1], {"k": 1}, True],
)
def test_score_skill_rejects_invalid_or_unhashable_eval_id(monkeypatch, bad_eval_id):
    opt = SkillOptimizer(api_key="test-key")

    async def fake_ask(agent, prompt):
        if prompt.startswith("Execute this skill:"):
            return "output"
        return json.dumps({"results": [{"eval_id": bad_eval_id, "passed": True, "reason": "bad id"}]})

    monkeypatch.setattr(opt, "_ask", fake_ask)

    res = run(opt._score_skill(SKILL_V0, [{"id": 1, "input": "only"}], EVALS))
    assert res["total"] == 2
    assert res["passed"] == 0
    assert res["pass_rate"] == 0.0
    assert res["parse_errors"] == 1
    assert all(d.get("parse_error") is True for d in res["details"])
    assert all(d["reason"] == "no verdict returned" for d in res["details"])


def test_analyze_failures_excludes_parse_error_placeholders(monkeypatch):
    opt = SkillOptimizer(api_key="test-key")
    captured = {}

    async def fake_ask_json(agent, prompt, fallback=None):
        captured["prompt"] = prompt
        return {
            "diagnosis": "real issue",
            "mutation_strategy": "add_constraint",
            "target_section": "rules",
            "suggested_change": "tighten",
        }

    monkeypatch.setattr(opt, "_ask_json", fake_ask_json)
    details = [
        {"eval_id": 1, "passed": False, "parse_error": True, "reason": "no verdict returned"},
        {"eval_id": 2, "passed": False, "reason": "real failure"},
    ]

    run(
        opt._analyze_failures(
            SKILL_V0,
            SCENARIOS,
            EVALS,
            details,
            result={"pass_rate": 50.0, "passed": 1, "total": 2, "parse_errors": 1},
        )
    )
    assert '"eval_id": 2' in captured["prompt"]
    assert '"eval_id": 1' not in captured["prompt"]


def test_optimize_skips_round_when_only_parse_error_misses(monkeypatch):
    opt = SkillOptimizer(api_key="test-key")

    def noisy_scorer(skill_md, scenarios, evals):
        return {
            "pass_rate": 0.0,
            "passed": 0,
            "total": 2,
            "parse_errors": 1,
            "details": [
                {"eval_id": 1, "passed": False, "parse_error": True, "reason": "no verdict"},
                {"eval_id": 2, "passed": False, "parse_error": True, "reason": "no verdict"},
            ],
        }

    async def should_not_analyze(*args, **kwargs):
        raise AssertionError("diagnose should not run for parse-error-only misses")

    async def should_not_mutate(*args, **kwargs):
        raise AssertionError("mutator should not run for parse-error-only misses")

    monkeypatch.setattr(opt, "_analyze_failures", should_not_analyze)
    monkeypatch.setattr(opt, "_mutate_skill", should_not_mutate)

    events = []
    res = run(
        opt.optimize(
            {"SKILL.md": SKILL_V0},
            [{"id": 1, "input": "x"}],
            EVALS,
            max_rounds=1,
            scorer=noisy_scorer,
            callback=events.append,
        )
    )

    assert [m["outcome"] for m in res["mutation_log"]] == ["skipped"]
    assert res["mutation_log"][0]["description"] == "Scoring replies could not be parsed"
    assert res["mutation_log"][0]["parse_errors"] == 1
    exp = next(e for e in events if e["type"] == "experiment_result")["data"]
    assert exp["outcome"] == "skipped"
    assert exp["description"] == "Scoring replies could not be parsed"


# -- 3. min_gain -------------------------------------------------------------


def test_min_gain_validation_and_threshold(monkeypatch):
    opt = SkillOptimizer(api_key="test-key")

    with pytest.raises(ValueError):
        run(opt.optimize({"SKILL.md": SKILL_V0}, SCENARIOS, EVALS, min_gain=-0.1))

    scores_by_md = {
        SKILL_V0: {"pass_rate": 50.0, "passed": 2, "total": 4},
        SKILL_V1: {"pass_rate": 58.0, "passed": 2, "total": 4},  # +8.0 < 10.0 -> discard
        SKILL_V2: {"pass_rate": 65.0, "passed": 3, "total": 4},  # +15.0 >= 10.0 -> keep
    }
    mutations = iter([
        {"description": "small tweak", "reasoning": "r1", "new_skill_md": SKILL_V1},
        {"description": "big fix", "reasoning": "r2", "new_skill_md": SKILL_V2},
    ])

    async def fake_analyze(skill_md, scenarios, evals, details, mutation_log=None, result=None):
        return {
            "diagnosis": "needs improvement",
            "mutation_strategy": "add_constraint",
            "target_section": "rules",
            "suggested_change": "tighten",
        }

    async def fake_mutate(skill_md, analysis, context=""):
        return next(mutations)

    monkeypatch.setattr(opt, "_analyze_failures", fake_analyze)
    monkeypatch.setattr(opt, "_mutate_skill", fake_mutate)

    events = []
    res = run(
        opt.optimize(
            {"SKILL.md": SKILL_V0},
            SCENARIOS,
            EVALS,
            max_rounds=2,
            min_gain=10.0,
            scorer=lambda md, sc, ev: scores_by_md[md],
            callback=events.append,
        )
    )

    assert res["min_gain"] == 10.0
    assert res["baseline_score"] == 50.0
    assert res["final_score"] == 65.0
    assert res["improved_skill_md"] == SKILL_V2
    assert res["score_history"] == [50.0, 50.0, 65.0]
    assert [m["outcome"] for m in res["mutation_log"]] == ["discarded", "kept"]
    complete_event = next(e for e in events if e["type"] == "complete")
    assert complete_event["data"]["min_gain"] == 10.0


# -- 4. Skipped analyst/mutator rounds, unchanged, inconclusive --------------


def test_skipped_analyst_and_mutator_rounds_and_strategy_stats(monkeypatch):
    opt = SkillOptimizer(api_key="test-key")
    score_calls = []
    mutator_calls = 0

    def scorer_fn(md, sc, ev):
        score_calls.append(md)
        if md == SKILL_V0:
            return {"pass_rate": 50.0, "passed": 1, "total": 2, "failures": [{"eval_id": 1, "passed": False}]}
        return {"pass_rate": 80.0, "passed": 2, "total": 2}

    analyses = iter([
        {"diagnosis": "bad", "mutation_strategy": "add_example", PARSE_ERROR: True},
        {
            "diagnosis": "missing constraint",
            "mutation_strategy": "add_constraint",
            "target_section": "sec",
            "suggested_change": "fix",
        },
        {
            "diagnosis": "missing edge case",
            "mutation_strategy": "add_edge_case",
            "target_section": "sec",
            "suggested_change": "fix2",
        },
    ])
    mutations = iter([
        {"description": "Failed to parse", "new_skill_md": SKILL_V0, PARSE_ERROR: True},
        {"description": "Valid edit", "reasoning": "ok", "new_skill_md": SKILL_V1},
    ])

    async def fake_analyze(skill_md, scenarios, evals, details, mutation_log=None, result=None):
        return next(analyses)

    async def fake_mutate(skill_md, analysis, context=""):
        nonlocal mutator_calls
        mutator_calls += 1
        return next(mutations)

    monkeypatch.setattr(opt, "_analyze_failures", fake_analyze)
    monkeypatch.setattr(opt, "_mutate_skill", fake_mutate)

    events = []
    res = run(
        opt.optimize(
            {"SKILL.md": SKILL_V0},
            SCENARIOS,
            EVALS,
            max_rounds=3,
            scorer=scorer_fn,
            callback=events.append,
        )
    )

    # Round 1 skipped before mutator; Round 2 skipped before re-scoring; Round 3 kept
    assert mutator_calls == 2
    assert score_calls == [SKILL_V0, SKILL_V1]
    assert [m["outcome"] for m in res["mutation_log"]] == ["skipped", "skipped", "kept"]
    assert res["mutation_log"][0]["description"] == "Analyst reply could not be parsed"
    assert res["mutation_log"][1]["description"] == "Mutator reply could not be parsed"
    assert res["mutation_log"][0]["parse_errors"] == 1
    assert res["mutation_log"][1]["parse_errors"] == 1
    assert res["score_history"] == [50.0, 50.0, 50.0, 80.0]

    # _strategy_stats excludes skipped rounds
    assert res["strategy_stats"] == {"add_edge_case": {"total": 1, "kept": 1}}

    exp_events = [e["data"] for e in events if e["type"] == "experiment_result"]
    assert exp_events[0]["status"] == "skipped"
    assert exp_events[0]["outcome"] == "skipped"
    assert exp_events[0]["parse_errors"] == 1
    assert exp_events[1]["status"] == "skipped"
    assert exp_events[1]["outcome"] == "skipped"
    assert exp_events[2]["status"] == "kept"

    # tried_block also ignores skipped entries and caps at 6
    many_log = [
        {"round": i, "outcome": "skipped" if i % 2 == 0 else "discarded", "strategy_type": "s", "description": f"d{i}"}
        for i in range(1, 16)
    ]
    tried = BaseScorer.tried_block(many_log)
    assert "[skipped]" not in tried
    assert tried.count("- Round ") == 6
    assert "d15" in tried and "d3" not in tried


def test_unchanged_mutation_and_inconclusive_candidate_parse_errors(monkeypatch):
    opt = SkillOptimizer(api_key="test-key")
    score_calls = []

    def scorer_fn(md, sc, ev):
        score_calls.append(md)
        if md == SKILL_V0:
            return {"pass_rate": 40.0, "passed": 2, "total": 5, "parse_errors": 0}
        # Higher pass_rate, but introduced a parse error -> must be inconclusive!
        return {"pass_rate": 80.0, "passed": 4, "total": 5, "parse_errors": 1}

    async def fake_analyze(skill_md, scenarios, evals, details, mutation_log=None, result=None):
        return {
            "diagnosis": "d",
            "mutation_strategy": "restructure",
            "target_section": "t",
            "suggested_change": "c",
        }

    mutations = iter([
        {"description": "whitespace noop", "reasoning": "", "new_skill_md": f"  {SKILL_V0}\n\n"},
        {"description": "noisy candidate", "reasoning": "", "new_skill_md": SKILL_V1},
    ])

    async def fake_mutate(skill_md, analysis, context=""):
        return next(mutations)

    monkeypatch.setattr(opt, "_analyze_failures", fake_analyze)
    monkeypatch.setattr(opt, "_mutate_skill", fake_mutate)

    events = []
    res = run(
        opt.optimize(
            {"SKILL.md": SKILL_V0},
            SCENARIOS,
            EVALS,
            max_rounds=2,
            scorer=scorer_fn,
            callback=events.append,
        )
    )

    # Round 1 was unchanged so scorer_fn was NOT called for it; Round 2 was inconclusive
    assert score_calls == [SKILL_V0, SKILL_V1]
    assert [m["outcome"] for m in res["mutation_log"]] == ["unchanged", "inconclusive"]
    assert res["mutation_log"][0]["parse_errors"] == 0
    assert res["mutation_log"][1]["parse_errors"] == 1
    assert res["improved_skill_md"] == SKILL_V0
    assert res["final_score"] == 40.0
    assert res["score_history"] == [40.0, 40.0, 40.0]

    exp_events = [e["data"] for e in events if e["type"] == "experiment_result"]
    assert exp_events[0]["status"] == "unchanged"
    assert exp_events[0]["outcome"] == "unchanged"
    assert exp_events[1]["status"] == "inconclusive"
    assert exp_events[1]["outcome"] == "inconclusive"
    assert exp_events[1]["kept"] is False


# -- 5. split_holdout & holdout isolation / regression / reuse ---------------


def test_split_holdout_validation_order_and_determinism():
    items = [{"id": i} for i in range(1, 7)]

    for bad_frac in (-0.5, 1.0, 1.2):
        with pytest.raises(ValueError):
            split_holdout(items, bad_frac)

    assert split_holdout(items, 0.0) == (items, [])
    assert split_holdout([{"id": 1}], 0.5) == ([{"id": 1}], [])
    assert split_holdout([], 0.5) == ([], [])

    train1, hold1 = split_holdout(items, 0.34, seed=42)
    train2, hold2 = split_holdout(items, 0.34, seed=42)
    assert (train1, hold1) == (train2, hold2)
    assert len(hold1) == 2
    assert len(train1) == 4
    # Relative order preserved in both partitions
    assert [x["id"] for x in train1] == sorted(x["id"] for x in train1)
    assert [x["id"] for x in hold1] == sorted(x["id"] for x in hold1)
    assert set(x["id"] for x in train1).isdisjoint(x["id"] for x in hold1)

    # Never empties train even when fraction rounds to len(scenarios)
    t_two, h_two = split_holdout([{"id": 1}, {"id": 2}], 0.9, seed=0)
    assert len(t_two) == 1 and len(h_two) == 1


def test_holdout_isolation_regression_detection_and_fraction(monkeypatch):
    opt = SkillOptimizer(api_key="test-key")
    train_sc = [{"id": 1, "input": "train-1"}, {"id": 2, "input": "train-2"}]
    holdout_sc = [{"id": 99, "input": "secret-holdout"}]

    with pytest.raises(ValueError):
        run(
            opt.optimize(
                {"SKILL.md": SKILL_V0},
                train_sc,
                EVALS,
                holdout=holdout_sc,
                holdout_fraction=0.5,
            )
        )

    diagnosed_scenarios = []

    def overfit_scorer(md, scenarios, evals):
        ids = [s["id"] for s in scenarios]
        if ids == [99]:
            # V0 passes holdout (100%), overfitted V1 regresses on holdout (0%)
            rate = 100.0 if md == SKILL_V0 else 0.0
            return {"pass_rate": rate, "passed": int(rate == 100.0), "total": 1}
        rate = 50.0 if md == SKILL_V0 else 90.0
        return {"pass_rate": rate, "passed": 1, "total": 2}

    async def fake_analyze(skill_md, scenarios, evals, details, mutation_log=None, result=None):
        diagnosed_scenarios.append([s["id"] for s in scenarios])
        return {
            "diagnosis": "overfit train",
            "mutation_strategy": "add_example",
            "target_section": "examples",
            "suggested_change": "add train example",
        }

    async def fake_mutate(skill_md, analysis, context=""):
        return {"description": "overfit edit", "reasoning": "", "new_skill_md": SKILL_V1}

    monkeypatch.setattr(opt, "_analyze_failures", fake_analyze)
    monkeypatch.setattr(opt, "_mutate_skill", fake_mutate)

    events = []
    res = run(
        opt.optimize(
            {"SKILL.md": SKILL_V0},
            train_sc,
            EVALS,
            max_rounds=1,
            holdout=holdout_sc,
            scorer=overfit_scorer,
            callback=events.append,
        )
    )

    # Analyst never saw holdout scenario 99
    assert diagnosed_scenarios == [[1, 2]]
    assert res["final_score"] == 90.0
    assert res["holdout"] == {
        "baseline": 100.0,
        "final": 0.0,
        "total": 1,
        "regressed": True,
        "parse_errors": 0,
    }
    holdout_event = next(e for e in events if e["type"] == "holdout")
    assert holdout_event["data"] == res["holdout"]

    # Also verify holdout_fraction splits automatically
    all_four = [{"id": i, "input": f"s{i}"} for i in range(1, 5)]
    res_frac = run(
        opt.optimize(
            {"SKILL.md": SKILL_V0},
            all_four,
            EVALS,
            max_rounds=1,
            holdout_fraction=0.25,
            scorer=lambda md, sc, ev: {"pass_rate": 50.0 if md == SKILL_V0 else 80.0, "total": len(sc)},
        )
    )
    assert res_frac["holdout"]["total"] == 1
    assert res_frac["holdout"]["regressed"] is False


def test_holdout_reuses_baseline_score_when_skill_unchanged(monkeypatch):
    opt = SkillOptimizer(api_key="test-key")
    holdout_calls = 0

    def counting_scorer(md, scenarios, evals):
        nonlocal holdout_calls
        if scenarios[0]["id"] == 99:
            holdout_calls += 1
            return {"pass_rate": 75.0, "passed": 3, "total": 4}
        # Candidate does not improve -> discarded -> current_md stays SKILL_V0
        return {"pass_rate": 50.0 if md == SKILL_V0 else 40.0, "passed": 2, "total": 4}

    async def fake_analyze(skill_md, scenarios, evals, details, mutation_log=None, result=None):
        return {
            "diagnosis": "d",
            "mutation_strategy": "add_constraint",
            "target_section": "s",
            "suggested_change": "c",
        }

    async def fake_mutate(skill_md, analysis, context=""):
        return {"description": "worse edit", "reasoning": "", "new_skill_md": SKILL_V1}

    monkeypatch.setattr(opt, "_analyze_failures", fake_analyze)
    monkeypatch.setattr(opt, "_mutate_skill", fake_mutate)

    res = run(
        opt.optimize(
            {"SKILL.md": SKILL_V0},
            [{"id": 1, "input": "t1"}],
            EVALS,
            max_rounds=1,
            holdout=[{"id": 99, "input": "h1"}],
            scorer=counting_scorer,
        )
    )

    assert res["improved_skill_md"] == SKILL_V0
    assert holdout_calls == 1  # Scored once at start and reused at end
    assert res["holdout"] == {
        "baseline": 75.0,
        "final": 75.0,
        "total": 1,
        "regressed": False,
        "parse_errors": 0,
    }


# -- 6. Custom BaseScorer veto, callable scorers, and early convergence ------


def test_custom_base_scorer_improves_veto_context_and_extra_results(monkeypatch):
    class SafetyVetoScorer(BaseScorer):
        kind = "trigger"

        async def score(self, optimizer, skill_md, scenarios, evals):
            if skill_md == SKILL_V0:
                return {"pass_rate": 50.0, "passed": 2, "total": 4, "false_positives": 0}
            if skill_md == SKILL_V1:
                # Higher pass_rate, but introduces false positives -> vetoed!
                return {"pass_rate": 90.0, "passed": 4, "total": 4, "false_positives": 2}
            return {"pass_rate": 80.0, "passed": 3, "total": 4, "false_positives": 0}

        def mutation_context(self) -> str:
            return "Preserve precision: avoid overly broad trigger rules."

        def improves(self, candidate: dict, best: dict, min_gain: float = 0.0) -> bool:
            if candidate.get("false_positives", 0) > best.get("false_positives", 0):
                return False
            return super().improves(candidate, best, min_gain)

        def extra_results(self, best: dict) -> dict:
            return {"false_positives": best.get("false_positives", 0), "scorer_kind": self.kind}

    scorer = SafetyVetoScorer()
    assert isinstance(scorer, Scorer)
    assert isinstance(ExecutorScorer(), Scorer)

    opt = SkillOptimizer(api_key="test-key", scorer=scorer)
    seen_prompts = []

    async def fake_ask_json(agent, prompt, fallback=None):
        seen_prompts.append((agent.name, prompt))
        if agent.name == "analyst":
            return {
                "diagnosis": "fix trigger",
                "mutation_strategy": "add_constraint",
                "target_section": "frontmatter",
                "suggested_change": "refine",
            }
        # Mutator: round 1 -> SKILL_V1 (vetoed), round 2 -> SKILL_V2 (kept)
        target_md = SKILL_V1 if sum(1 for n, _ in seen_prompts if n == "mutator") == 1 else SKILL_V2
        return {"description": "edit", "reasoning": "r", "new_skill_md": target_md}

    monkeypatch.setattr(opt, "_ask_json", fake_ask_json)

    events = []
    res = run(
        opt.optimize(
            {"SKILL.md": SKILL_V0},
            SCENARIOS,
            EVALS,
            max_rounds=2,
            callback=events.append,
        )
    )

    assert [m["outcome"] for m in res["mutation_log"]] == ["discarded", "kept"]
    assert res["improved_skill_md"] == SKILL_V2
    assert res["final_score"] == 80.0
    assert res["false_positives"] == 0
    assert res["scorer_kind"] == "trigger"
    mutator_prompts = [p for name, p in seen_prompts if name == "mutator"]
    assert all("Preserve precision: avoid overly broad trigger rules." in p for p in mutator_prompts)
    complete_event = next(e for e in events if e["type"] == "complete")
    assert complete_event["data"]["false_positives"] == 0
    assert complete_event["data"]["scorer_kind"] == "trigger"


def test_callable_scorers_and_normalize_score_result():
    opt = SkillOptimizer(api_key="test-key")

    async def async_fn(skill_md, scenarios, evals):
        return {"passed": 3, "total": 4}

    def sync_fn(skill_md, scenarios, evals):
        return {"pass_rate": 62.5}

    assert isinstance(_coerce_scorer(async_fn), CallableScorer)
    r_async = run(opt.score(SKILL_V0, SCENARIOS, EVALS, scorer=async_fn))
    assert r_async == {
        "pass_rate": 75.0,
        "passed": 3,
        "total": 4,
        "per_eval": [],
        "details": [],
        "failures": [],
        "parse_errors": 0,
    }

    r_sync = run(opt.score(SKILL_V0, SCENARIOS, EVALS, scorer=sync_fn))
    assert r_sync["pass_rate"] == 62.5
    for key in ("pass_rate", "passed", "total", "per_eval", "details", "failures", "parse_errors"):
        assert key in r_sync

    norm = _normalize_score_result({
        "details": [{"eval_id": 1, "passed": True}, {"eval_id": 2, "passed": False}],
    })
    assert norm["passed"] == 1
    assert norm["total"] == 2
    assert norm["pass_rate"] == 50.0
    assert len(norm["failures"]) == 1


def test_normalize_score_result_rejects_invalid_pass_rate_and_missing_total():
    with pytest.raises(ValueError, match="pass_rate must be between 0 and 100"):
        _normalize_score_result({"pass_rate": 105.0})
    with pytest.raises(ValueError, match="pass_rate must be between 0 and 100"):
        _normalize_score_result({"pass_rate": -1.0})
    with pytest.raises(ValueError, match="pass_rate must be between 0 and 100"):
        _normalize_score_result({"pass_rate": float("nan")})
    with pytest.raises(ValueError, match="pass_rate must be between 0 and 100"):
        _normalize_score_result({"pass_rate": float("nan"), "total": 4})
    with pytest.raises(ValueError, match="total is required when passed is provided without pass_rate"):
        _normalize_score_result({"passed": 3})


def test_callable_aggregate_only_scorer_still_invokes_analyst(monkeypatch):
    opt = SkillOptimizer(api_key="test-key")
    seen_agents = []

    async def fake_ask_json(agent, prompt, fallback=None):
        seen_agents.append(agent.name)
        if agent.name == "analyst":
            assert "Aggregate score summary" in prompt
            return {
                "diagnosis": "aggregate score is low",
                "mutation_strategy": "add_constraint",
                "target_section": "rules",
                "suggested_change": "tighten constraints",
            }
        return {"description": "noop", "reasoning": "", "new_skill_md": SKILL_V0}

    monkeypatch.setattr(opt, "_ask_json", fake_ask_json)

    run(
        opt.optimize(
            {"SKILL.md": SKILL_V0},
            SCENARIOS,
            EVALS,
            max_rounds=1,
            scorer=lambda md, sc, ev: {"pass_rate": 40.0},
        )
    )

    assert "analyst" in seen_agents
    assert "mutator" in seen_agents


def test_early_convergence_stops_loop_only_when_clean(monkeypatch):
    opt = SkillOptimizer(api_key="test-key")
    analyze_calls = 0

    async def fake_analyze(skill_md, scenarios, evals, details, mutation_log=None, result=None):
        nonlocal analyze_calls
        analyze_calls += 1
        return {
            "diagnosis": "fix last failure",
            "mutation_strategy": "add_constraint",
            "target_section": "rules",
            "suggested_change": "fix",
        }

    async def fake_mutate(skill_md, analysis, context=""):
        return {"description": "reach 100%", "reasoning": "", "new_skill_md": SKILL_V1}

    monkeypatch.setattr(opt, "_analyze_failures", fake_analyze)
    monkeypatch.setattr(opt, "_mutate_skill", fake_mutate)

    # Case 1: Baseline is 50%, Round 1 reaches 100% cleanly -> converges at start of Round 2
    events = []
    res = run(
        opt.optimize(
            {"SKILL.md": SKILL_V0},
            SCENARIOS,
            EVALS,
            max_rounds=5,
            scorer=lambda md, sc, ev: {
                "pass_rate": 50.0 if md == SKILL_V0 else 100.0,
                "passed": 2 if md == SKILL_V0 else 4,
                "total": 4,
                "parse_errors": 0,
            },
            callback=events.append,
        )
    )
    assert analyze_calls == 1
    assert len(res["mutation_log"]) == 1
    assert res["final_score"] == 100.0
    assert {"type": "converged", "data": {"round": 2}} in events

    # Case 2: 100% pass_rate WITH parse_errors > 0 must NOT converge early
    events_noisy = []
    run(
        opt.optimize(
            {"SKILL.md": SKILL_V0},
            SCENARIOS,
            EVALS,
            max_rounds=1,
            scorer=lambda md, sc, ev: {
                "pass_rate": 100.0,
                "passed": 4,
                "total": 4,
                "parse_errors": 1,
            },
            callback=events_noisy.append,
        )
    )
    assert not any(e["type"] == "converged" for e in events_noisy)
    assert analyze_calls == 2


def test_callable_aggregate_only_full_pass_converges_round_1_and_empty_evals_do_not(monkeypatch):
    opt = SkillOptimizer(api_key="k")
    mutator_calls = 0

    async def fake_ask_json(agent, prompt, fallback=None):
        nonlocal mutator_calls
        if agent.name == "mutator":
            mutator_calls += 1
        return {"description": "noop", "reasoning": "", "new_skill_md": SKILL_V0}

    monkeypatch.setattr(opt, "_ask_json", fake_ask_json)

    events = []
    res = run(
        opt.optimize(
            {"SKILL.md": SKILL_V0},
            SCENARIOS,
            EVALS,
            max_rounds=3,
            scorer=lambda md, sc, ev: {"pass_rate": 100.0},
            callback=events.append,
        )
    )

    assert res["mutation_log"] == []
    assert mutator_calls == 0
    assert {"type": "converged", "data": {"round": 1}} in events
    assert not any(e["type"] == "experiment_start" for e in events)

    events_empty = []
    res_empty = run(
        opt.optimize(
            {"SKILL.md": SKILL_V0},
            SCENARIOS,
            EVALS,
            max_rounds=1,
            scorer=lambda md, sc, ev: {"total": 0},
            callback=events_empty.append,
        )
    )

    assert res_empty["final_score"] == 0.0
    assert len(res_empty["mutation_log"]) == 1
    assert res_empty["mutation_log"][0]["outcome"] == "unchanged"
    assert mutator_calls == 1
    assert not any(e["type"] == "converged" for e in events_empty)
    baseline_empty = next(e for e in events_empty if e["type"] == "baseline")
    assert baseline_empty["data"]["score"] == 0.0
    assert baseline_empty["data"]["total"] == 0
