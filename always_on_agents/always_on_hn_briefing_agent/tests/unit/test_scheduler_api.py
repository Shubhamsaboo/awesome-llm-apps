import base64
import json

from fastapi.testclient import TestClient

from always_on_hn_briefing_agent.scheduler_api import app, run_scheduled_scout


def test_scheduled_scout_defaults_to_dry_run():
    result = run_scheduled_scout({"top_n": 2})

    assert result["dry_run"] is True
    assert result["delivery"]["status"] == "dry_run"
    assert len(result["brief"]["stories"]) == 2


def test_trigger_endpoint_accepts_scheduler_payload():
    client = TestClient(app)

    response = client.post(
        "/agent-scout/trigger",
        json={"dry_run": True, "top_n": 1, "live": False},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["dry_run"] is True
    assert len(payload["brief"]["stories"]) == 1


def test_pubsub_endpoint_decodes_scheduler_message():
    client = TestClient(app)
    message = base64.b64encode(
        json.dumps({"dry_run": True, "top_n": 1, "live": False}).encode("utf-8")
    ).decode("ascii")

    response = client.post("/agent-scout/pubsub", json={"message": {"data": message}})

    assert response.status_code == 200
    payload = response.json()
    assert payload["top_n"] == 1
    assert payload["delivery"]["status"] == "dry_run"


def test_trigger_endpoint_tolerates_empty_body():
    client = TestClient(app)

    response = client.post("/agent-scout/trigger")

    assert response.status_code == 200
    assert response.json()["delivery"]["status"] == "dry_run"


def test_scheduled_scout_reports_missing_delivery_config(monkeypatch):
    for name in [
        "AGENTSCOUT_DELIVERY",
        "AGENTSCOUT_WEBHOOK_URL",
        "AGENTSCOUT_EMAIL_TO",
        "AGENTSCOUT_EMAIL_FROM",
        "AGENTSCOUT_GMAIL_CLIENT_ID",
        "AGENTSCOUT_GMAIL_CLIENT_SECRET",
        "AGENTSCOUT_GMAIL_REFRESH_TOKEN",
    ]:
        monkeypatch.delenv(name, raising=False)

    result = run_scheduled_scout({"dry_run": False, "top_n": 1, "live": False})

    assert result["delivery"]["attempted"] is True
    assert result["delivery"]["status"] == "skipped_no_delivery"


def test_explicit_gmail_delivery_reports_missing_config(monkeypatch):
    monkeypatch.setenv("AGENTSCOUT_DELIVERY", "gmail")
    for name in [
        "AGENTSCOUT_EMAIL_TO",
        "AGENTSCOUT_EMAIL_FROM",
        "AGENTSCOUT_GMAIL_CLIENT_ID",
        "AGENTSCOUT_GMAIL_CLIENT_SECRET",
        "AGENTSCOUT_GMAIL_REFRESH_TOKEN",
    ]:
        monkeypatch.delenv(name, raising=False)

    result = run_scheduled_scout({"dry_run": False, "top_n": 1, "live": False})

    assert result["delivery"]["provider"] == "gmail"
    assert result["delivery"]["status"] == "skipped_missing_gmail_config"
