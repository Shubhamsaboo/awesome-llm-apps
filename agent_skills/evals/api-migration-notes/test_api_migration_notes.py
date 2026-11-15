#!/usr/bin/env python3
"""
Executable eval for api-migration-notes.

    python3 agent_skills/evals/api-migration-notes/test_api_migration_notes.py

Covers differ classifications ($ref, cycles, caps, enum, required-ness) and
the notes checker (pass, missing id, unknown id, missing example). Python
stdlib only.
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile


HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.abspath(os.path.join(HERE, "..", "..", "api-migration-notes"))
DIFF_SCRIPT = os.path.join(SKILL, "scripts", "oas_diff.py")
CHECK_SCRIPT = os.path.join(SKILL, "scripts", "check_notes.py")
FIXTURES = os.path.join(HERE, "fixtures")

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append(bool(ok))
    suffix = "" if ok or not detail else ": %s" % detail
    print("  %s %s%s" % ("PASS" if ok else "FAIL", name, suffix))


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


oas_diff = load_module(DIFF_SCRIPT, "oas_diff")
check_notes = load_module(CHECK_SCRIPT, "check_notes")


def run_cli(script, args):
    return subprocess.run(
        [sys.executable, script, *args],
        capture_output=True,
        text=True,
        timeout=20,
    )


def of_kind(report, kind):
    return [item for item in report.get("changes", []) if item.get("kind") == kind]


def has_kind(report, kind):
    return bool(of_kind(report, kind))


def pointer_has(records, fragment):
    for item in records:
        blob = "%s %s %s" % (
            item.get("old_pointer") or "",
            item.get("new_pointer") or "",
            item.get("summary") or "",
        )
        if fragment in blob:
            return True
    return False


def write_json(path, doc):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(doc, handle)


def spec(paths, components=None, extra=None):
    doc = {
        "openapi": "3.0.3",
        "info": {"title": "T", "version": "1"},
        "paths": paths,
    }
    if components is not None:
        doc["components"] = components
    if extra:
        doc.update(extra)
    return doc


def json_response(schema):
    return {
        "200": {
            "description": "ok",
            "content": {"application/json": {"schema": schema}},
        }
    }


def test_orders_fixture():
    print("orders fixture classifications:")
    old_path = os.path.join(FIXTURES, "orders-v1.json")
    new_path = os.path.join(FIXTURES, "orders-v2.json")
    result = run_cli(DIFF_SCRIPT, [old_path, new_path])
    check("differ exits 0", result.returncode == 0, result.stderr.strip())
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        check("stdout is JSON", False, str(error))
        return {}
    check("stdout is JSON", True)
    check("breaking count > 0", report.get("summary", {}).get("breaking", 0) > 0, report.get("summary"))
    check("removed_path /health", pointer_has(of_kind(report, "removed_path"), "/health"), of_kind(report, "removed_path"))
    check(
        "path pointer encodes the leading slash",
        any((item.get("old_pointer") or "") == "/paths/~1health" for item in of_kind(report, "removed_path")),
        of_kind(report, "removed_path"),
    )
    check(
        "removed_operation DELETE",
        pointer_has(of_kind(report, "removed_operation"), "delete"),
        of_kind(report, "removed_operation"),
    )
    check(
        "removed_response_field note",
        pointer_has(of_kind(report, "removed_response_field"), "note"),
        of_kind(report, "removed_response_field"),
    )
    renamed = of_kind(report, "renamed_response_field")
    check(
        "renamed_response_field name -> displayName",
        any(item.get("details", {}).get("from") == "name" and item.get("details", {}).get("to") == "displayName" for item in renamed),
        renamed,
    )
    check(
        "request_field_required quantity",
        pointer_has(of_kind(report, "request_field_required"), "quantity"),
        of_kind(report, "request_field_required"),
    )
    check(
        "type_narrowing total",
        pointer_has(of_kind(report, "type_narrowing"), "total"),
        of_kind(report, "type_narrowing"),
    )
    check("format_narrowing present", has_kind(report, "format_narrowing"), of_kind(report, "format_narrowing"))
    check("enum_narrowing present", has_kind(report, "enum_narrowing"), of_kind(report, "enum_narrowing"))
    check("enum_widening present", has_kind(report, "enum_widening"), of_kind(report, "enum_widening"))
    check(
        "parameter_location_change status",
        pointer_has(of_kind(report, "parameter_location_change"), "status"),
        of_kind(report, "parameter_location_change"),
    )
    check("auth_scheme_change present", has_kind(report, "auth_scheme_change"), of_kind(report, "auth_scheme_change"))
    check(
        "status_code_removed 400",
        pointer_has(of_kind(report, "status_code_removed"), "400"),
        of_kind(report, "status_code_removed"),
    )
    check(
        "new_optional_field shippedAt",
        pointer_has(of_kind(report, "new_optional_field"), "shippedAt"),
        of_kind(report, "new_optional_field"),
    )
    check(
        "new_endpoint /invoices",
        pointer_has(of_kind(report, "new_endpoint"), "/invoices"),
        of_kind(report, "new_endpoint"),
    )
    check("deprecated present", has_kind(report, "deprecated"), of_kind(report, "deprecated"))
    check(
        "cycle warning emitted",
        any("cycle" in warning for warning in report.get("warnings", [])),
        report.get("warnings"),
    )
    ids = [item["id"] for item in report["changes"]]
    check("ids are unique", len(ids) == len(set(ids)), ids)
    check("breaking ids use BRK prefix", all(item["id"].startswith("BRK-") for item in report["changes"] if item["severity"] == "breaking"))
    return report


def test_ref_resolution():
    print("local $ref resolution:")
    old = spec(
        {
            "/items": {
                "get": {
                    "responses": json_response({"$ref": "#/components/schemas/Item"}),
                }
            }
        },
        {"schemas": {"Item": {"type": "object", "properties": {"sku": {"type": "string"}, "tag": {"type": "string"}}}}},
    )
    new = spec(
        {
            "/items": {
                "get": {
                    "responses": json_response({"$ref": "#/components/schemas/Item"}),
                }
            }
        },
        {"schemas": {"Item": {"type": "object", "properties": {"sku": {"type": "string"}}}}},
    )
    report = oas_diff.diff_documents(old, new)
    fields = of_kind(report, "removed_response_field")
    check(
        "property removed via $ref uses component pointer",
        any(
            (item.get("old_pointer") or "").endswith("/components/schemas/Item/properties/tag")
            for item in fields
        ),
        fields,
    )


def test_all_of_ref():
    print("allOf $ref merge:")
    old = spec(
        {
            "/n": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "allOf": [
                                        {"$ref": "#/components/schemas/Base"},
                                        {"type": "object", "properties": {"sku": {"type": "string"}}},
                                    ]
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "ok"}},
                }
            }
        },
        {"schemas": {"Base": {"type": "object", "properties": {"n": {"type": "integer"}}}}},
    )
    new = spec(
        {
            "/n": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "allOf": [
                                        {"$ref": "#/components/schemas/Base"},
                                        {
                                            "type": "object",
                                            "required": ["sku"],
                                            "properties": {"sku": {"type": "string"}},
                                        },
                                    ]
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "ok"}},
                }
            }
        },
        {"schemas": {"Base": {"type": "object", "properties": {"n": {"type": "integer"}}}}},
    )
    report = oas_diff.diff_documents(old, new)
    check(
        "allOf merged required field is detected",
        pointer_has(of_kind(report, "request_field_required"), "sku"),
        of_kind(report, "request_field_required"),
    )


def test_enum_and_required():
    print("enum narrowing vs widening, required-ness:")
    old = spec(
        {
            "/p": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "color": {"type": "string", "enum": ["red", "blue"]},
                                        "size": {"type": "string"},
                                    },
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "ok"}},
                }
            }
        }
    )
    new = spec(
        {
            "/p": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["size"],
                                    "properties": {
                                        "color": {"type": "string", "enum": ["red", "blue", "green"]},
                                        "size": {"type": "string"},
                                    },
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "ok"}},
                }
            }
        }
    )
    report = oas_diff.diff_documents(old, new)
    check("enum widening is additive", has_kind(report, "enum_widening"), of_kind(report, "enum_widening"))
    check("no enum narrowing on widening-only", not has_kind(report, "enum_narrowing"), of_kind(report, "enum_narrowing"))
    check("existing field newly required", pointer_has(of_kind(report, "request_field_required"), "size"))

    narrow_old = spec({"/q": {"get": {"responses": json_response({"type": "string", "enum": ["a", "b", "c"]})}}})
    narrow_new = spec({"/q": {"get": {"responses": json_response({"type": "string", "enum": ["a", "b"]})}}})
    narrow = oas_diff.diff_documents(narrow_old, narrow_new)
    check("enum narrowing is breaking", has_kind(narrow, "enum_narrowing") and not has_kind(narrow, "enum_widening"))


def test_cycle_and_caps():
    print("cycles and caps:")
    node = {
        "type": "object",
        "properties": {"next": {"$ref": "#/components/schemas/Node"}},
    }
    cyclic = spec(
        {"/t": {"get": {"responses": json_response({"$ref": "#/components/schemas/Node"})}}},
        {"schemas": {"Node": node}},
    )
    report = oas_diff.diff_documents(cyclic, cyclic)
    check("cycle does not hang", True)
    check("cycle warns", any("cycle" in w for w in report.get("warnings", [])), report.get("warnings"))

    components = {}
    for index in range(6):
        name = "S%d" % index
        nxt = "S%d" % (index + 1)
        if index < 5:
            components[name] = {"$ref": "#/components/schemas/%s" % nxt}
        else:
            components[name] = {"type": "string"}
    deep = spec(
        {"/d": {"get": {"responses": json_response({"$ref": "#/components/schemas/S0"})}}},
        {"schemas": components},
    )
    caps = oas_diff.Caps(max_ref_depth=3, max_nodes=50000, max_refs=2000)
    capped = oas_diff.diff_documents(deep, deep, caps=caps)
    check(
        "ref depth cap warns",
        any("depth cap" in w or "ref depth" in w for w in capped.get("warnings", [])),
        capped.get("warnings"),
    )

    wide_props = {"p%d" % i: {"type": "string"} for i in range(80)}
    wide = spec(
        {"/w": {"get": {"responses": json_response({"type": "object", "properties": wide_props})}}},
    )
    tiny = oas_diff.Caps(max_ref_depth=32, max_nodes=20, max_refs=2000)
    node_capped = oas_diff.diff_documents(wide, wide, caps=tiny)
    check(
        "node cap warns",
        any("size cap" in w for w in node_capped.get("warnings", [])),
        node_capped.get("warnings"),
    )


def notes_for(changes, skip=None, extra=None, examples=True):
    skip = set(skip or [])
    extra = list(extra or [])
    lines = ["# Migration notes", ""]
    for item in changes:
        ident = item["id"]
        if item.get("severity") != "breaking":
            continue
        if ident in skip:
            continue
        lines.append("## [%s] %s" % (ident, item["summary"]))
        lines.append("<!-- change: %s -->" % ident)
        lines.append("")
        lines.append("Clients calling this operation must update.")
        if examples:
            lines.append("")
            lines.append("### Before")
            lines.append("")
            lines.append("```http")
            lines.append("GET /before")
            lines.append("```")
            lines.append("")
            lines.append("### After")
            lines.append("")
            lines.append("```http")
            lines.append("GET /after")
            lines.append("```")
        lines.append("")
    for ident in extra:
        lines.append("## [%s] invented" % ident)
        lines.append("<!-- change: %s -->" % ident)
        lines.append("")
        lines.append("### Before")
        lines.append("")
        lines.append("```http")
        lines.append("GET /before")
        lines.append("```")
        lines.append("")
        lines.append("### After")
        lines.append("")
        lines.append("```http")
        lines.append("GET /after")
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def test_checker(report):
    print("checker:")
    breaking = [item for item in report["changes"] if item["severity"] == "breaking"]
    check("fixture produced breaking records", bool(breaking), report.get("summary"))
    with tempfile.TemporaryDirectory(prefix="api-mig-eval-") as tmp:
        diff_path = os.path.join(tmp, "changes.json")
        write_json(diff_path, report)

        good = os.path.join(tmp, "good.md")
        with open(good, "w", encoding="utf-8") as handle:
            handle.write(notes_for(report["changes"]))
        ok = run_cli(CHECK_SCRIPT, [good, diff_path])
        check("complete notes exit 0", ok.returncode == 0, ok.stdout + ok.stderr)
        check("complete notes say PASS", "PASS" in ok.stdout, ok.stdout)

        missing_id = breaking[0]["id"]
        bad_missing = os.path.join(tmp, "missing.md")
        with open(bad_missing, "w", encoding="utf-8") as handle:
            handle.write(notes_for(report["changes"], skip=[missing_id]))
        miss = run_cli(CHECK_SCRIPT, [bad_missing, diff_path])
        check("missing id exits 1", miss.returncode == 1, miss.stdout + miss.stderr)
        check("missing id is listed", missing_id in miss.stdout, miss.stdout)

        unknown = os.path.join(tmp, "unknown.md")
        with open(unknown, "w", encoding="utf-8") as handle:
            handle.write(notes_for(report["changes"], extra=["BRK-999"]))
        unk = run_cli(CHECK_SCRIPT, [unknown, diff_path])
        check("unknown id exits 1", unk.returncode == 1, unk.stdout)
        check("unknown id is listed", "BRK-999" in unk.stdout, unk.stdout)

        no_ex = os.path.join(tmp, "no-examples.md")
        with open(no_ex, "w", encoding="utf-8") as handle:
            handle.write(notes_for(report["changes"], examples=False))
        example = run_cli(CHECK_SCRIPT, [no_ex, diff_path])
        check("missing examples exit 1", example.returncode == 1, example.stdout)
        check("missing_examples listed", "missing_examples:" in example.stdout, example.stdout)

        usage = run_cli(CHECK_SCRIPT, [])
        check("checker usage exits 2", usage.returncode == 2, usage.stderr)


def test_yaml_rejected():
    print("YAML input:")
    with tempfile.TemporaryDirectory(prefix="api-mig-yaml-") as tmp:
        yaml_path = os.path.join(tmp, "spec.yaml")
        json_path = os.path.join(tmp, "spec.json")
        with open(yaml_path, "w", encoding="utf-8") as handle:
            handle.write("openapi: 3.0.3\n")
        write_json(json_path, spec({"/x": {"get": {"responses": {"200": {"description": "ok"}}}}}))
        result = run_cli(DIFF_SCRIPT, [yaml_path, json_path])
        check("YAML input exits 2", result.returncode == 2, result.stderr)
        check("YAML error mentions convert", "JSON" in result.stderr and "yq" in result.stderr, result.stderr)


def main():
    report = test_orders_fixture()
    print()
    test_ref_resolution()
    print()
    test_all_of_ref()
    print()
    test_enum_and_required()
    print()
    test_cycle_and_caps()
    print()
    if report:
        test_checker(report)
    else:
        check("checker skipped because differ JSON missing", False)
    print()
    test_yaml_rejected()
    print()
    if all(CHECKS):
        print("PASS: %d/%d checks" % (len(CHECKS), len(CHECKS)))
        return 0
    print("FAIL: %d/%d checks passed" % (sum(CHECKS), len(CHECKS)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
