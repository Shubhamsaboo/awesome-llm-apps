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


# --- Regression: malformed provider schemas must never terminate the bridge ---


def test_boolean_property_schema_does_not_raise():
    """A boolean schema (`{"x": true}`) is valid JSON Schema draft 6+."""
    assert validate_tool_arguments("t", {"x": "anything"}, {"properties": {"x": True}}) is None
    assert validate_tool_arguments("t", {"x": 1}, {"properties": {"x": False}}) is None


def test_non_iterable_required_does_not_raise():
    """`"required": true` used to raise TypeError while iterating."""
    schema = {"properties": {"x": {"type": "string"}}, "required": True}
    assert validate_tool_arguments("t", {"x": "ok"}, schema) is None


def test_non_dict_properties_does_not_raise():
    for bad_properties in ([], ["x"], None, True, "x", 42):
        schema = {"properties": bad_properties, "required": ["x"]}
        # A broken `properties` must not crash; `required` still applies.
        assert validate_tool_arguments("t", {}, schema) is not None
        assert validate_tool_arguments("t", {"x": 1}, schema) is None


def test_mixed_malformed_schema_fragments_do_not_raise():
    schema = {
        "properties": {
            "ok": {"type": "string"},
            "free": True,
            "broken": [],
            "nullish": None,
        },
        "required": ["ok", 7, None],
        "additionalProperties": False,
    }
    assert validate_tool_arguments("t", {"ok": 1}, schema) is not None
    assert (
        validate_tool_arguments("t", {"ok": "yes", "free": 3, "broken": {}, "nullish": []}, schema)
        is None
    )


def test_non_dict_schema_does_not_raise():
    for bad_schema in (None, True, [], "object", 3):
        assert validate_tool_arguments("t", {"x": 1}, bad_schema) is None


def test_required_with_non_string_entries_is_safe():
    schema = {"properties": {"x": {"type": "string"}}, "required": [1, None, "x"]}
    error = validate_tool_arguments("t", {}, schema)
    assert error is not None and "x" in error


def test_integral_float_satisfies_integer():
    assert validate_tool_arguments("t", {"x": 3.0}, {"properties": {"x": {"type": "integer"}}}) is None
    assert validate_tool_arguments("t", {"x": 3.5}, {"properties": {"x": {"type": "integer"}}}) is not None
    assert validate_tool_arguments("t", {"x": True}, {"properties": {"x": {"type": "integer"}}}) is not None
