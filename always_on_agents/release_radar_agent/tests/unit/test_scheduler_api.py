import base64
import json
import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from always_on_agents.release_radar_agent.delivery import send_brief
from always_on_agents.release_radar_agent.scheduler_api import (
    app,
    run_scheduled_radar,
)


def test_scheduled_radar_defaults_to_sample_dry_run():
    result = run_scheduled_radar({"top_n": 2, "live": False})

    assert result["dry_run"] is True
    assert result["delivery"]["status"] == "dry_run"
    assert result["brief"]["watch_mode"] == "sample"
    assert len(result["brief"]["releases"]) == 2


def test_delivery_without_credentials_never_calls_network():
    payload = run_scheduled_radar({"dry_run": True, "top_n": 1, "live": False})[
        "brief"
    ]

    with patch.dict(os.environ, {}, clear=True), patch(
        "urllib.request.urlopen"
    ) as urlopen:
        delivery = send_brief(payload)

    assert delivery["sent"] is False
    assert delivery["status"] == "skipped_no_delivery"
    urlopen.assert_not_called()


def test_explicit_non_dry_run_still_requires_delivery_configuration():
    with patch.dict(os.environ, {}, clear=True), patch(
        "urllib.request.urlopen"
    ) as urlopen:
        result = run_scheduled_radar({"dry_run": False, "top_n": 1, "live": False})

    assert result["delivery"]["attempted"] is True
    assert result["delivery"]["sent"] is False
    assert result["delivery"]["status"] == "skipped_no_delivery"
    urlopen.assert_not_called()


def test_scheduler_manifest_path_is_server_configured(tmp_path):
    requested_manifest = tmp_path / "package.json"
    requested_manifest.write_text('{"dependencies": {"react": "18.2.0"}}')

    with patch.dict(os.environ, {}, clear=True):
        result = run_scheduled_radar(
            {
                "dry_run": True,
                "live": False,
                "manifest_path": str(requested_manifest),
            }
        )

    assert result["brief"]["manifest_path"] == "deterministic sample data"


def test_trigger_and_pubsub_endpoints_return_briefs():
    client = TestClient(app)
    response = client.post(
        "/release-radar/trigger",
        json={"dry_run": True, "top_n": 1, "live": False},
    )
    message = base64.b64encode(
        json.dumps({"dry_run": True, "top_n": 1, "live": False}).encode("utf-8")
    ).decode("ascii")
    pubsub_response = client.post(
        "/release-radar/pubsub", json={"message": {"data": message}}
    )

    assert response.status_code == 200
    assert response.json()["brief"]["releases"]
    assert pubsub_response.status_code == 200
    assert pubsub_response.json()["delivery"]["status"] == "dry_run"
