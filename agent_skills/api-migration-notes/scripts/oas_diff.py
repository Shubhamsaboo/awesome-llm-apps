#!/usr/bin/env python3
"""
Diff two OpenAPI 3.x JSON documents into stable change records.

Usage:
    python3 oas_diff.py OLD.json NEW.json
    python3 oas_diff.py --old OLD.json --new NEW.json

JSON only. Convert YAML before running, for example:

    yq -o=json openapi.yaml > openapi.json

Python 3.11 standard library. No network. Local $ref resolution only, with
cycle protection and size caps.

Exit codes: 0 success, 2 usage or input error.
"""

import argparse
import json
import os
import sys


HTTP_METHODS = (
    "get", "put", "post", "delete", "options", "head", "patch", "trace",
)
MAX_REF_DEPTH = 32
MAX_NODES = 50000
MAX_REFS = 2000
MAX_FILE_BYTES = 2_000_000

BREAKING = "breaking"
ADDITIVE = "additive"
DEPRECATION = "deprecation"

KIND_ORDER = {
    "removed_path": 0,
    "removed_operation": 1,
    "removed_response_field": 2,
    "renamed_response_field": 3,
    "removed_request_field": 4,
    "request_field_required": 5,
    "type_narrowing": 6,
    "format_narrowing": 7,
    "enum_narrowing": 8,
    "parameter_location_change": 9,
    "auth_scheme_change": 10,
    "status_code_removed": 11,
    "removed_parameter": 12,
    "new_optional_field": 20,
    "new_endpoint": 21,
    "enum_widening": 22,
    "new_parameter": 23,
    "deprecated": 30,
}


def encode_token(token):
    return str(token).replace("~", "~0").replace("/", "~1")


def join_pointer(*parts):
    """Join JSON Pointer tokens.

    A part that already looks like a pointer this script produced
    (`/paths…`, `/components…`, `/security`, `/info`, or any string
    containing `~`) is split as pre-encoded segments. Every other part
    is a raw OpenAPI key and is escaped (`/` → `~1`).
    """
    tokens = []
    for part in parts:
        if part is None or part == "":
            continue
        text = str(part)
        existing = text.startswith(("/paths", "/components", "/security", "/info")) or (
            text.startswith("/") and "~" in text
        )
        if existing:
            rest = text[1:]
            if rest:
                tokens.extend(rest.split("/"))
        else:
            tokens.append(encode_token(text))
    return "/" + "/".join(tokens) if tokens else ""


def pointer_tokens(ref):
    if not ref or ref == "#":
        return []
    if ref.startswith("#/"):
        raw = ref[2:]
    elif ref.startswith("/"):
        raw = ref[1:]
    else:
        return None
    out = []
    for part in raw.split("/"):
        out.append(part.replace("~1", "/").replace("~0", "~"))
    return out


def lookup(doc, ref):
    tokens = pointer_tokens(ref)
    if tokens is None:
        return None
    current = doc
    for token in tokens:
        if isinstance(current, list):
            try:
                current = current[int(token)]
            except (ValueError, IndexError, TypeError):
                return None
        elif isinstance(current, dict):
            if token not in current:
                return None
            current = current[token]
        else:
            return None
    return current


def is_ref(node):
    return isinstance(node, dict) and isinstance(node.get("$ref"), str)


def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def type_set(schema):
    if not isinstance(schema, dict):
        return set()
    types = set()
    raw = schema.get("type")
    if isinstance(raw, list):
        types.update(str(item) for item in raw if item is not None)
    elif isinstance(raw, str):
        types.add(raw)
    if schema.get("nullable") is True:
        types.add("null")
    return types


def schema_signature(schema):
    if not isinstance(schema, dict):
        return ("nonobject", repr(schema))
    props = schema.get("properties")
    keys = tuple(sorted(props)) if isinstance(props, dict) else ()
    enum = schema.get("enum")
    enum_t = tuple(json.dumps(v, sort_keys=True) for v in enum) if isinstance(enum, list) else ()
    return (
        tuple(sorted(type_set(schema))),
        schema.get("format"),
        enum_t,
        keys,
        tuple(schema.get("required") or []) if isinstance(schema.get("required"), list) else (),
    )


class Caps:
    def __init__(self, max_ref_depth=MAX_REF_DEPTH, max_nodes=MAX_NODES, max_refs=MAX_REFS):
        self.max_ref_depth = max_ref_depth
        self.max_nodes = max_nodes
        self.max_refs = max_refs
        self.nodes = 0
        self.refs = 0
        self.warnings = []
        self.hit_nodes = False
        self.hit_refs = False

    def warn(self, message):
        if message not in self.warnings:
            self.warnings.append(message)

    def count_node(self):
        self.nodes += 1
        if self.nodes > self.max_nodes and not self.hit_nodes:
            self.hit_nodes = True
            self.warn("size cap: stopped after %d nodes" % self.max_nodes)
        return not self.hit_nodes

    def count_ref(self):
        self.refs += 1
        if self.refs > self.max_refs and not self.hit_refs:
            self.hit_refs = True
            self.warn("size cap: stopped after %d $ref resolutions" % self.max_refs)
        return not self.hit_refs


class Resolver:
    def __init__(self, doc, caps):
        self.doc = doc
        self.caps = caps

    def resolve(self, node, origin="", stack=None):
        stack = list(stack or [])
        current = node
        current_origin = origin
        while is_ref(current):
            ref = current["$ref"]
            if not ref.startswith("#"):
                self.caps.warn("skipped non-local $ref %s" % ref)
                return current, current_origin
            target_pointer = pointer_from_ref(ref)
            if ref in stack or target_pointer in stack:
                self.caps.warn("cycle: %s" % " -> ".join(stack + [ref]))
                return {"x-unresolved-cycle": True, "$ref": ref}, target_pointer or current_origin
            if len(stack) >= self.caps.max_ref_depth:
                self.caps.warn("ref depth cap (%d) at %s" % (self.caps.max_ref_depth, ref))
                return current, current_origin
            if not self.caps.count_ref():
                return current, current_origin
            target = lookup(self.doc, ref)
            if target is None:
                self.caps.warn("unresolved $ref %s" % ref)
                return current, current_origin
            stack.append(ref)
            current = target
            current_origin = pointer_from_ref(ref) or current_origin
        return current, current_origin


def pointer_from_ref(ref):
    tokens = pointer_tokens(ref)
    if tokens is None:
        return ""
    return join_pointer(*tokens)


def merge_all_of(schema, resolver, origin, stack=None):
    schema, origin = resolver.resolve(schema, origin, stack)
    if not isinstance(schema, dict):
        return schema, origin
    parts = schema.get("allOf")
    if not isinstance(parts, list) or not parts:
        return schema, origin
    merged = {key: value for key, value in schema.items() if key != "allOf"}
    properties = dict(merged["properties"]) if isinstance(merged.get("properties"), dict) else {}
    required = list(merged["required"]) if isinstance(merged.get("required"), list) else []
    for index, part in enumerate(parts):
        part_origin = join_pointer(origin, "allOf", str(index)) if origin else origin
        flattened, part_origin = merge_all_of(part, resolver, part_origin, stack)
        if not isinstance(flattened, dict):
            continue
        if isinstance(flattened.get("properties"), dict):
            properties.update(flattened["properties"])
        for name in flattened.get("required") or []:
            if name not in required:
                required.append(name)
        for key, value in flattened.items():
            if key in ("properties", "required", "allOf"):
                continue
            if key not in merged:
                merged[key] = value
        if origin == "" or origin is None:
            origin = part_origin
    if properties:
        merged["properties"] = properties
    if required:
        merged["required"] = required
    return merged, origin


class Differ:
    def __init__(self, old_doc, new_doc, caps=None):
        self.old_doc = old_doc
        self.new_doc = new_doc
        self.caps = caps or Caps()
        self.old_res = Resolver(old_doc, self.caps)
        self.new_res = Resolver(new_doc, self.caps)
        self.changes = []
        self.seen_records = set()
        self.seen_schema_pairs = set()

    def add(self, kind, severity, old_pointer, new_pointer, summary, details=None):
        key = (kind, old_pointer or "", new_pointer or "", summary)
        if key in self.seen_records:
            return
        self.seen_records.add(key)
        record = {
            "kind": kind,
            "severity": severity,
            "old_pointer": old_pointer or None,
            "new_pointer": new_pointer or None,
            "summary": summary,
            "details": details or {},
        }
        self.changes.append(record)

    def freeze(self):
        def sort_key(item):
            sev_rank = {BREAKING: 0, DEPRECATION: 1, ADDITIVE: 2}.get(item["severity"], 9)
            kind_rank = KIND_ORDER.get(item["kind"], 50)
            return (
                sev_rank,
                kind_rank,
                item["kind"],
                item.get("old_pointer") or "",
                item.get("new_pointer") or "",
                item.get("summary") or "",
            )

        self.changes.sort(key=sort_key)
        counters = {BREAKING: 0, ADDITIVE: 0, DEPRECATION: 0}
        prefixes = {BREAKING: "BRK", ADDITIVE: "ADD", DEPRECATION: "DEP"}
        for item in self.changes:
            counters[item["severity"]] += 1
            item["id"] = "%s-%03d" % (prefixes[item["severity"]], counters[item["severity"]])
        return self.changes

    def walk(self):
        self.diff_paths()
        self.diff_security_schemes()
        self.diff_global_security()

    def diff_paths(self):
        old_paths = self.old_doc.get("paths") if isinstance(self.old_doc.get("paths"), dict) else {}
        new_paths = self.new_doc.get("paths") if isinstance(self.new_doc.get("paths"), dict) else {}
        for path in sorted(set(old_paths) | set(new_paths)):
            if not self.caps.count_node():
                return
            old_item = old_paths.get(path)
            new_item = new_paths.get(path)
            old_ptr = join_pointer("paths", path)
            new_ptr = join_pointer("paths", path)
            if old_item is not None and new_item is None:
                self.add(
                    "removed_path",
                    BREAKING,
                    old_ptr,
                    None,
                    "Removed path %s" % path,
                    {"path": path},
                )
                continue
            if old_item is None and new_item is not None:
                methods = [m for m in HTTP_METHODS if isinstance(new_item, dict) and m in new_item]
                self.add(
                    "new_endpoint",
                    ADDITIVE,
                    None,
                    new_ptr,
                    "New path %s (%s)" % (path, ", ".join(methods) or "no methods"),
                    {"path": path, "methods": methods},
                )
                continue
            old_item, old_ptr = self.old_res.resolve(old_item, old_ptr)
            new_item, new_ptr = self.new_res.resolve(new_item, new_ptr)
            if not isinstance(old_item, dict) or not isinstance(new_item, dict):
                continue
            old_methods = [m for m in HTTP_METHODS if m in old_item]
            new_methods = [m for m in HTTP_METHODS if m in new_item]
            for method in sorted(set(old_methods) | set(new_methods)):
                old_op = old_item.get(method)
                new_op = new_item.get(method)
                old_op_ptr = join_pointer(old_ptr, method)
                new_op_ptr = join_pointer(new_ptr, method)
                if old_op is not None and new_op is None:
                    self.add(
                        "removed_operation",
                        BREAKING,
                        old_op_ptr,
                        None,
                        "Removed operation %s %s" % (method.upper(), path),
                        {"path": path, "method": method},
                    )
                    continue
                if old_op is None and new_op is not None:
                    self.add(
                        "new_endpoint",
                        ADDITIVE,
                        None,
                        new_op_ptr,
                        "New operation %s %s" % (method.upper(), path),
                        {"path": path, "method": method},
                    )
                    continue
                self.diff_operation(path, method, old_op, new_op, old_op_ptr, new_op_ptr, old_item, new_item)

    def operation_params(self, path_item, operation, op_ptr, resolver):
        sources = []
        if isinstance(path_item, dict) and isinstance(path_item.get("parameters"), list):
            sources.append((path_item["parameters"], join_pointer(op_ptr.rsplit("/", 1)[0], "parameters")))
        if isinstance(operation, dict) and isinstance(operation.get("parameters"), list):
            sources.append((operation["parameters"], join_pointer(op_ptr, "parameters")))
        by_name = {}
        for params, base_ptr in sources:
            for index, param in enumerate(params):
                if not self.caps.count_node():
                    break
                resolved, origin = resolver.resolve(param, join_pointer(base_ptr, str(index)))
                if not isinstance(resolved, dict):
                    continue
                name = resolved.get("name")
                if not name:
                    continue
                location = resolved.get("in")
                by_name[name] = {
                    "param": resolved,
                    "pointer": origin or join_pointer(base_ptr, str(index)),
                    "in": location,
                    "name": name,
                }
        return by_name

    def diff_operation(self, path, method, old_op, new_op, old_ptr, new_ptr, old_item, new_item):
        old_op, old_ptr = self.old_res.resolve(old_op, old_ptr)
        new_op, new_ptr = self.new_res.resolve(new_op, new_ptr)
        if not isinstance(old_op, dict) or not isinstance(new_op, dict):
            return
        if old_op.get("deprecated") is not True and new_op.get("deprecated") is True:
            self.add(
                "deprecated",
                DEPRECATION,
                old_ptr,
                new_ptr,
                "Operation %s %s is now deprecated" % (method.upper(), path),
                {"path": path, "method": method},
            )
        old_params = self.operation_params(old_item, old_op, old_ptr, self.old_res)
        new_params = self.operation_params(new_item, new_op, new_ptr, self.new_res)
        self.diff_parameters(old_params, new_params, path, method)
        self.diff_request_body(old_op, new_op, old_ptr, new_ptr, path, method)
        self.diff_responses(old_op, new_op, old_ptr, new_ptr, path, method)
        self.diff_operation_security(old_op, new_op, old_ptr, new_ptr, path, method)

    def diff_parameters(self, old_params, new_params, path, method):
        for name in sorted(set(old_params) | set(new_params)):
            old_p = old_params.get(name)
            new_p = new_params.get(name)
            if old_p and not new_p:
                self.add(
                    "removed_parameter",
                    BREAKING,
                    old_p["pointer"],
                    None,
                    "Removed parameter %s on %s %s" % (name, method.upper(), path),
                    {"name": name, "in": old_p.get("in"), "path": path, "method": method},
                )
                continue
            if new_p and not old_p:
                required = new_p["param"].get("required") is True or new_p.get("in") == "path"
                kind = "request_field_required" if required else "new_parameter"
                severity = BREAKING if required else ADDITIVE
                self.add(
                    kind,
                    severity,
                    None,
                    new_p["pointer"],
                    "%s parameter %s on %s %s"
                    % ("Required" if required else "New optional", name, method.upper(), path),
                    {"name": name, "in": new_p.get("in"), "path": path, "method": method},
                )
                continue
            if old_p["in"] != new_p["in"]:
                self.add(
                    "parameter_location_change",
                    BREAKING,
                    old_p["pointer"],
                    new_p["pointer"],
                    "Parameter %s moved from %s to %s on %s %s"
                    % (name, old_p.get("in"), new_p.get("in"), method.upper(), path),
                    {
                        "name": name,
                        "old_in": old_p.get("in"),
                        "new_in": new_p.get("in"),
                        "path": path,
                        "method": method,
                    },
                )
            if old_p["param"].get("required") is not True and new_p["param"].get("required") is True:
                self.add(
                    "request_field_required",
                    BREAKING,
                    old_p["pointer"],
                    new_p["pointer"],
                    "Parameter %s is now required on %s %s" % (name, method.upper(), path),
                    {"name": name, "path": path, "method": method},
                )
            if old_p["param"].get("deprecated") is not True and new_p["param"].get("deprecated") is True:
                self.add(
                    "deprecated",
                    DEPRECATION,
                    old_p["pointer"],
                    new_p["pointer"],
                    "Parameter %s on %s %s is now deprecated" % (name, method.upper(), path),
                    {"name": name, "path": path, "method": method},
                )
            old_schema = old_p["param"].get("schema")
            new_schema = new_p["param"].get("schema")
            if old_schema is not None or new_schema is not None:
                self.compare_schema(
                    old_schema or {},
                    new_schema or {},
                    join_pointer(old_p["pointer"], "schema"),
                    join_pointer(new_p["pointer"], "schema"),
                    "request",
                )

    def media_schemas(self, container, base_ptr, resolver):
        if not isinstance(container, dict):
            return {}
        body, body_ptr = resolver.resolve(container, base_ptr)
        if not isinstance(body, dict):
            return {}
        content = body.get("content")
        content_ptr = join_pointer(body_ptr or base_ptr, "content")
        if not isinstance(content, dict):
            return {}
        out = {}
        for media, media_obj in content.items():
            if not isinstance(media_obj, dict):
                continue
            schema = media_obj.get("schema")
            if schema is None:
                continue
            media_ptr = join_pointer(content_ptr, media, "schema")
            out[media] = (schema, media_ptr)
        return out

    def diff_request_body(self, old_op, new_op, old_ptr, new_ptr, path, method):
        old_body = old_op.get("requestBody")
        new_body = new_op.get("requestBody")
        if old_body is None and new_body is None:
            return
        if old_body is not None and new_body is None:
            self.add(
                "removed_request_field",
                BREAKING,
                join_pointer(old_ptr, "requestBody"),
                None,
                "Removed request body on %s %s" % (method.upper(), path),
                {"path": path, "method": method},
            )
            return
        if old_body is None and new_body is not None:
            required = isinstance(new_body, dict) and new_body.get("required") is True
            if required:
                self.add(
                    "request_field_required",
                    BREAKING,
                    None,
                    join_pointer(new_ptr, "requestBody"),
                    "Request body is now required on %s %s" % (method.upper(), path),
                    {"path": path, "method": method},
                )
            old_media = {}
        else:
            old_media = self.media_schemas(old_body, join_pointer(old_ptr, "requestBody"), self.old_res)
        new_media = self.media_schemas(new_body, join_pointer(new_ptr, "requestBody"), self.new_res)
        if isinstance(old_body, dict) and isinstance(new_body, dict):
            if old_body.get("required") is not True and new_body.get("required") is True:
                self.add(
                    "request_field_required",
                    BREAKING,
                    join_pointer(old_ptr, "requestBody"),
                    join_pointer(new_ptr, "requestBody"),
                    "Request body is now required on %s %s" % (method.upper(), path),
                    {"path": path, "method": method},
                )
        for media in sorted(set(old_media) | set(new_media)):
            if media in old_media and media not in new_media:
                self.add(
                    "removed_request_field",
                    BREAKING,
                    old_media[media][1],
                    None,
                    "Removed request content type %s on %s %s" % (media, method.upper(), path),
                    {"media_type": media, "path": path, "method": method},
                )
                continue
            if media not in old_media and media in new_media:
                self.add(
                    "new_optional_field",
                    ADDITIVE,
                    None,
                    new_media[media][1],
                    "New request content type %s on %s %s" % (media, method.upper(), path),
                    {"media_type": media, "path": path, "method": method},
                )
                continue
            old_schema, old_s_ptr = old_media[media]
            new_schema, new_s_ptr = new_media[media]
            self.compare_schema(old_schema, new_schema, old_s_ptr, new_s_ptr, "request")

    def diff_responses(self, old_op, new_op, old_ptr, new_ptr, path, method):
        old_resp = old_op.get("responses") if isinstance(old_op.get("responses"), dict) else {}
        new_resp = new_op.get("responses") if isinstance(new_op.get("responses"), dict) else {}
        for code in sorted(set(old_resp) | set(new_resp), key=lambda c: (c == "default", c)):
            old_r = old_resp.get(code)
            new_r = new_resp.get(code)
            old_r_ptr = join_pointer(old_ptr, "responses", code)
            new_r_ptr = join_pointer(new_ptr, "responses", code)
            if old_r is not None and new_r is None:
                self.add(
                    "status_code_removed",
                    BREAKING,
                    old_r_ptr,
                    None,
                    "Removed status %s from %s %s" % (code, method.upper(), path),
                    {"status": code, "path": path, "method": method},
                )
                continue
            if old_r is None and new_r is not None:
                self.add(
                    "new_optional_field",
                    ADDITIVE,
                    None,
                    new_r_ptr,
                    "New status %s on %s %s" % (code, method.upper(), path),
                    {"status": code, "path": path, "method": method},
                )
                continue
            old_media = self.media_schemas(old_r, old_r_ptr, self.old_res)
            new_media = self.media_schemas(new_r, new_r_ptr, self.new_res)
            for media in sorted(set(old_media) | set(new_media)):
                if media in old_media and media not in new_media:
                    self.add(
                        "removed_response_field",
                        BREAKING,
                        old_media[media][1],
                        None,
                        "Removed response content type %s for status %s on %s %s"
                        % (media, code, method.upper(), path),
                        {"media_type": media, "status": code, "path": path, "method": method},
                    )
                    continue
                if media not in old_media and media in new_media:
                    self.add(
                        "new_optional_field",
                        ADDITIVE,
                        None,
                        new_media[media][1],
                        "New response content type %s for status %s on %s %s"
                        % (media, code, method.upper(), path),
                        {"media_type": media, "status": code, "path": path, "method": method},
                    )
                    continue
                old_schema, old_s_ptr = old_media[media]
                new_schema, new_s_ptr = new_media[media]
                self.compare_schema(old_schema, new_schema, old_s_ptr, new_s_ptr, "response")

    def compare_schema(self, old_schema, new_schema, old_ptr, new_ptr, role, stack=None):
        stack = list(stack or [])
        old_schema, old_ptr = merge_all_of(old_schema, self.old_res, old_ptr, stack)
        new_schema, new_ptr = merge_all_of(new_schema, self.new_res, new_ptr, stack)
        pair = (old_ptr, new_ptr, role)
        if pair in self.seen_schema_pairs:
            return
        self.seen_schema_pairs.add(pair)
        if not self.caps.count_node():
            return
        if not isinstance(old_schema, dict) or not isinstance(new_schema, dict):
            return
        if old_schema.get("x-unresolved-cycle") or new_schema.get("x-unresolved-cycle"):
            return

        old_types = type_set(old_schema)
        new_types = type_set(new_schema)
        if old_types and new_types and new_types < old_types:
            self.add(
                "type_narrowing",
                BREAKING,
                old_ptr,
                new_ptr,
                "Type narrowed from %s to %s" % (sorted(old_types), sorted(new_types)),
                {"old_type": sorted(old_types), "new_type": sorted(new_types), "role": role},
            )
        elif old_types and new_types and new_types != old_types and not old_types < new_types:
            # Unrelated type swap (integer -> string, etc.) is breaking for callers.
            self.add(
                "type_narrowing",
                BREAKING,
                old_ptr,
                new_ptr,
                "Type changed from %s to %s" % (sorted(old_types), sorted(new_types)),
                {"old_type": sorted(old_types), "new_type": sorted(new_types), "role": role},
            )
        elif (not old_types) and new_types:
            self.add(
                "type_narrowing",
                BREAKING,
                old_ptr,
                new_ptr,
                "Type constrained to %s" % sorted(new_types),
                {"old_type": [], "new_type": sorted(new_types), "role": role},
            )

        old_format = old_schema.get("format")
        new_format = new_schema.get("format")
        if old_format != new_format:
            if new_format and (not old_format or old_format != new_format):
                self.add(
                    "format_narrowing",
                    BREAKING,
                    old_ptr,
                    new_ptr,
                    "Format changed from %s to %s" % (old_format or "(none)", new_format),
                    {"old_format": old_format, "new_format": new_format, "role": role},
                )

        old_enum = old_schema.get("enum") if isinstance(old_schema.get("enum"), list) else None
        new_enum = new_schema.get("enum") if isinstance(new_schema.get("enum"), list) else None
        if old_enum is not None or new_enum is not None:
            old_set = {json.dumps(v, sort_keys=True) for v in (old_enum or [])}
            new_set = {json.dumps(v, sort_keys=True) for v in (new_enum or [])}
            if new_enum is not None and old_enum is None:
                self.add(
                    "enum_narrowing",
                    BREAKING,
                    old_ptr,
                    new_ptr,
                    "Enum constraint added (%d values)" % len(new_enum),
                    {"added_constraint": new_enum, "role": role},
                )
            elif old_enum is not None and new_enum is None:
                self.add(
                    "enum_widening",
                    ADDITIVE,
                    old_ptr,
                    new_ptr,
                    "Enum constraint removed",
                    {"removed_constraint": old_enum, "role": role},
                )
            else:
                removed = sorted(old_set - new_set)
                added = sorted(new_set - old_set)
                if removed:
                    self.add(
                        "enum_narrowing",
                        BREAKING,
                        old_ptr,
                        new_ptr,
                        "Enum lost %d value(s)" % len(removed),
                        {
                            "removed": [json.loads(v) for v in removed],
                            "role": role,
                        },
                    )
                if added:
                    self.add(
                        "enum_widening",
                        ADDITIVE,
                        old_ptr,
                        new_ptr,
                        "Enum gained %d value(s)" % len(added),
                        {
                            "added": [json.loads(v) for v in added],
                            "role": role,
                        },
                    )

        if old_schema.get("additionalProperties") is not False and new_schema.get("additionalProperties") is False:
            self.add(
                "type_narrowing",
                BREAKING,
                old_ptr,
                new_ptr,
                "additionalProperties closed (was open)",
                {"role": role},
            )

        if old_schema.get("deprecated") is not True and new_schema.get("deprecated") is True:
            self.add(
                "deprecated",
                DEPRECATION,
                old_ptr,
                new_ptr,
                "Schema is now deprecated",
                {"role": role},
            )

        child_stack = stack + [p for p in (old_ptr, new_ptr) if p]
        old_items = old_schema.get("items")
        new_items = new_schema.get("items")
        if old_items is not None and new_items is not None:
            self.compare_schema(
                old_items,
                new_items,
                join_pointer(old_ptr, "items"),
                join_pointer(new_ptr, "items"),
                role,
                child_stack,
            )

        self.diff_object_properties(old_schema, new_schema, old_ptr, new_ptr, role, child_stack)

        old_one = old_schema.get("oneOf") if isinstance(old_schema.get("oneOf"), list) else None
        new_one = new_schema.get("oneOf") if isinstance(new_schema.get("oneOf"), list) else None
        if old_one is not None and new_one is not None and len(new_one) < len(old_one):
            self.add(
                "type_narrowing",
                BREAKING,
                join_pointer(old_ptr, "oneOf"),
                join_pointer(new_ptr, "oneOf"),
                "oneOf variants reduced from %d to %d" % (len(old_one), len(new_one)),
                {"role": role},
            )

    def diff_object_properties(self, old_schema, new_schema, old_ptr, new_ptr, role, stack=None):
        stack = list(stack or [])
        old_props = old_schema.get("properties") if isinstance(old_schema.get("properties"), dict) else {}
        new_props = new_schema.get("properties") if isinstance(new_schema.get("properties"), dict) else {}
        old_req = set(old_schema.get("required") or []) if isinstance(old_schema.get("required"), list) else set()
        new_req = set(new_schema.get("required") or []) if isinstance(new_schema.get("required"), list) else set()

        removed = {name: old_props[name] for name in old_props if name not in new_props}
        added = {name: new_props[name] for name in new_props if name not in old_props}
        paired = set()
        if role == "response":
            unused_added = dict(added)
            for old_name in sorted(removed):
                old_sig = schema_signature(
                    merge_all_of(removed[old_name], self.old_res, join_pointer(old_ptr, "properties", old_name))[0]
                )
                match = None
                for new_name in sorted(unused_added):
                    new_sig = schema_signature(
                        merge_all_of(unused_added[new_name], self.new_res, join_pointer(new_ptr, "properties", new_name))[0]
                    )
                    if old_sig == new_sig:
                        match = new_name
                        break
                if match is not None:
                    self.add(
                        "renamed_response_field",
                        BREAKING,
                        join_pointer(old_ptr, "properties", old_name),
                        join_pointer(new_ptr, "properties", match),
                        "Response field %s renamed to %s" % (old_name, match),
                        {"from": old_name, "to": match, "role": role},
                    )
                    paired.add(old_name)
                    unused_added.pop(match, None)

        for name in sorted(removed):
            if name in paired:
                continue
            kind = "removed_response_field" if role == "response" else "removed_request_field"
            self.add(
                kind,
                BREAKING,
                join_pointer(old_ptr, "properties", name),
                None,
                "%s field %s was removed" % ("Response" if role == "response" else "Request", name),
                {"name": name, "role": role},
            )

        for name in sorted(added):
            already_renamed = False
            if role == "response":
                for item in self.changes:
                    if item["kind"] == "renamed_response_field" and item["details"].get("to") == name:
                        already_renamed = True
                        break
            if already_renamed:
                continue
            if role == "request" and name in new_req:
                self.add(
                    "request_field_required",
                    BREAKING,
                    None,
                    join_pointer(new_ptr, "properties", name),
                    "New required request field %s" % name,
                    {"name": name, "role": role},
                )
            else:
                self.add(
                    "new_optional_field",
                    ADDITIVE,
                    None,
                    join_pointer(new_ptr, "properties", name),
                    "New optional %s field %s" % (role, name),
                    {"name": name, "role": role},
                )

        for name in sorted(set(old_props) & set(new_props)):
            if name not in old_req and name in new_req and role == "request":
                self.add(
                    "request_field_required",
                    BREAKING,
                    join_pointer(old_ptr, "properties", name),
                    join_pointer(new_ptr, "properties", name),
                    "Request field %s is now required" % name,
                    {"name": name, "role": role},
                )
            old_prop = old_props[name]
            new_prop = new_props[name]
            if isinstance(old_prop, dict) and old_prop.get("deprecated") is not True:
                new_prop_resolved, _ = self.new_res.resolve(new_prop, join_pointer(new_ptr, "properties", name))
                if isinstance(new_prop_resolved, dict) and new_prop_resolved.get("deprecated") is True:
                    self.add(
                        "deprecated",
                        DEPRECATION,
                        join_pointer(old_ptr, "properties", name),
                        join_pointer(new_ptr, "properties", name),
                        "Field %s is now deprecated" % name,
                        {"name": name, "role": role},
                    )
            self.compare_schema(
                old_prop,
                new_prop,
                join_pointer(old_ptr, "properties", name),
                join_pointer(new_ptr, "properties", name),
                role,
                stack,
            )

    def diff_security_schemes(self):
        old_comp = self.old_doc.get("components") if isinstance(self.old_doc.get("components"), dict) else {}
        new_comp = self.new_doc.get("components") if isinstance(self.new_doc.get("components"), dict) else {}
        old_schemes = old_comp.get("securitySchemes") if isinstance(old_comp.get("securitySchemes"), dict) else {}
        new_schemes = new_comp.get("securitySchemes") if isinstance(new_comp.get("securitySchemes"), dict) else {}
        for name in sorted(set(old_schemes) | set(new_schemes)):
            old_s = old_schemes.get(name)
            new_s = new_schemes.get(name)
            old_ptr = join_pointer("components", "securitySchemes", name)
            new_ptr = join_pointer("components", "securitySchemes", name)
            if old_s is not None and new_s is None:
                self.add(
                    "auth_scheme_change",
                    BREAKING,
                    old_ptr,
                    None,
                    "Removed security scheme %s" % name,
                    {"scheme": name},
                )
                continue
            if old_s is None and new_s is not None:
                continue
            old_s, _ = self.old_res.resolve(old_s, old_ptr)
            new_s, _ = self.new_res.resolve(new_s, new_ptr)
            if not isinstance(old_s, dict) or not isinstance(new_s, dict):
                continue
            for field in ("type", "scheme", "bearerFormat", "openIdConnectUrl", "in", "name"):
                if old_s.get(field) != new_s.get(field):
                    self.add(
                        "auth_scheme_change",
                        BREAKING,
                        old_ptr,
                        new_ptr,
                        "Security scheme %s changed %s from %s to %s"
                        % (name, field, old_s.get(field), new_s.get(field)),
                        {"scheme": name, "field": field},
                    )
            if json.dumps(old_s.get("flows"), sort_keys=True) != json.dumps(new_s.get("flows"), sort_keys=True):
                self.add(
                    "auth_scheme_change",
                    BREAKING,
                    join_pointer(old_ptr, "flows"),
                    join_pointer(new_ptr, "flows"),
                    "Security scheme %s OAuth flows changed" % name,
                    {"scheme": name},
                )

    def security_names(self, security):
        names = set()
        for req in as_list(security):
            if isinstance(req, dict):
                names.update(req.keys())
        return names

    def effective_security(self, op, global_security):
        if isinstance(op, dict) and "security" in op:
            return op.get("security")
        return global_security

    def diff_global_security(self):
        old_global = self.old_doc.get("security")
        new_global = self.new_doc.get("security")
        old_names = self.security_names(old_global)
        new_names = self.security_names(new_global)
        added = sorted(new_names - old_names)
        if added and new_global:
            self.add(
                "auth_scheme_change",
                BREAKING,
                "/security" if old_global is not None else None,
                "/security",
                "Global security now requires %s" % ", ".join(added),
                {"added": added},
            )

    def diff_operation_security(self, old_op, new_op, old_ptr, new_ptr, path, method):
        old_sec = self.effective_security(old_op, self.old_doc.get("security"))
        new_sec = self.effective_security(new_op, self.new_doc.get("security"))
        old_names = self.security_names(old_sec)
        new_names = self.security_names(new_sec)
        if new_sec == [] and old_sec != []:
            return
        added = sorted(new_names - old_names)
        if added and new_sec:
            self.add(
                "auth_scheme_change",
                BREAKING,
                join_pointer(old_ptr, "security") if "security" in old_op else "/security",
                join_pointer(new_ptr, "security") if "security" in new_op else "/security",
                "Operation %s %s now requires %s" % (method.upper(), path, ", ".join(added)),
                {"added": added, "path": path, "method": method},
            )


def load_document(path):
    if not os.path.isfile(path):
        raise ValueError("file not found: %s" % path)
    size = os.path.getsize(path)
    if size > MAX_FILE_BYTES:
        raise ValueError("file exceeds %d byte cap: %s" % (MAX_FILE_BYTES, path))
    lower = path.lower()
    if lower.endswith((".yaml", ".yml")):
        raise ValueError(
            "YAML is not parsed; convert to JSON first, e.g. "
            "`yq -o=json %s > %s`" % (path, os.path.splitext(path)[0] + ".json")
        )
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError("invalid JSON in %s: %s" % (path, error))
    if not isinstance(doc, dict):
        raise ValueError("%s is not a JSON object" % path)
    version = str(doc.get("openapi") or "")
    if not version.startswith("3."):
        raise ValueError("%s is not OpenAPI 3.x (openapi=%r)" % (path, version))
    return doc


def info_block(doc, path):
    info = doc.get("info") if isinstance(doc.get("info"), dict) else {}
    return {
        "file": path,
        "openapi": doc.get("openapi"),
        "title": info.get("title"),
        "version": info.get("version"),
    }


def diff_files(old_path, new_path, caps=None):
    old_doc = load_document(old_path)
    new_doc = load_document(new_path)
    return diff_documents(old_doc, new_doc, old_path=old_path, new_path=new_path, caps=caps)


def diff_documents(old_doc, new_doc, old_path="old.json", new_path="new.json", caps=None):
    caps = caps or Caps()
    differ = Differ(old_doc, new_doc, caps)
    differ.walk()
    changes = differ.freeze()
    summary = {
        "breaking": sum(1 for item in changes if item["severity"] == BREAKING),
        "additive": sum(1 for item in changes if item["severity"] == ADDITIVE),
        "deprecation": sum(1 for item in changes if item["severity"] == DEPRECATION),
    }
    return {
        "old": info_block(old_doc, old_path),
        "new": info_block(new_doc, new_path),
        "limits": {
            "max_ref_depth": caps.max_ref_depth,
            "max_nodes": caps.max_nodes,
            "max_refs": caps.max_refs,
            "max_file_bytes": MAX_FILE_BYTES,
        },
        "warnings": caps.warnings,
        "changes": changes,
        "summary": summary,
    }


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Diff two OpenAPI 3.x JSON documents.")
    parser.add_argument("old", nargs="?", help="old OpenAPI JSON path")
    parser.add_argument("new", nargs="?", help="new OpenAPI JSON path")
    parser.add_argument("--old", dest="old_flag", help="old OpenAPI JSON path")
    parser.add_argument("--new", dest="new_flag", help="new OpenAPI JSON path")
    parser.add_argument("--json", action="store_true", help="emit JSON (default)")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    old_path = args.old_flag or args.old
    new_path = args.new_flag or args.new
    if not old_path or not new_path:
        print("usage: oas_diff.py OLD.json NEW.json", file=sys.stderr)
        return 2
    try:
        report = diff_files(old_path, new_path)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
