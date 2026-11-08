"""Uploaded sources must survive an unsuccessful extraction so users can retry."""
import json
from types import SimpleNamespace

import pytest

from src import tools


@pytest.fixture
def upload(monkeypatch, tmp_path):
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
    upload_dir = tmp_path / "knowledge-explorer-uploads"
    upload_dir.mkdir()
    source = upload_dir / "1234-report.txt"
    source.write_text("A fictional source document for extraction.", encoding="utf-8")
    return source


def runtime():
    return SimpleNamespace(state={}, tool_call_id="extract-test")


def set_reply(monkeypatch, content):
    monkeypatch.setattr(
        tools, "_get_llm",
        lambda: SimpleNamespace(invoke=lambda prompt: SimpleNamespace(content=content)),
    )


def test_invalid_json_keeps_upload_and_retry_uses_original_content(monkeypatch, upload):
    prompts = []
    replies = iter(["not JSON", '{"nodes": [], "edges": []}'])

    def invoke(prompt):
        prompts.append(prompt)
        return SimpleNamespace(content=next(replies))

    monkeypatch.setattr(tools, "_get_llm", lambda: SimpleNamespace(invoke=invoke))
    failed = tools.extract_knowledge.func(runtime())
    assert "Failed to parse" in failed.update["messages"][0].content
    assert upload.exists()

    newer_upload = upload.with_name("5678-newer.txt")
    newer_upload.write_text("A newer source document.", encoding="utf-8")
    succeeded = tools.extract_knowledge.func(runtime())
    assert succeeded.update["processingStatus"] == "ready"
    assert not upload.exists()
    assert not newer_upload.exists()
    assert "A fictional source document for extraction." in prompts[1]
    assert "A newer source document." in prompts[1]
    assert {doc["name"]: doc["content"] for doc in succeeded.update["documents"]} == {
        "report.txt": "A fictional source document for extraction.",
        "newer.txt": "A newer source document.",
    }


def test_model_error_keeps_upload(monkeypatch, upload):
    def invoke(prompt):
        raise RuntimeError("endpoint unavailable")

    monkeypatch.setattr(tools, "_get_llm", lambda: SimpleNamespace(invoke=invoke))
    with pytest.raises(RuntimeError, match="endpoint unavailable"):
        tools.extract_knowledge.func(runtime())
    assert upload.exists()


def test_graph_conversion_error_keeps_upload(monkeypatch, upload):
    set_reply(monkeypatch, json.dumps({"nodes": [{"label": "Example"}], "edges": []}))

    def fail_uuid4():
        raise RuntimeError("cannot allocate node id")

    monkeypatch.setattr(tools, "uuid", SimpleNamespace(uuid4=fail_uuid4))
    with pytest.raises(RuntimeError, match="cannot allocate node id"):
        tools.extract_knowledge.func(runtime())
    assert upload.exists()


def test_success_cleans_consumed_uploads_only(monkeypatch, upload):
    late_upload = upload.with_name("5678-later.txt")
    unreadable = upload.with_name("unreadable-directory")
    unreadable.mkdir()

    def invoke(prompt):
        late_upload.write_text("Uploaded while the model was running.", encoding="utf-8")
        return SimpleNamespace(content='{"nodes": [{"label": "Example"}], "edges": []}')

    monkeypatch.setattr(tools, "_get_llm", lambda: SimpleNamespace(invoke=invoke))
    result = tools.extract_knowledge.func(runtime())
    assert result.update["nodes"][0]["label"] == "Example"
    assert not upload.exists()
    assert late_upload.exists()
    assert unreadable.is_dir()


def test_cleanup_failure_does_not_discard_extraction(monkeypatch, upload, capsys):
    set_reply(monkeypatch, '{"nodes": [], "edges": []}')

    def fail_remove(path):
        raise PermissionError("file is locked")

    monkeypatch.setattr(tools.os, "remove", fail_remove)
    result = tools.extract_knowledge.func(runtime())
    assert result.update["processingStatus"] == "ready"
    assert result.update["documents"][0]["name"] == "report.txt"
    assert upload.exists()
    assert "file is locked" in capsys.readouterr().out
