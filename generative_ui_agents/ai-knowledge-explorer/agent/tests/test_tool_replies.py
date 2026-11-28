import json
from types import SimpleNamespace

import pytest

from src import tools

PASTED = SimpleNamespace(type="human", content="A pasted document about graphs. " * 5)
GRAPH = {
    "nodes": [
        {"id": "n1", "label": "A", "type": "concept", "description": "", "detail": "", "sourceDocuments": []},
        {"id": "n2", "label": "B", "type": "concept", "description": "", "detail": "", "sourceDocuments": []},
    ],
    "edges": [],
    "documents": [],
}


@pytest.fixture
def run_tool(monkeypatch, tmp_path):
    # extract_knowledge reads and deletes the files in the upload directory.
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))

    def run(tool, reply, state, **kwargs):
        llm = SimpleNamespace(invoke=lambda prompt: SimpleNamespace(content=reply))
        monkeypatch.setattr(tools, "_get_llm", lambda: llm)
        runtime = SimpleNamespace(state=state, tool_call_id="call-1")
        return tool.func(runtime=runtime, **kwargs).update

    return run


@pytest.mark.parametrize(
    "tool, state, kwargs, message",
    [
        (tools.extract_knowledge, {"messages": [PASTED]}, {}, "Failed to parse extraction results. Try again."),
        (tools.find_connections, GRAPH, {}, "Failed to parse connections."),
        (tools.expand_node, GRAPH, {"node_id": "n1"}, "Failed to parse expansion results."),
    ],
)
def test_reply_that_is_not_a_json_object_reports_a_parse_failure(run_tool, tool, state, kwargs, message):
    update = run_tool(tool, '[{"label": "C"}]', state, **kwargs)

    assert update["messages"][0].content == message


@pytest.mark.parametrize("reply", ['{"nodes": null, "edges": null}', '{"nodes": [{"type": "concept"}, "A"]}'])
def test_extract_knowledge_skips_entries_it_cannot_read(run_tool, reply):
    update = run_tool(tools.extract_knowledge, reply, {"messages": [PASTED]})

    assert update["nodes"] == []
    assert update["edges"] == []


def test_edges_with_source_and_target_keys_are_kept(run_tool):
    reply = '{"nodes": [{"label": "A"}, {"label": "B"}], "edges": [{"source": "A", "target": "B", "label": "uses"}]}'

    update = run_tool(tools.extract_knowledge, reply, {"messages": [PASTED]})

    ids = {node["label"]: node["id"] for node in update["nodes"]}
    assert [(edge["source"], edge["target"], edge["label"]) for edge in update["edges"]] == [
        (ids["A"], ids["B"], "uses")
    ]


def test_edge_weight_is_coerced_to_an_integer(run_tool):
    reply = json.dumps({
        "nodes": [{"label": "A", "type": "concept"}, {"label": "B", "type": "concept"}],
        "edges": [{"source_label": "A", "target_label": "B", "label": "uses", "weight": "3"}],
    })

    update = run_tool(tools.extract_knowledge, reply, {"messages": [PASTED]})

    assert update["edges"][0]["weight"] == 3


def test_unusable_edge_weights_fall_back_to_the_prompt_default(run_tool):
    reply = json.dumps({
        "nodes": [{"label": "A"}, {"label": "B"}],
        "edges": [
            {"source_label": "A", "target_label": "B", "weight": "heavy"},
            {"source_label": "B", "target_label": "A", "weight": 99},
        ],
    })

    update = run_tool(tools.extract_knowledge, reply, {"messages": [PASTED]})

    assert [edge["weight"] for edge in update["edges"]] == [1, 3]


@pytest.mark.parametrize(
    "path, expected",
    [
        ("/tmp/uploads/1699999999-quarterly-report.pdf", "quarterly-report.pdf"),
        ("/tmp/uploads/1699999999-notes.txt", "notes.txt"),
        ("/tmp/uploads/report.pdf", "report.pdf"),
    ],
)
def test_upload_name_only_drops_the_generated_timestamp(path, expected):
    assert tools._upload_name(path) == expected
