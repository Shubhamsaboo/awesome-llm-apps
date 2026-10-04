#!/usr/bin/env python3
"""Normalize log exports from GCP or AWS into one evidence bundle.

Everything downstream — the RCA scorer, the optimizer, the skill itself — reads
only the normalized shape, so the same rubric and the same golden set work
whichever backend the logs came from.

    python scripts/normalize_evidence.py logs.json                    # auto-detect
    python scripts/normalize_evidence.py logs.json --vendor gcp -o bundle.json
    gcloud logging read '...' --format=json | python scripts/normalize_evidence.py -

Supported inputs
  gcp  Logs Explorer JSON / `gcloud logging read --format=json`
  aws  CloudWatch Logs Insights `get-query-results`, or `filter-log-events`
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from typing import Optional

# GCP and OTel both carry more severity spellings than anyone needs.
SEVERITY_MAP = {
    "DEBUG": "DEBUG", "TRACE": "DEBUG", "FINE": "DEBUG", "100": "DEBUG",
    "INFO": "INFO", "INFORMATION": "INFO", "NOTICE": "INFO", "200": "INFO",
    "WARN": "WARN", "WARNING": "WARN", "300": "WARN",
    "ERROR": "ERROR", "ERR": "ERROR", "SEVERE": "ERROR", "500": "ERROR",
    "CRITICAL": "CRITICAL", "FATAL": "CRITICAL", "ALERT": "CRITICAL",
    "EMERGENCY": "CRITICAL", "600": "CRITICAL", "700": "CRITICAL", "800": "CRITICAL",
}


def _severity(raw, fallback: str = "INFO") -> str:
    if raw is None:
        return fallback
    return SEVERITY_MAP.get(str(raw).strip().upper(), fallback)


def _iso(value) -> Optional[str]:
    """Coerce epoch millis/seconds, or assorted string formats, to ISO-8601 UTC."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        # Heuristic: anything past ~2001 in seconds is >1e9; millis are >1e12.
        seconds = value / 1000.0 if value > 1e11 else float(value)
        return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()
    text = str(value).strip()
    if re.fullmatch(r"\d{10,19}", text):
        return _iso(int(text))
    # CloudWatch Insights uses "2026-09-18 14:02:11.123" (no T, no zone).
    candidate = text.replace(" ", "T", 1) if " " in text and "T" not in text else text
    candidate = re.sub(r"Z$", "+00:00", candidate)
    # Trim sub-microsecond precision that fromisoformat rejects on older Pythons.
    candidate = re.sub(r"(\.\d{6})\d+", r"\1", candidate)
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return text  # Keep the original rather than silently dropping a timestamp.
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _entry(ts=None, severity="INFO", service=None, message="", trace_id=None,
           attributes=None):
    # attributes is an explicit dict rather than **kwargs: adapters copy whole
    # vendor payloads in here, and a key like "message" or "service" would
    # otherwise collide with a named parameter.
    return {
        "ts": _iso(ts),
        "severity": severity,
        "service": service,
        "message": (message or "").strip(),
        "trace_id": trace_id,
        "attributes": {k: v for k, v in (attributes or {}).items()
                       if v not in (None, "", {})},
    }


# -- Vendor adapters ---------------------------------------------------------


def from_gcp(payload) -> list:
    rows = payload if isinstance(payload, list) else payload.get("entries", [payload])
    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        resource = r.get("resource") or {}
        labels = {**(resource.get("labels") or {}), **(r.get("labels") or {})}
        jp = r.get("jsonPayload") or {}
        http = r.get("httpRequest") or {}
        message = (
            jp.get("message")
            or jp.get("msg")
            or r.get("textPayload")
            or (json.dumps(jp) if jp else "")
            or r.get("protoPayload", {}).get("status", {}).get("message", "")
        )
        # "projects/p/traces/abc" -> "abc"
        trace = r.get("trace")
        trace_id = trace.rsplit("/", 1)[-1] if trace else None
        out.append(_entry(
            ts=r.get("timestamp") or r.get("receiveTimestamp"),
            severity=_severity(r.get("severity")),
            service=(labels.get("container_name") or labels.get("service_name")
                     or labels.get("function_name") or labels.get("module_id")
                     or resource.get("type")),
            message=message,
            trace_id=trace_id,
            attributes={
                "span_id": r.get("spanId"),
                "env": labels.get("namespace_name") or labels.get("environment"),
                "resource_type": resource.get("type"),
                "http_status": http.get("status"),
                "http_url": http.get("requestUrl"),
                "latency": http.get("latency"),
                "stack_trace": jp.get("stack_trace") or jp.get("stackTrace"),
                "log_name": r.get("logName"),
            },
        ))
    return out


def from_aws(payload) -> list:
    out = []

    # Shape A: Logs Insights get-query-results -> rows of [{field, value}, ...]
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        for row in payload["results"]:
            if not isinstance(row, list):
                continue
            f = {c.get("field"): c.get("value") for c in row if isinstance(c, dict)}
            consumed = {"@timestamp", "timestamp", "@message", "message", "@logStream",
                        "@log", "@ingestionTime", "@ptr", "level", "severity",
                        "service", "traceId", "trace_id"}
            out.append(_entry(
                ts=f.get("@timestamp") or f.get("timestamp"),
                severity=_severity(f.get("level") or f.get("severity")
                                   or _infer_severity(f.get("@message", ""))),
                service=f.get("service") or f.get("@logStream") or f.get("@log"),
                message=f.get("@message") or f.get("message", ""),
                trace_id=f.get("traceId") or f.get("trace_id"),
                attributes={"log_stream": f.get("@logStream"),
                            **{k: v for k, v in f.items() if k not in consumed}},
            ))
        return out

    # Shape B: filter-log-events / GetLogEvents -> {"events": [...]}
    for e in (payload.get("events") if isinstance(payload, dict) else payload) or []:
        if not isinstance(e, dict):
            continue
        msg = e.get("message", "")
        nested = _try_json(msg)
        out.append(_entry(
            ts=e.get("timestamp"),
            severity=_severity((nested or {}).get("level") or _infer_severity(msg)),
            service=e.get("logStreamName"),
            message=(nested or {}).get("message", msg),
            trace_id=(nested or {}).get("trace_id") or (nested or {}).get("traceId"),
            attributes={"log_stream": e.get("logStreamName"),
                        "event_id": e.get("eventId")},
        ))
    return out


ADAPTERS = {"gcp": from_gcp, "aws": from_aws}


def _try_json(text):
    try:
        v = json.loads(text)
        return v if isinstance(v, dict) else None
    except (TypeError, ValueError):
        return None


def _infer_severity(message: str) -> str:
    m = (message or "").upper()
    for token in ("CRITICAL", "FATAL", "ERROR", "WARN", "DEBUG"):
        if token in m:
            return token
    return "INFO"


def detect_vendor(payload) -> str:
    """Identify the export format from its shape."""
    if isinstance(payload, dict):
        if isinstance(payload.get("results"), list) and payload["results"]:
            first = payload["results"][0]
            if isinstance(first, list) and first and isinstance(first[0], dict) \
                    and "field" in first[0]:
                return "aws"
        if "events" in payload:
            return "aws"
        if "entries" in payload:
            return "gcp"
        payload = [payload]
    if isinstance(payload, list) and payload:
        first = next((r for r in payload if isinstance(r, dict)), None)
        if first:
            if {"insertId", "logName", "jsonPayload", "textPayload", "receiveTimestamp"} \
                    & first.keys():
                return "gcp"
            if isinstance(first.get("resource"), dict) and "type" in first["resource"]:
                return "gcp"
            if {"logStreamName", "ingestionTime"} & first.keys():
                return "aws"
    raise ValueError(
        "Could not detect the log format. Pass --vendor gcp|aws."
    )


def build_bundle(payload, vendor=None, query=None, symptom=None, deploys=None) -> dict:
    vendor = vendor or detect_vendor(payload)
    if vendor not in ADAPTERS:
        raise ValueError(f"Unknown vendor {vendor!r}. Expected one of {sorted(ADAPTERS)}.")
    entries = ADAPTERS[vendor](payload)
    entries.sort(key=lambda e: e["ts"] or "")
    stamped = [e["ts"] for e in entries if e["ts"]]
    counts: dict = {}
    for e in entries:
        counts[e["severity"]] = counts.get(e["severity"], 0) + 1
    return {
        "vendor": vendor,
        "query": query,
        "symptom": symptom,
        "symptom_window": {"start": stamped[0], "end": stamped[-1]} if stamped else None,
        "entry_count": len(entries),
        "severity_counts": counts,
        "trace_ids": sorted({e["trace_id"] for e in entries if e["trace_id"]}),
        "services": sorted({e["service"] for e in entries if e["service"]}),
        "deploys": deploys or [],
        "entries": entries,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Normalize vendor log exports into an evidence bundle.")
    p.add_argument("input", help="Path to the export JSON, or - for stdin.")
    p.add_argument("--vendor", choices=sorted(ADAPTERS), default=None,
                   help="Skip auto-detection.")
    p.add_argument("--query", default=None, help="The query that produced these logs.")
    p.add_argument("--symptom", default=None, help="One line on what looks wrong.")
    p.add_argument("-o", "--out", default=None, help="Write here instead of stdout.")
    args = p.parse_args()

    raw = sys.stdin.read() if args.input == "-" else open(args.input).read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        # Tolerate newline-delimited JSON, which both gcloud and aws can emit.
        payload = [json.loads(line) for line in raw.splitlines() if line.strip()]

    bundle = build_bundle(payload, args.vendor, args.query, args.symptom)
    text = json.dumps(bundle, indent=2)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text + "\n")
        w = bundle["symptom_window"] or {}
        print(f"  {bundle['vendor']} · {bundle['entry_count']} entries · "
              f"{len(bundle['services'])} services · "
              f"{len(bundle['trace_ids'])} traces", file=sys.stderr)
        print(f"  window {w.get('start')} → {w.get('end')}", file=sys.stderr)
        print(f"  wrote {args.out}", file=sys.stderr)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
