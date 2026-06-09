"""
Data structuring tools.
- detect_schema: parse CSV/JSON/markdown/text, detect column types
- transform_data: group, sort, filter, aggregate, calculate trends
- pick_component: choose A2UI component based on data shape + user intent
"""

import csv
import io
import json
import re
from langchain.tools import tool, ToolRuntime


def _guess_type(values):
    """Guess column type from a sample of string values."""
    nums = 0
    dates = 0
    currencies = 0
    for v in values[:20]:
        v = v.strip()
        if not v:
            continue
        if re.match(r"^\$[\d,.]+$", v):
            currencies += 1
            continue
        cleaned = v.replace(",", "").replace("%", "")
        try:
            float(cleaned)
            nums += 1
            continue
        except ValueError:
            pass
        if re.match(r"\d{4}-\d{2}-\d{2}", v) or re.match(r"\d{1,2}/\d{1,2}/\d{2,4}", v):
            dates += 1

    total = len([v for v in values[:20] if v.strip()])
    if not total:
        return "string"
    if currencies / total > 0.5:
        return "currency"
    if nums / total > 0.5:
        return "number"
    if dates / total > 0.5:
        return "date"
    return "string"


def _parse_number(v):
    """Try to parse a string as a number, stripping $ and , and %."""
    v = v.strip().replace(",", "").replace("$", "").replace("%", "")
    try:
        return float(v)
    except ValueError:
        return None


def _parse_csv(raw_input):
    reader = csv.DictReader(io.StringIO(raw_input.strip()))
    columns = reader.fieldnames or []
    rows = list(reader)
    col_types = {}
    for col in columns:
        col_types[col] = _guess_type([r.get(col, "") for r in rows])
    return {
        "format": "csv",
        "columns": [{"name": c, "type": col_types.get(c, "string")} for c in columns],
        "rows": rows,
        "row_count": len(rows),
    }


def _parse_json(raw_input):
    data = json.loads(raw_input.strip())
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list) or not data:
        return {"format": "json", "columns": [], "rows": [], "row_count": 0}
    columns = list(data[0].keys()) if isinstance(data[0], dict) else []
    col_types = {}
    for col in columns:
        col_types[col] = _guess_type([str(r.get(col, "")) for r in data if isinstance(r, dict)])
    return {
        "format": "json",
        "columns": [{"name": c, "type": col_types.get(c, "string")} for c in columns],
        "rows": [r for r in data if isinstance(r, dict)],
        "row_count": len(data),
    }


def _parse_markdown(raw_input):
    lines = [l.strip() for l in raw_input.strip().splitlines() if l.strip()]
    if len(lines) < 2:
        return {"format": "markdown_table", "columns": [], "rows": [], "row_count": 0}
    headers = [c.strip() for c in lines[0].split("|") if c.strip()]
    data_lines = [l for l in lines[2:] if not re.match(r"^[\s|:-]+$", l)]
    rows = []
    for line in data_lines:
        vals = [c.strip() for c in line.split("|") if c.strip()]
        row = {}
        for i, h in enumerate(headers):
            row[h] = vals[i] if i < len(vals) else ""
        rows.append(row)
    col_types = {}
    for col in headers:
        col_types[col] = _guess_type([r.get(col, "") for r in rows])
    return {
        "format": "markdown_table",
        "columns": [{"name": c, "type": col_types.get(c, "string")} for c in headers],
        "rows": rows,
        "row_count": len(rows),
    }


@tool
def detect_schema(raw_input: str) -> dict:
    """Analyze pasted data and detect its structure.

    Parses CSV, JSON, markdown tables, or plain text. Returns format,
    columns with types (string/number/currency/date), parsed rows,
    and row count. Always call this first when a user pastes data.
    """
    text = raw_input.strip()
    if not text:
        return {"format": "empty", "columns": [], "rows": [], "row_count": 0}

    first = text.lstrip()[:1]
    if first in ("[", "{"):
        try:
            return _parse_json(text)
        except json.JSONDecodeError:
            pass

    lines = text.splitlines()
    non_empty = [l for l in lines if l.strip()]
    if len(non_empty) >= 2 and "|" in non_empty[0] and re.match(r"^[\s|:-]+$", non_empty[1]):
        return _parse_markdown(text)

    if "," in non_empty[0] and len(non_empty) >= 2:
        try:
            return _parse_csv(text)
        except Exception:
            pass

    return {
        "format": "plain_text",
        "columns": [],
        "rows": [{"text": l} for l in non_empty],
        "row_count": len(non_empty),
        "note": "Unstructured text. Use the LLM to infer structure from the content.",
    }


@tool
def transform_data(data: list[dict], operation: str, params: dict) -> dict:
    """Transform structured data. Operations:

    - group_by: group rows by a column. params: {"column": "Region"}
    - sort: sort rows. params: {"column": "Sales", "order": "desc"}
    - filter: filter rows. params: {"column": "Region", "value": "West"}
    - aggregate: compute stats. params: {"column": "Sales", "func": "sum|avg|min|max|count"}
    - trend: compare two numeric columns. params: {"col_a": "Q1 Sales", "col_b": "Q2 Sales"}
    """
    if not data:
        return {"result": [], "operation": operation, "error": "No data provided"}

    if operation == "group_by":
        col = params.get("column", "")
        groups = {}
        for row in data:
            key = str(row.get(col, "Unknown"))
            groups.setdefault(key, []).append(row)
        result = []
        for group_name, group_rows in groups.items():
            numeric_cols = [k for k in group_rows[0] if k != col and _parse_number(str(group_rows[0].get(k, ""))) is not None]
            totals = {}
            for nc in numeric_cols:
                vals = [_parse_number(str(r.get(nc, "0"))) for r in group_rows]
                vals = [v for v in vals if v is not None]
                totals[nc] = sum(vals)
            result.append({
                "group": group_name,
                "count": len(group_rows),
                "totals": totals,
                "rows": group_rows,
            })
        return {"result": result, "operation": "group_by", "column": col}

    if operation == "sort":
        col = params.get("column", "")
        desc = params.get("order", "asc") == "desc"
        def sort_key(row):
            v = _parse_number(str(row.get(col, "")))
            return v if v is not None else 0
        sorted_rows = sorted(data, key=sort_key, reverse=desc)
        return {"result": sorted_rows, "operation": "sort", "column": col}

    if operation == "filter":
        col = params.get("column", "")
        val = str(params.get("value", ""))
        filtered = [r for r in data if str(r.get(col, "")).lower() == val.lower()]
        return {"result": filtered, "operation": "filter", "column": col, "value": val, "matched": len(filtered)}

    if operation == "aggregate":
        col = params.get("column", "")
        func = params.get("func", "sum")
        vals = [_parse_number(str(r.get(col, ""))) for r in data]
        vals = [v for v in vals if v is not None]
        if not vals:
            return {"result": None, "operation": "aggregate", "error": f"No numeric values in {col}"}
        if func == "sum":
            result = sum(vals)
        elif func == "avg":
            result = sum(vals) / len(vals)
        elif func == "min":
            result = min(vals)
        elif func == "max":
            result = max(vals)
        elif func == "count":
            result = len(vals)
        else:
            result = sum(vals)
        return {"result": result, "operation": "aggregate", "column": col, "func": func}

    if operation == "trend":
        col_a = params.get("col_a", "")
        col_b = params.get("col_b", "")
        trends = []
        for row in data:
            a = _parse_number(str(row.get(col_a, "")))
            b = _parse_number(str(row.get(col_b, "")))
            if a is not None and b is not None:
                change = b - a
                pct = (change / a * 100) if a != 0 else 0
                name_col = next((k for k in row if k not in (col_a, col_b)), None)
                trends.append({
                    "name": row.get(name_col, "") if name_col else "",
                    col_a: a,
                    col_b: b,
                    "change": change,
                    "change_pct": round(pct, 1),
                    "direction": "up" if change > 0 else "down" if change < 0 else "flat",
                })
        return {"result": trends, "operation": "trend", "col_a": col_a, "col_b": col_b}

    return {"error": f"Unknown operation: {operation}"}



@tool
def pick_component(data_shape: dict, user_intent: str) -> dict:
    """Pick the best A2UI component based on data shape and user intent.

    data_shape: output from detect_schema or transform_data (has format, columns, row_count, or operation).
    user_intent: what the user asked for -- "show the data", "group by X", "compare", "summarize", "timeline", "chart".

    Returns the component name and reasoning.
    """
    intent = user_intent.lower()
    columns = data_shape.get("columns", [])
    operation = data_shape.get("operation", "")
    has_dates = any(c.get("type") == "date" for c in columns if isinstance(c, dict))
    has_numbers = any(c.get("type") in ("number", "currency") for c in columns if isinstance(c, dict))
    row_count = data_shape.get("row_count", 0)

    if "timeline" in intent and has_dates:
        return {"component": "Timeline", "reason": "Date column detected + timeline requested"}

    if operation == "group_by" or "group" in intent:
        return {"component": "CardGrid", "reason": "Grouped data renders best as cards with per-group summaries"}

    if operation == "trend" or "trend" in intent or "compar" in intent or "declin" in intent:
        return {"component": "ComparisonView", "reason": "Trend/comparison data with directional indicators"}

    if "summar" in intent:
        return {"component": "SummaryCard", "reason": "High-level stats overview requested"}

    if "chart" in intent or "bar" in intent:
        return {"component": "BarChart", "reason": "Chart visualization requested"}

    if "pie" in intent or "distribut" in intent:
        return {"component": "PieChart", "reason": "Distribution/pie chart requested"}

    if "dashboard" in intent:
        return {"component": "DashboardCard", "reason": "Multi-metric dashboard requested"}

    if row_count > 0:
        return {"component": "DataTable", "reason": "Default: tabular data renders as a sortable table"}

    return {"component": "DataTable", "reason": "Fallback to table view"}
