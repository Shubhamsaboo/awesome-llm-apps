import base64
import json
import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from always_on_agents.page_watch_agent.delivery import send_brief
from always_on_agents.page_watch_agent.scheduler_api import (
    app,
    run_scheduled_watch,
)


def test_scheduled_watch_defaults_to_sample_dry_run():
    result = run_scheduled_watch({"live": False})

    assert result["dry_run"] is True
    assert result["delivery"]["status"] == "dry_run"
    assert result["delivery"]["sent"] is False
    assert result["brief"]["watch_mode"] == "sample"
    assert result["brief"]["pages"]


def test_scheduler_does_not_disable_live_model_by_default():
    with patch(
        "always_on_agents.page_watch_agent.scheduler_api.run_page_watch"
    ) as run:
        run.return_value = {
            "subject": "Page Watch brief",
            "text": "brief",
            "html": "<p>brief</p>",
            "pages": [],
        }
        run_scheduled_watch({"live": True})

    assert run.call_args.kwargs["live"] is True
    assert run.call_args.kwargs["live_model"] is None


def test_delivery_without_credentials_never_calls_network():
    payload = run_scheduled_watch({"dry_run": True, "live": False})["brief"]

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
        result = run_scheduled_watch({"dry_run": False, "live": False})

    assert result["delivery"]["attempted"] is True
    assert result["delivery"]["sent"] is False
    assert result["delivery"]["status"] == "skipped_no_delivery"
    urlopen.assert_not_called()


def test_scheduler_watchlist_path_is_server_configured(tmp_path):
    requested = tmp_path / "watch.json"
    requested.write_text(
        json.dumps({"pages": [{"url": "https://example.invalid/x", "name": "X"}]}),
        encoding="utf-8",
    )

    with patch.dict(os.environ, {}, clear=True):
        result = run_scheduled_watch(
            {
                "dry_run": True,
                "live": False,
                "watchlist_path": str(requested),
            }
        )

    assert result["brief"]["watchlist_path"] == "deterministic sample pages"


def test_trigger_and_pubsub_endpoints_return_briefs():
    client = TestClient(app)
    response = client.post(
        "/page-watch/trigger",
        json={"dry_run": True, "live": False},
    )
    message = base64.b64encode(
        json.dumps({"dry_run": True, "live": False}).encode("utf-8")
    ).decode("ascii")
    pubsub_response = client.post(
        "/page-watch/pubsub", json={"message": {"data": message}}
    )
    dry_run = client.get("/page-watch/dry-run")

    assert response.status_code == 200
    assert response.json()["brief"]["pages"]
    assert response.json()["delivery"]["status"] == "dry_run"
    assert pubsub_response.status_code == 200
    assert pubsub_response.json()["delivery"]["status"] == "dry_run"
    assert dry_run.status_code == 200
    assert dry_run.json()["dry_run"] is True
    assert dry_run.json()["delivery"]["sent"] is False
