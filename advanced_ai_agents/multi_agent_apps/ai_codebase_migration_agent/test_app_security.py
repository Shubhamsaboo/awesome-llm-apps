import ast
from pathlib import Path

import app


def test_chart_tool_schema_does_not_accept_source_code():
    properties = app.generate_matplotlib_chart.args_schema.model_json_schema()[
        "properties"
    ]

    assert "python_code" not in properties
    assert set(properties) == {"chart_type", "labels", "values", "title", "y_label"}


def test_chart_tool_rejects_mismatched_data():
    result = app.generate_matplotlib_chart.invoke(
        {"chart_type": "bar", "labels": ["Low"], "values": []}
    )

    assert (
        result == "Error rendering chart: labels and values must have the same length."
    )


def test_app_has_no_dynamic_code_execution():
    source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "exec"
        for node in ast.walk(tree)
    )
