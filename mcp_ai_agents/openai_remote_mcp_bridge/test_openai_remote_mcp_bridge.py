from openai_remote_mcp_bridge import validate_tool_arguments


SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "limit": {"type": "integer"},
        "filters": {"type": "object"},
        "tags": {"type": "array"},
    },
    "required": ["query"],
    "additionalProperties": False,
}


def test_valid_arguments_pass():
    assert validate_tool_arguments("search", {"query": "agno", "limit": 3}, SCHEMA) is None


def test_missing_required_argument_is_rejected():
    error = validate_tool_arguments("search", {"limit": 3}, SCHEMA)
    assert error is not None
    assert "query" in error


def test_unexpected_argument_is_rejected_when_schema_is_closed():
    error = validate_tool_arguments("search", {"query": "x", "nope": 1}, SCHEMA)
    assert error is not None
    assert "nope" in error


def test_wrong_scalar_type_is_rejected():
    assert validate_tool_arguments("search", {"query": 5}, SCHEMA) is not None
    assert validate_tool_arguments("search", {"query": "x", "limit": "3"}, SCHEMA) is not None


def test_boolean_is_not_an_integer():
    assert validate_tool_arguments("search", {"query": "x", "limit": True}, SCHEMA) is not None


def test_wrong_container_type_is_rejected():
    assert validate_tool_arguments("search", {"query": "x", "filters": []}, SCHEMA) is not None
    assert validate_tool_arguments("search", {"query": "x", "tags": {}}, SCHEMA) is not None


def test_empty_arguments_fail_when_schema_requires_properties():
    error = validate_tool_arguments("search", {}, SCHEMA)
    assert error is not None
    assert "query" in error


def test_empty_arguments_pass_for_argument_less_tool():
    schema = {"type": "object", "properties": {}}
    assert validate_tool_arguments("ping", {}, schema) is None


def test_open_schema_allows_extra_keys():
    schema = {"type": "object", "properties": {"a": {"type": "string"}}}
    assert validate_tool_arguments("t", {"a": "x", "b": 1}, schema) is None


NULLABLE_SCHEMA = {
    "type": "object",
    "properties": {"note": {"type": ["string", "null"]}},
}


def test_union_type_accepts_each_member():
    assert validate_tool_arguments("t", {"note": "x"}, NULLABLE_SCHEMA) is None
    assert validate_tool_arguments("t", {"note": None}, NULLABLE_SCHEMA) is None


def test_union_type_rejects_non_member():
    error = validate_tool_arguments("t", {"note": 42}, NULLABLE_SCHEMA)
    assert error is not None
    assert "string" in error


def test_null_only_type_rejects_any_value():
    schema = {"type": "object", "properties": {"note": {"type": ["null"]}}}
    assert validate_tool_arguments("t", {"note": "x"}, schema) is not None
    assert validate_tool_arguments("t", {"note": None}, schema) is None


def test_unlisted_schema_types_do_not_raise():
    schema = {"type": "object", "properties": {"id": {"type": "uuid"}}}
    assert validate_tool_arguments("t", {"id": 123}, schema) is None
    broken = {"type": "object", "properties": {"id": {"type": ""}}}
    assert validate_tool_arguments("t", {"id": object()}, broken) is None
