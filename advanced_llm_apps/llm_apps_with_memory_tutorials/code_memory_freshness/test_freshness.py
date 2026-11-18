"""Offline checks of evidence routing, immutable anchors and the interactive app."""

import json
from dataclasses import replace

import pytest

import freshness_lab as lab

CASES = json.loads((lab.HERE / "cases.json").read_text())


@pytest.mark.parametrize("key", CASES)
def test_real_git_snapshots_detect_each_teaching_case(tmp_path, key):
    case = CASES[key]
    note = lab.prepare_case(case, tmp_path / "repo")
    state = lab.inspect_note(tmp_path / "repo", note)
    assert state["state"] == case["expected_state"]
    assert note.commit and note.file_blob and note.code
    if key == "changed_valid":
        assert state["target"]["shape"] != note.shape  # no blanket invalidation
    if key == "dependency_changed":
        assert state["target"]["code"] == note.code  # unchanged function is not enough
    if key == "moved":
        assert state["target"]["path"] == "service.py"
        assert state["target"]["symbol"] == "charge_cached"


def test_ambiguous_matching_bodies_are_not_arbitrarily_resolved(tmp_path):
    case = CASES["moved"]
    note = lab.prepare_case(case, tmp_path / "repo")
    repo = tmp_path / "repo"
    (repo / "duplicate.py").write_text((repo / "service.py").read_text())
    state = lab.inspect_note(repo, note)
    assert state["state"] == "unresolved" and state["target"] is None
    assert len(state["candidates"]) == 2


def test_exact_target_wins_over_a_similar_function_elsewhere(tmp_path):
    repo = tmp_path / "repo"
    note = lab.prepare_case(CASES["unchanged"], repo)
    (repo / "duplicate.py").write_text((repo / "payments.py").read_text())
    state = lab.inspect_note(repo, note)
    assert state["state"] == "context_changed"
    assert state["target"]["path"] == "payments.py"


def test_source_reader_refuses_an_escaping_symlink(tmp_path):
    repo = tmp_path / "repo"
    lab.prepare_case(CASES["unchanged"], repo)
    outside = tmp_path / "outside.py"
    outside.write_text("private_data = True\n")
    (repo / "escape.py").symlink_to(outside)
    with pytest.raises(ValueError):
        lab.sources(repo)


def test_store_keeps_original_anchor_and_every_separate_check(tmp_path):
    repo = tmp_path / "repo"
    note = lab.prepare_case(CASES["unchanged"], repo)
    store = lab.Store(str(tmp_path / "memory.sqlite3"))
    try:
        store.save(note)
        store.save(replace(note, text="not an authorized replacement"))
        store.record(note, {"snapshot": "a", "verdict": "supported"})
        store.record(note, {"snapshot": "b", "verdict": "unclear"})
        assert store.notes() == [note]
        assert store.db.execute("SELECT count(*) FROM checks").fetchone()[0] == 2
    finally:
        store.close()


@pytest.mark.parametrize("key", ["unchanged", "changed_valid"])
@pytest.mark.parametrize("mode", ["blind", "always", "freshness"])
def test_routing_counts_all_calls_without_forcing_model_verdicts(tmp_path, key, mode):
    repo = tmp_path / "repo"
    case = CASES[key]
    note = lab.prepare_case(case, repo)
    calls = []

    def ask(prompt):
        calls.append(prompt)
        evidence = (
            "return cached" if key == "changed_valid" else "return _seen[request_id]"
        )
        if prompt.startswith("Recheck"):
            return {
                "verdict": "supported",
                "reason": "The cache guard remains",
                "evidence": evidence,
            }
        return {
            "action": "reuse",
            "reason": "Current source supports the finding",
            "evidence": evidence,
        }

    out = lab.review(ask, repo, note, case["question"], mode)
    expected = 1 + int(mode == "always" or (mode == "freshness" and key != "unchanged"))
    assert len(calls) == expected and out["review"]["action"] == "reuse"
    # Every final reviewer sees the same current source, regardless of mode.
    assert lab.inspect_note(repo, note)["context"] in calls[-1]


def test_model_cannot_invent_a_source_quote(tmp_path):
    repo = tmp_path / "repo"
    note = lab.prepare_case(CASES["unchanged"], repo)
    with pytest.raises(ValueError, match="verbatim"):
        lab.review(
            lambda _: {"action": "reuse", "reason": "guessed", "evidence": "invented"},
            repo,
            note,
            "Is it still true?",
            "blind",
        )


def test_streamlit_switches_scenarios_and_records_a_review(monkeypatch):
    from types import SimpleNamespace

    # AppTest executes this file as __main__, so patch the provider imports rather
    # than the separately imported module's class in a second namespace.
    import openai
    from openai.types.completion_usage import CompletionUsage
    from streamlit.testing.v1 import AppTest

    content = json.dumps(
        {
            "action": "reuse",
            "reason": "The cache returns",
            "evidence": "return _seen[request_id]",
        }
    )
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=CompletionUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
    )
    completions = SimpleNamespace(create=lambda **kw: response)
    client = SimpleNamespace(
        chat=SimpleNamespace(completions=completions), close=lambda: None
    )
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: client)
    app = AppTest.from_file(
        str(lab.HERE / "freshness_lab.py"), default_timeout=20
    ).run()
    assert not app.exception
    app.button[0].click().run()
    assert not app.exception and not app.error
    assert any(s.value == "Reuse" for s in app.subheader)
    store = app.session_state["store"]
    assert store.db.execute("SELECT count(*) FROM checks").fetchone()[0] == 1
    app.selectbox[0].select("changed_valid").run()
    assert not app.exception
    app.session_state["store"].close()
    app.session_state["sandbox"].cleanup()


@pytest.mark.parametrize(
    "key",
    ["unchanged", "changed_valid", "changed_unsafe", "moved", "dependency_changed"],
)
def test_reference_actions_agree_with_the_toy_program_behavior(key):
    case = CASES[key]
    files = case["after"]
    scope = {}
    # Execute only the committed teaching fixtures, never a user's inspected checkout.
    if "helpers.py" in files:
        helpers = {}
        exec(files["helpers.py"], helpers)  # noqa: S102 — versioned toy fixtures only
        scope["run_once"] = helpers["run_once"]
    body = files.get("payments.py", files.get("service.py"))
    exec(body.replace("from helpers import run_once\n", ""), scope)  # noqa: S102 — versioned toy fixtures only
    charge = scope.get("charge", scope.get("charge_cached"))
    effects = []

    def send():
        effects.append("send")
        return "receipt"

    if key == "changed_unsafe":
        args = ("same-request", send, lambda: effects.append("notify"))
    else:
        args = ("same-request", send)
    charge(*args)
    before_second_call = list(effects)
    charge(*args)
    same_effects = effects == before_second_call
    assert same_effects is (case["expected_action"] == "reuse")


def test_evaluator_retains_a_client_initialization_failure(tmp_path, monkeypatch):
    from types import SimpleNamespace

    import evaluate

    def unavailable(*args, **kwargs):
        raise ValueError("No provider client")

    monkeypatch.setattr(evaluate, "Model", unavailable)
    output = tmp_path / "failed-run"
    args = SimpleNamespace(
        provider="Bedrock",
        model="test",
        region="test",
        repeats=1,
        seed=23,
        output=str(output),
    )
    with pytest.raises(RuntimeError, match="Stopped"):
        evaluate.run(args)
    rows = [
        json.loads(line)
        for line in (output / "attempts.jsonl").read_text().splitlines()
    ]
    assert len(rows) == 1 and rows[0]["error_type"] == "ValueError"
    assert rows[0]["calls"] == [] and not rows[0]["correct"]
    assert not (output / "summary.json").exists()


def test_evaluation_refuses_an_empty_cohort_before_creating_output(tmp_path):
    from types import SimpleNamespace

    import evaluate

    output = tmp_path / "zero-run"
    with pytest.raises(ValueError, match="repeat"):
        evaluate.run(SimpleNamespace(repeats=0, output=str(output)))
    assert not output.exists()


@pytest.mark.parametrize("operation_fails", [False, True])
@pytest.mark.parametrize("cleanup_fails", [False, True])
def test_evaluation_keeps_the_attempt_when_cleanup_fails(
    tmp_path, monkeypatch, operation_fails, cleanup_fails
):
    from types import SimpleNamespace

    import evaluate

    class RecordedModel:
        def __init__(self, *args, **kwargs):
            self.calls = [{"input_tokens": 3, "output_tokens": 2, "seconds": 0.01}]

        def close(self):
            if cleanup_fails:
                raise OSError("cleanup failed")

    def response(*args, **kwargs):
        if operation_fails:
            raise ValueError("provider response failed")
        return {"review": {"action": "reuse", "reason": "completed response"}}

    monkeypatch.setattr(evaluate, "Model", RecordedModel)
    monkeypatch.setattr(evaluate, "review", response)
    output = tmp_path / "cleanup-run"
    args = SimpleNamespace(
        provider="Bedrock",
        model="test",
        region="test",
        repeats=1,
        seed=23,
        output=str(output),
    )
    if operation_fails or cleanup_fails:
        with pytest.raises(RuntimeError, match="Stopped"):
            evaluate.run(args)
    else:
        evaluate.run(args)
    rows = [
        json.loads(line)
        for line in (output / "attempts.jsonl").read_text().splitlines()
    ]
    assert len(rows) == (1 if operation_fails or cleanup_fails else 18)
    first = rows[0]
    assert first["calls"] == [{"input_tokens": 3, "output_tokens": 2, "seconds": 0.01}]
    if operation_fails:
        assert first["error_type"] == "ValueError" and not first["correct"]
    else:
        assert first["result"]["review"]["reason"] == "completed response"
        assert first["correct"] and "error_type" not in first
    assert first.get("cleanup_error_type") == ("OSError" if cleanup_fails else None)
    assert (output / "summary.json").exists() is not (operation_fails or cleanup_fails)
