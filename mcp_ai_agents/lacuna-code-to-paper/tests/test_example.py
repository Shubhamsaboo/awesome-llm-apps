"""Check the example's attribution decisions without depending on a live corpus."""

import ast
import json
import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

example = runpy.run_path(str(Path(__file__).resolve().parents[1] / "examples/code_to_paper.py"))
call_json = example["call_json"]
github_key = example["github_key"]
select_resource = example["select_resource"]


def test_repository_identity_accepts_url_but_not_other_hosts_or_file_paths():
    assert github_key("https://github.com/Dao-AILab/flash-attention.git") == (
        "dao-ailab/flash-attention"
    )
    for value in ("https://example.com/Dao-AILab/flash-attention", "owner/repo/blob/main"):
        with pytest.raises(ValueError):
            github_key(value)


def test_identity_beats_search_rank_and_allows_recorded_rename():
    unrelated = {"id": "wrong", "provider": "github", "title": "other/flash-attention"}
    renamed = {
        "id": "right",
        "provider": "github",
        "title": "Dao-AILab/flash-attention",
        "provider_key": "hazyresearch/flash-attention",
    }
    assert select_resource([unrelated, renamed], "Dao-AILab/flash-attention") == renamed


def test_no_identity_match_does_not_attribute_the_first_result():
    with pytest.raises(ValueError, match="found 0"):
        select_resource([{"id": "wrong", "provider": "github", "title": "x/y"}], "a/b")


def test_ambiguous_identity_stops_before_attribution():
    candidates = [{"id": str(i), "provider": "github", "title": "a/b"} for i in range(2)]
    with pytest.raises(ValueError, match="found 2"):
        select_resource(candidates, "a/b")


@pytest.mark.parametrize("structured", [None, {"results": []}])
async def test_json_decoding_supports_both_mcp_result_formats(structured):
    class FakeClient:
        async def call_tool(self, name, arguments):
            return SimpleNamespace(
                is_error=False,
                structured_content=structured,
                content=[SimpleNamespace(type="text", text='{"results": []}')],
            )

    assert await call_json(FakeClient(), "search_lacuna", {}) == {"results": []}


async def test_tool_error_is_not_reported_as_no_papers():
    class FakeClient:
        async def call_tool(self, name, arguments):
            return SimpleNamespace(
                is_error=True,
                content=[SimpleNamespace(type="text", text="Service unavailable")],
            )

    with pytest.raises(RuntimeError, match="Service unavailable"):
        await call_json(FakeClient(), "search_lacuna", {})


@pytest.mark.parametrize("name", ["github_key", "select_resource", "call_json", "trace_repository"])
def test_notebook_functions_match_script(name):
    examples_dir = Path(__file__).resolve().parents[1] / "examples"
    script = ast.parse((examples_dir / "code_to_paper.py").read_text())
    notebook = json.loads((examples_dir / "code_to_paper.ipynb").read_text())
    notebook_nodes = []
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        if source.lstrip().startswith("%"):
            continue  # The notebook's dependency-install cell is IPython syntax.
        notebook_nodes.extend(ast.parse(source).body)

    def definitions(nodes):
        return [
            ast.dump(node, include_attributes=False)
            for node in nodes
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
        ]

    script_definitions = definitions(script.body)
    notebook_definitions = definitions(notebook_nodes)
    assert len(script_definitions) == 1, f"Expected one script definition of {name}"
    assert len(notebook_definitions) == 1, f"Expected one notebook definition of {name}"
    assert notebook_definitions == script_definitions, f"Notebook and script differ for {name}"
