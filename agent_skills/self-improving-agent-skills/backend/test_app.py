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

    async def optimize(self, skill_files, scenarios, evals, max_rounds=5, callback=None):
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
