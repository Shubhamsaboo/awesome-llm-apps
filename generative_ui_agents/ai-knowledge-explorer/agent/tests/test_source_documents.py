"""Keep original source text available to expand_node after extraction."""
from types import SimpleNamespace

import pytest

from src import tools


@pytest.fixture
def extraction(monkeypatch, tmp_path):
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
    upload_dir = tmp_path / "knowledge-explorer-uploads"
    upload_dir.mkdir()
    monkeypatch.setattr(
        tools, "_get_llm",
        lambda: SimpleNamespace(invoke=lambda prompt: SimpleNamespace(
            content='{"nodes": [{"label": "Example"}], "edges": []}'
        )),
    )

    def run(files=None, messages=None):
        for name, content in (files or {}).items():
            (upload_dir / name).write_text(content, encoding="utf-8")
        runtime = SimpleNamespace(
            state={"messages": messages or []}, tool_call_id="source-test"
        )
        return tools.extract_knowledge.func(runtime).update

    return run


def test_markdown_horizontal_rule_does_not_truncate_source(extraction):
    content = "First section.\n\n---\n\nSecond section with important details."
    result = extraction({"1234-report.md": content})
    assert result["documents"][0]["content"] == content


def test_marker_like_source_text_does_not_mix_documents(extraction):
    first = "First document.\n\n--- second.txt ---\nThis belongs to the first document."
    second = "This is the actual second document."
    result = extraction({"1234-first.txt": first, "5678-second.txt": second})
    docs = {doc["name"]: doc["content"] for doc in result["documents"]}
    assert docs == {"first.txt": first, "second.txt": second}


def test_pasted_source_is_saved_for_node_expansion(extraction):
    content = "A fictional pasted source document. " * 5
    message = SimpleNamespace(type="human", content=content)
    result = extraction(messages=[message])
    assert result["documents"][0]["name"] == "pasted content"
    assert result["documents"][0]["content"] == content
    assert result["nodes"][0]["sourceDocuments"] == ["pasted content"]


def test_original_unicode_and_whitespace_are_preserved(extraction):
    content = "  Müller and شاہ\n\nOriginal source whitespace.\n\n"
    result = extraction({"1234-report.txt": content})
    assert result["documents"][0]["content"] == content


def test_expansion_receives_full_extracted_source(extraction, monkeypatch):
    content = "First section.\n\n---\n\nDetails needed for a deeper explanation."
    state = extraction({"1234-report.md": content})
    prompts = []

    def invoke(prompt):
        prompts.append(prompt)
        return SimpleNamespace(content='{"detail": "More detail", "sub_nodes": [], "sub_edges": []}')

    monkeypatch.setattr(tools, "_get_llm", lambda: SimpleNamespace(invoke=invoke))
    runtime = SimpleNamespace(state=state, tool_call_id="expand-test")
    tools.expand_node.func(state["nodes"][0]["id"], runtime)
    assert content in prompts[0]
