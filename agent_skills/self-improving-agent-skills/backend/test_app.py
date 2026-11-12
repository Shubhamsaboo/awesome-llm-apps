"""Tests for the API's model selection.

Run from backend/ with the app's requirements plus pytest and httpx:

    pip install -r requirements.txt pytest httpx
    pytest

No Gemini call is made: the optimizer is replaced with a fake that records
the model it was built with.
"""

import inspect
import time

import pytest
from fastapi.testclient import TestClient

import app as backend
from adk_optimizer import DEFAULT_MODEL, SkillOptimizer


class FakeOptimizer:
    """Stands in for SkillOptimizer and records every model it was built with."""

    built = []

    def __init__(self, api_key, model):
        FakeOptimizer.built.append(model)

    async def analyze_skill(self, skill_files):
        return {
            "scenarios": [{"id": 1, "description": "s", "input": "do it"}],
            "evals": [{"id": 1, "name": "e", "question": "ok?"}],
        }

    async def optimize(
        self,
        skill_files,
        scenarios,
        evals,
        max_rounds=5,
        callback=None,
        min_gain=0.0,
        holdout_fraction=0.0,
    ):
        return {
            "baseline_score": 0,
            "final_score": 0,
            "improved_skill_md": "",
            "score_history": [0],
            "mutation_log": [],
        }


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(backend, "SkillOptimizer", FakeOptimizer)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    FakeOptimizer.built.clear()
    backend.sessions.clear()
    with TestClient(backend.app) as c:
        yield c


def new_session():
    files = {"SKILL.md": "---\nname: t\ndescription: d\n---\n# T\n"}
    return backend.create_session_from_files(files, list(files))["session_id"]


def analyze(client, sid, **body):
    return client.post("/api/analyze", json={"session_id": sid, "gemini_api_key": "k", **body})


def test_one_default_everywhere():
    """The optimizer's own default is the app's, so the two cannot drift."""
    assert backend.DEFAULT_MODEL == DEFAULT_MODEL
    assert inspect.signature(SkillOptimizer.__init__).parameters["model"].default == DEFAULT_MODEL
    assert backend.MODEL_SUGGESTIONS[0] == DEFAULT_MODEL


def test_models_endpoint_reports_default_and_env_override(client, monkeypatch):
    data = client.get("/api/models").json()
    assert data["default"] == DEFAULT_MODEL
    assert data["suggestions"][0] == DEFAULT_MODEL
    assert len(data["suggestions"]) == len(set(data["suggestions"]))

    monkeypatch.setenv("GEMINI_MODEL", " gemini-custom ")
    data = client.get("/api/models").json()
    assert data["default"] == "gemini-custom"
    assert data["suggestions"][0] == "gemini-custom"
    assert DEFAULT_MODEL in data["suggestions"]


def test_analyze_runs_on_the_requested_model(client):
    sid = new_session()
    res = analyze(client, sid, model=" gemini-3.1-pro-preview ")
    assert res.status_code == 200, res.text
    assert res.json()["model"] == "gemini-3.1-pro-preview"
    assert FakeOptimizer.built == ["gemini-3.1-pro-preview"]
    assert backend.sessions[sid]["model"] == "gemini-3.1-pro-preview"
    assert backend.sessions[sid]["status"] == "analyzed"


@pytest.mark.parametrize("body", [{}, {"model": None}, {"model": ""}, {"model": "   "}])
def test_analyze_without_a_model_uses_the_server_default(client, monkeypatch, body):
    sid = new_session()
    assert analyze(client, sid, **body).json()["model"] == DEFAULT_MODEL

    monkeypatch.setenv("GEMINI_MODEL", "gemini-from-env")
    assert analyze(client, sid, **body).json()["model"] == "gemini-from-env"
    assert FakeOptimizer.built == [DEFAULT_MODEL, "gemini-from-env"]


@pytest.mark.parametrize("bad", ["gemini 3 flash", "gemini-3.8-flash!", "-leading-dash", "a" * 129, "x\ny"])
def test_a_name_that_is_not_a_model_id_is_refused(client, bad):
    sid = new_session()
    res = analyze(client, sid, model=bad)
    assert res.status_code == 400
    assert res.json()["detail"] == "Invalid model name"
    assert FakeOptimizer.built == []
    assert backend.sessions[sid]["status"] == "uploaded"


def test_a_prefixed_model_id_is_accepted(client):
    """Some SDKs write ids as models/<name>; the slash is fine."""
    sid = new_session()
    assert analyze(client, sid, model="models/gemini-3.8-flash").json()["model"] == "models/gemini-3.8-flash"


def test_regenerate_passes_the_model_through(client):
    sid = new_session()
    res = client.post("/api/regenerate", json={"session_id": sid, "gemini_api_key": "k", "model": "gemini-3-flash-preview"})
    assert res.status_code == 200, res.text
    assert res.json()["model"] == "gemini-3-flash-preview"
    assert FakeOptimizer.built == ["gemini-3-flash-preview"]


def test_a_client_that_predates_the_field_still_works(client):
    """The UI before the model field sent only these two keys."""
    sid = new_session()
    res = client.post("/api/analyze", json={"session_id": sid, "gemini_api_key": "k"})
    assert res.status_code == 200
    assert FakeOptimizer.built == [DEFAULT_MODEL]


def configured_session(client):
    sid = new_session()
    client.post("/api/update-config", json={"session_id": sid, "scenarios": [{"id": 1, "input": "x"}], "evals": [{"id": 1}]})
    assert backend.sessions[sid]["status"] == "configured"
    return sid


def test_start_refuses_a_bad_model_before_marking_the_session_running(client):
    sid = configured_session(client)
    res = client.post(f"/api/start/{sid}", json={"gemini_api_key": "k", "model": "not a model"})
    assert res.status_code == 400
    assert backend.sessions[sid]["status"] == "configured"
    assert "model" not in backend.sessions[sid]
    assert FakeOptimizer.built == []


def test_start_runs_on_the_requested_model_and_status_reports_it(client):
    sid = configured_session(client)
    res = client.post(f"/api/start/{sid}", json={"gemini_api_key": "k", "model": "gemini-3.1-pro-preview"})
    assert res.status_code == 200, res.text
    assert res.json() == {"status": "started", "model": "gemini-3.1-pro-preview"}
    assert client.get(f"/api/status/{sid}").json()["model"] == "gemini-3.1-pro-preview"
    # The optimizer is built inside the background task.
    deadline = time.time() + 5
    while FakeOptimizer.built != ["gemini-3.1-pro-preview"] and time.time() < deadline:
        time.sleep(0.05)
    assert FakeOptimizer.built == ["gemini-3.1-pro-preview"]


def test_start_without_a_model_uses_the_env_default(client, monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "gemini-from-env")
    sid = configured_session(client)
    res = client.post(f"/api/start/{sid}", json={"gemini_api_key": "k"})
    assert res.status_code == 200, res.text
    assert res.json()["model"] == "gemini-from-env"


def test_real_optimizer_builds_all_three_agents_on_the_model():
    """No network: ADK agents are plain objects until they run."""
    opt = SkillOptimizer(api_key="test-key", model="gemini-3.8-flash")
    assert opt.model == "gemini-3.8-flash"
    assert {a.model for a in (opt.executor, opt.analyst, opt.mutator)} == {"gemini-3.8-flash"}
    assert SkillOptimizer(api_key="test-key").model == DEFAULT_MODEL


class RecordingOptimizer:
    """Test double whose optimize() signature accepts min_gain and holdout_fraction."""

    calls = []
    emit_complete = True

    def __init__(self, api_key, model):
        self.model = model

    async def optimize(
        self,
        skill_files,
        scenarios,
        evals,
        max_rounds=5,
        callback=None,
        min_gain=0.0,
        holdout_fraction=0.0,
    ):
        RecordingOptimizer.calls.append({
            "max_rounds": max_rounds,
            "min_gain": min_gain,
            "holdout_fraction": holdout_fraction,
        })
        mutation_log = [
            {
                "round": 1,
                "strategy_type": "add_constraint",
                "diagnosis": "missing rule",
                "description": "added rule",
                "score_before": 50.0,
                "score_after": 75.0,
                "kept": True,
                "outcome": "kept",
                "parse_errors": 0,
            },
            {
                "round": 2,
                "strategy_type": "unknown",
                "diagnosis": "",
                "description": "Analyst reply could not be parsed",
                "score_before": 75.0,
                "score_after": 75.0,
                "kept": False,
                "outcome": "skipped",
                "parse_errors": 1,
            },
            {
                "round": 3,
                "strategy_type": "add_example",
                "diagnosis": "edge case",
                "description": "added noisy example",
                "score_before": 75.0,
                "score_after": 80.0,
                "kept": False,
                "outcome": "inconclusive",
                "parse_errors": 2,
            },
            {
                "round": 4,
                "strategy_type": "restructure",
                "diagnosis": "minor",
                "description": "small tweak",
                "score_before": 75.0,
                "score_after": 76.0,
                "kept": False,
                "outcome": "discarded",
                "parse_errors": 0,
            },
            {
                "round": 5,
                "strategy_type": "restructure",
                "diagnosis": "noop",
                "description": "no effective edit",
                "score_before": 75.0,
                "score_after": 75.0,
                "kept": False,
                "outcome": "unchanged",
                "parse_errors": 0,
            },
        ]
        holdout = {
            "baseline": 50.0,
            "final": 75.0,
            "total": 1,
            "regressed": False,
            "parse_errors": 0,
        }
        summary = {
            "baseline_score": 50.0,
            "final_score": 75.0,
            "improved_skill_md": "# Improved\n",
            "score_history": [50.0, 75.0, 75.0, 75.0, 75.0],
            "mutation_log": mutation_log,
            "strategy_stats": {"add_constraint": {"attempts": 1, "kept": 1}},
            "min_gain": min_gain,
            "parse_errors": 1,
            "holdout": holdout,
        }
        if callback:
            await callback({"type": "baseline", "data": {"score": 50.0, "per_eval": []}})
            for m in mutation_log:
                await callback({
                    "type": "experiment_result",
                    "data": {
                        "round": m["round"],
                        "score": m["score_after"],
                        "kept": m["kept"],
                        "outcome": m["outcome"],
                        "parse_errors": m["parse_errors"],
                        "description": m["description"],
                        "strategy": m["strategy_type"],
                        "per_eval": [],
                    },
                })
            if RecordingOptimizer.emit_complete:
                await callback({"type": "complete", "data": dict(summary)})
        return summary


def _wait_for_complete(client, sid):
    deadline = time.time() + 5
    data = client.get(f"/api/status/{sid}").json()
    while data["status"] != "complete" and time.time() < deadline:
        time.sleep(0.02)
        data = client.get(f"/api/status/{sid}").json()
    assert data["status"] == "complete", data
    return data


@pytest.mark.parametrize("emit_complete", [True, False])
def test_start_forwards_min_gain_and_holdout_and_exposes_guard_fields(
    client, monkeypatch, emit_complete
):
    RecordingOptimizer.calls.clear()
    RecordingOptimizer.emit_complete = emit_complete
    monkeypatch.setattr(backend, "SkillOptimizer", RecordingOptimizer)

    sid = configured_session(client)
    res = client.post(
        f"/api/start/{sid}",
        json={
            "gemini_api_key": "k",
            "max_rounds": 5,
            "min_gain": 5.0,
            "holdout_fraction": 0.25,
        },
    )
    assert res.status_code == 200, res.text

    status = _wait_for_complete(client, sid)
    assert RecordingOptimizer.calls == [
        {"max_rounds": 5, "min_gain": 5.0, "holdout_fraction": 0.25}
    ]

    exps = status["experiments"]
    assert [e["status"] for e in exps] == [
        "baseline",
        "keep",
        "discard",
        "discard",
        "discard",
        "discard",
    ]
    assert [e.get("outcome") for e in exps] == [
        "baseline",
        "kept",
        "skipped",
        "inconclusive",
        "discarded",
        "unchanged",
    ]
    assert [e.get("parse_errors") for e in exps[1:]] == [0, 1, 2, 0, 0]

    final = status["final_result"]
    assert final["min_gain"] == 5.0
    assert final["holdout"] == {
        "baseline": 50.0,
        "final": 75.0,
        "total": 1,
        "regressed": False,
        "parse_errors": 0,
    }
    assert final["parse_errors"] == 1
    assert final["experiments_run"] == 5
    assert final["kept"] == 1
    assert final["discarded"] == 1
    assert final["skipped"] == 1
    assert final["unchanged"] == 1
    assert final["inconclusive"] == 1
    assert (
        final["kept"]
        + final["discarded"]
        + final["skipped"]
        + final["unchanged"]
        + final["inconclusive"]
    ) == final["experiments_run"]
    assert [c["status"] for c in final["changelog"]] == [
        "keep",
        "discard",
        "discard",
        "discard",
        "discard",
    ]
    assert [c["outcome"] for c in final["changelog"]] == [
        "kept",
        "skipped",
        "inconclusive",
        "discarded",
        "unchanged",
    ]


@pytest.mark.parametrize(
    "bad_fields",
    [
        {"min_gain": -1.0},
        {"min_gain": 101.0},
        {"holdout_fraction": -0.1},
        {"holdout_fraction": 1.0},
    ],
)
def test_start_rejects_invalid_min_gain_or_holdout_fraction(client, bad_fields):
    sid = configured_session(client)
    res = client.post(f"/api/start/{sid}", json={"gemini_api_key": "k", **bad_fields})
    assert res.status_code == 422
    assert backend.sessions[sid]["status"] == "configured"
    assert FakeOptimizer.built == []


def test_fake_optimizer_with_guard_kwargs_works_with_defaults(client):
    assert "min_gain" in inspect.signature(FakeOptimizer.optimize).parameters
    assert "holdout_fraction" in inspect.signature(FakeOptimizer.optimize).parameters
    sid = configured_session(client)
    res = client.post(f"/api/start/{sid}", json={"gemini_api_key": "k"})
    assert res.status_code == 200, res.text

    status = _wait_for_complete(client, sid)
    final = status["final_result"]
    assert final["min_gain"] == 0.0
    assert final["holdout"] is None
    assert final["parse_errors"] == 0
    assert final["skipped"] == 0
    assert final["inconclusive"] == 0
