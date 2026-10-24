"""OpenTelemetry tracing for the optimizer, plus a local store for human feedback.

Every optimizer run becomes one trace:

    optimizer.session                 one run of the loop
      optimizer.baseline | optimizer.round
        optimizer.score               scores the skill over all scenarios
          llm.call                    one model call (role, backend, prompt, response)

Spans always go to a local SQLite file so the Streamlit "Sessions" tab can show
them. If OTEL_EXPORTER_OTLP_ENDPOINT is set they are also sent to that collector
(Jaeger, Grafana Tempo, Phoenix, ...). Human feedback is stored in the same file
and re-emitted as a `human.feedback` span under the span it rates, so a collector
sees it too.

Prompts and responses are recorded in span attributes (clipped), because without
them a trace cannot tell you why a call routed wrong. They can contain incident
data: set TRIAGE_TRACE_CONTENT=0 to record sizes only.
"""

import json
import os
import sqlite3
import threading
import time
from typing import Optional, Sequence

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
from opentelemetry.trace import Link, NonRecordingSpan, SpanContext, TraceFlags

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB = os.path.join(ROOT, ".traces", "traces.db")
MAX_CONTENT_CHARS = 20_000
FEEDBACK_SPAN = "human.feedback"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS spans (
    span_id TEXT PRIMARY KEY, trace_id TEXT NOT NULL, parent_id TEXT, name TEXT NOT NULL,
    start_ns INTEGER, end_ns INTEGER, status TEXT, attributes TEXT, events TEXT
);
CREATE INDEX IF NOT EXISTS spans_trace ON spans(trace_id);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT, trace_id TEXT NOT NULL, span_id TEXT NOT NULL,
    target TEXT NOT NULL, rating INTEGER, comment TEXT, ts REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS feedback_trace ON feedback(trace_id);
"""


def record_content() -> bool:
    return os.environ.get("TRIAGE_TRACE_CONTENT", "1") != "0"


def clip(text: str, limit: int = MAX_CONTENT_CHARS) -> str:
    text = text or ""
    return text if len(text) <= limit else text[:limit] + f"… [clipped, {len(text)} chars total]"


class Store:
    """SQLite-backed span + feedback store. One short connection per operation, so it
    is safe across Streamlit's script thread, asyncio tasks and the exporter."""

    def __init__(self, path: Optional[str] = None):
        self.path = path or os.environ.get("TRIAGE_TRACE_DB") or DEFAULT_DB
        self._lock = threading.Lock()

    def _connect(self) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        con = sqlite3.connect(self.path, timeout=30)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA journal_mode=WAL")
        con.executescript(_SCHEMA)
        return con

    def _run(self, sql: str, params: Sequence = (), many: bool = False):
        with self._lock:
            con = self._connect()
            try:
                cur = con.executemany(sql, params) if many else con.execute(sql, params)
                rows = cur.fetchall() if cur.description else []
                con.commit()
                return rows
            finally:
                con.close()

    # -- writes --------------------------------------------------------------

    def add_spans(self, rows: list) -> None:
        self._run(
            "INSERT OR REPLACE INTO spans VALUES (?,?,?,?,?,?,?,?,?)", rows, many=True
        )

    def add_feedback(self, trace_id, span_id, target, rating, comment) -> None:
        self._run(
            "INSERT INTO feedback (trace_id, span_id, target, rating, comment, ts) "
            "VALUES (?,?,?,?,?,?)",
            (trace_id, span_id, target, rating, comment or "", time.time()),
        )

    # -- reads ---------------------------------------------------------------

    def spans(self, trace_id: str) -> list:
        out = []
        for r in self._run("SELECT * FROM spans WHERE trace_id=? ORDER BY start_ns", (trace_id,)):
            d = dict(r)
            d["attributes"] = json.loads(d["attributes"] or "{}")
            d["events"] = json.loads(d["events"] or "[]")
            out.append(d)
        return out

    def feedback(self, trace_id: str) -> list:
        return [dict(r) for r in self._run(
            "SELECT * FROM feedback WHERE trace_id=? ORDER BY ts", (trace_id,))]

    def latest_feedback(self, trace_id: str) -> dict:
        """Newest rating per span, so re-rating replaces the old one in the UI."""
        latest: dict = {}
        for f in self.feedback(trace_id):
            latest[f["span_id"]] = f
        return latest

    def sessions(self, limit: int = 50) -> list:
        ids = [r["trace_id"] for r in self._run(
            "SELECT trace_id, MIN(start_ns) AS t FROM spans GROUP BY trace_id "
            "ORDER BY t DESC LIMIT ?", (limit,))]
        out = []
        for tid in ids:
            sp = [s for s in self.spans(tid) if s["name"] != FEEDBACK_SPAN]
            root = next((s for s in sp if s["parent_id"] is None), None)
            calls = [s for s in sp if s["name"] == "llm.call"]
            a = (root or sp[0])["attributes"] if sp else {}
            out.append({
                "trace_id": tid,
                "name": root["name"] if root else "in progress",
                "start_ns": min(s["start_ns"] for s in sp) if sp else 0,
                "end_ns": root["end_ns"] if root else None,
                "model": a.get("gen_ai.request.model") or a.get("triage.model", ""),
                "backend": a.get("triage.backend", ""),
                "calls": len(calls),
                "errors": sum(1 for s in sp if s["status"] == "ERROR"),
                "input_tokens": sum(s["attributes"].get("gen_ai.usage.input_tokens", 0) for s in calls),
                "output_tokens": sum(s["attributes"].get("gen_ai.usage.output_tokens", 0) for s in calls),
                "rated": len(self.latest_feedback(tid)),
            })
        return out


store = Store()


class SQLiteSpanExporter(SpanExporter):
    def export(self, spans) -> SpanExportResult:
        rows = []
        for s in spans:
            ctx = s.get_span_context()
            rows.append((
                format(ctx.span_id, "016x"), format(ctx.trace_id, "032x"),
                format(s.parent.span_id, "016x") if s.parent else None,
                s.name, s.start_time, s.end_time, s.status.status_code.name,
                json.dumps(dict(s.attributes or {}), default=str),
                json.dumps([{"name": e.name, "attributes": dict(e.attributes or {})}
                            for e in s.events], default=str),
            ))
        try:
            store.add_spans(rows)
        except sqlite3.Error:
            return SpanExportResult.FAILURE
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        pass


_init_lock = threading.Lock()
_initialised = False


def init(db_path: Optional[str] = None) -> None:
    """Idempotent. Safe to call on every Streamlit rerun and from every CLI."""
    global _initialised
    if db_path:
        store.path = db_path
    with _init_lock:
        if _initialised:
            return
        provider = TracerProvider(resource=Resource.create({"service.name": "triage-agent"}))
        # Simple (synchronous) for SQLite: volume is a few calls a second at most,
        # and the Sessions tab should see a finished call immediately.
        provider.add_span_processor(SimpleSpanProcessor(SQLiteSpanExporter()))
        if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") or os.environ.get(
                "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"):
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        trace.set_tracer_provider(provider)
        _initialised = True


def tracer() -> trace.Tracer:
    init()
    return trace.get_tracer("triage-agent")


def span(name: str, **attributes):
    """`with span("optimizer.round", round=3) as sp:` — current span for child calls."""
    return tracer().start_as_current_span(
        name, attributes={k: v for k, v in attributes.items() if v is not None})


def record_feedback(trace_id: str, span_id: str, target: str, rating: Optional[int],
                    comment: str = "") -> None:
    """Save feedback on a span and emit it as a `human.feedback` child span.

    rating: 1 = good, 0 = bad, None = comment only. target: call | round | session.
    """
    init()
    store.add_feedback(trace_id, span_id, target, rating, comment)
    target_ctx = SpanContext(
        trace_id=int(trace_id, 16), span_id=int(span_id, 16), is_remote=True,
        trace_flags=TraceFlags(TraceFlags.SAMPLED),
    )
    parent = trace.set_span_in_context(NonRecordingSpan(target_ctx))
    with tracer().start_as_current_span(
        FEEDBACK_SPAN, context=parent, links=[Link(target_ctx)],
        attributes={
            "feedback.target": target,
            "feedback.rating": -1 if rating is None else rating,
            "feedback.comment": comment or "",
            "feedback.target_span_id": span_id,
        },
    ):
        pass
