# Classification rules

`scripts/oas_diff.py` emits one record per distinct `(kind, old pointer, new pointer, summary)`. IDs are assigned after a stable sort: breaking, then deprecations, then additive; then kind; then pointers.

Local `$ref` values (`#/…`) are resolved before comparison. External refs are skipped with a warning. Cycles and size caps (`max_ref_depth`, `max_nodes`, `max_refs`, file byte cap) stop expansion and are listed under `warnings`. They do not invent changes.

## Breaking

| Kind | What changed |
|---|---|
| `removed_path` | A path item disappeared |
| `removed_operation` | An HTTP method disappeared from a path that remains |
| `removed_response_field` | A response (or nested component) property was deleted |
| `renamed_response_field` | Exactly one removed response property paired with one added property of the same type/format/enum/property-keys signature |
| `removed_request_field` | A request body, request content type, or request property disappeared |
| `request_field_required` | A request property or parameter became required, or a new required request property/parameter appeared |
| `type_narrowing` | Types shrank or swapped, `oneOf` lost variants, or `additionalProperties` became `false` |
| `format_narrowing` | A `format` appeared or changed |
| `enum_narrowing` | Enum values were removed, or an enum appeared where none existed |
| `parameter_location_change` | A parameter kept its name but changed `in` |
| `auth_scheme_change` | A security scheme was removed or altered, or an operation/root now requires a scheme it did not |
| `status_code_removed` | An operation lost a response status key (including `default`) |
| `removed_parameter` | An operation/path parameter disappeared |

## Additive

| Kind | What changed |
|---|---|
| `new_optional_field` | A non-required property, a new response status, or a new content type |
| `new_endpoint` | A new path, or a new method on an existing path |
| `enum_widening` | Enum values were added, or an enum constraint was removed |
| `new_parameter` | A non-required parameter appeared |

## Deprecations

| Kind | What changed |
|---|---|
| `deprecated` | An operation, parameter, schema, or property newly has `deprecated: true` |

## Pointers

Pointers are RFC 6901 JSON Pointers into the original documents. Property changes that resolve through a `$ref` are recorded at the component origin (for example `/components/schemas/Order/properties/note`), not at every call site.

## What this does not classify

- YAML input (convert to JSON first)
- OpenAPI 2.x / Swagger 2 documents
- Non-local `$ref`s (other files, HTTP)
- Runtime traffic, HAR files, GraphQL, gRPC, or protobuf
