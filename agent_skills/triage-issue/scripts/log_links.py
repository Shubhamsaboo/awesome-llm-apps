"""Parse log-explorer links offline, so an eval can judge them without network or credentials.

A Logs Explorer link encodes its whole query in the URL:

    https://console.cloud.google.com/logs/query;query=<urlencoded>;startTime=...;endTime=...?project=<id>

so an RCA that cites one can be checked against the evidence bundle: does the link
pin an absolute time window, does that window cover the symptom, do the trace IDs
in its query belong to the evidence?

One parser per vendor, registered in PARSERS. GCP Logs Explorer is implemented;
a CloudWatch Logs Insights parser slots in beside it without touching callers.

    python scripts/log_links.py '<url>'      # print what a link says
"""

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import parse_qs, unquote, urlsplit

# A link anchored by a cursor but with no explicit window still points at one
# moment. Allow this much slack between that moment and the symptom window.
CURSOR_GRACE = timedelta(minutes=5)

# Stops at whitespace, `<>"` and backticks. `(`, `)` and `'` are allowed, because
# browsers leave them unencoded in queries; a trailing `)` that closes Markdown
# link syntax is trimmed afterwards by _trim().
_GCP_URL = re.compile(r"https://console\.cloud\.google\.com/logs/(?:query|viewer)[^\s<>\"\]`]*")
_GCP_TRACE = re.compile(
    r"""(?:logging\.googleapis\.com/trace|trace)\s*[=:]\s*["']?projects/[^/"'\s]+/traces/([0-9A-Za-z]+)"""
    r"""|jsonPayload\.(?:trace_?[iI]d|traceId)\s*[=:]\s*["']?([0-9A-Za-z-]+)""",
)
_TRAILING = ".,;:'"
# Logs Explorer parameters, which may sit in `;key=value` path segments (current
# links) or in the `?query` string (older and hand-built links).
_PARAMS = ("query", "advancedFilter", "startTime", "endTime", "timeRange",
           "cursorTimestamp", "duration", "project")


def _trim(url: str) -> str:
    """Drop trailing punctuation, and `)` that close an enclosing Markdown link
    rather than a parenthesis opened inside the URL."""
    while url:
        if url[-1] in _TRAILING:
            url = url[:-1]
        elif url.endswith(")") and url.count(")") > url.count("("):
            url = url[:-1]
        else:
            break
    return url


def _iso(value: Optional[str]) -> Optional[datetime]:
    """Parse the timestamp shapes Logs Explorer emits; None if it is not one."""
    if not value:
        return None
    text = re.sub(r"Z$", "+00:00", value.strip())
    text = re.sub(r"(\.\d{6})\d+", r"\1", text)  # trim past microseconds for older Pythons
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _is_duration(value: str) -> bool:
    return bool(re.fullmatch(r"P(?:\d+D)?(?:T(?:\d+H)?(?:\d+M)?(?:\d+S)?)?", value or "")) and value != "P"


def parse_gcp(url: str) -> Optional[dict]:
    """Decode a Logs Explorer URL. Returns None if it is not one."""
    url = _trim(url)
    parts = urlsplit(url)
    if parts.netloc != "console.cloud.google.com" or not parts.path.startswith("/logs/"):
        return None

    params: dict = {}
    for segment in parts.path.split(";")[1:]:
        key, _, value = segment.partition("=")
        params[key] = unquote(value)
    qs = parse_qs(parts.query)
    for key in _PARAMS:
        if key not in params and qs.get(key):
            params[key] = qs[key][0]
    project = params.get("project")

    query = params.get("query") or params.get("advancedFilter") or ""
    trace_ids = sorted({t for m in _GCP_TRACE.finditer(query) for t in m.groups() if t})

    start, end = _iso(params.get("startTime")), _iso(params.get("endTime"))
    time_range = params.get("timeRange", "")
    if not (start and end) and "/" in time_range:
        a, _, b = time_range.partition("/")
        start, end = _iso(a), _iso(b)
    cursor = _iso(params.get("cursorTimestamp"))
    duration = time_range if _is_duration(time_range) else (
        params.get("duration") if _is_duration(params.get("duration", "")) else None)

    # Pinned means the link will show the same logs next week. A bare relative
    # range ("last hour") does not: it moves with the clock.
    pinned = bool(start and end) or cursor is not None
    return {
        "vendor": "gcp",
        "url": url,
        "project": project,
        "query": query,
        "trace_ids": trace_ids,
        "start": start.isoformat() if start else None,
        "end": end.isoformat() if end else None,
        "cursor": cursor.isoformat() if cursor else None,
        "duration": duration,
        "pinned": pinned,
    }


# Vendor registry: pattern that finds this vendor's links in free text, and its parser.
PARSERS = {
    "gcp": (_GCP_URL, parse_gcp),
}


def parse_link(url: str) -> Optional[dict]:
    for _, parser in PARSERS.values():
        parsed = parser(url)
        if parsed:
            return parsed
    return None


def find_links(text: str) -> list:
    """Every recognised log-explorer link in `text`, parsed, in order, de-duplicated."""
    found, seen = [], set()
    for pattern, parser in PARSERS.values():
        for m in pattern.finditer(text or ""):
            parsed = parser(m.group(0))
            if parsed and link_key(parsed) not in seen:
                seen.add(link_key(parsed))
                found.append(parsed)
    return found


def link_key(parsed: dict) -> tuple:
    """Identity of a link by what it shows, so re-encoding the URL does not change it.

    A link with no recognised query falls back to its URL, so two different links
    that both failed to parse can never be mistaken for the same one.
    """
    return (parsed["vendor"], parsed["project"], parsed["query"], parsed["start"],
            parsed["end"], parsed["cursor"], parsed["duration"],
            None if parsed["query"] else parsed["url"])


def round_trips(url: str) -> bool:
    """True if this URL, pasted into an RCA, is found again as the same link.

    A link that does not round-trip could never be cited successfully, so it
    should be rejected when it is attached rather than fail every RCA later.
    """
    parsed = parse_link(url)
    found = find_links(url)
    return bool(parsed) and len(found) == 1 and link_key(found[0]) == link_key(parsed)


def _window(symptom_window: Optional[dict]):
    if not symptom_window:
        return None
    s, e = _iso(symptom_window.get("start")), _iso(symptom_window.get("end"))
    return (s, e) if s and e else None


def covers_symptom(parsed: dict, symptom_window: Optional[dict]) -> Optional[bool]:
    """Does the link's time scope include the symptom window?

    True/False when decidable, None when it is not (no symptom window to compare to,
    or the link has no absolute time at all — `pinned` reports that separately).
    """
    sym = _window(symptom_window)
    if sym is None:
        return None
    s_start, s_end = sym
    start, end = _iso(parsed["start"]), _iso(parsed["end"])
    if start and end:
        return start <= s_end and end >= s_start
    cursor = _iso(parsed["cursor"])
    if cursor:
        return s_start - CURSOR_GRACE <= cursor <= s_end + CURSOR_GRACE
    return None


def describe(parsed: dict) -> str:
    """One line for humans: what a link will show."""
    scope = (f"{parsed['start']} → {parsed['end']}" if parsed["start"] and parsed["end"]
             else f"around {parsed['cursor']}" if parsed["cursor"]
             else f"relative {parsed['duration'] or '(default)'} — not pinned")
    traces = f" · trace {', '.join(parsed['trace_ids'])}" if parsed["trace_ids"] else ""
    return f"{parsed['vendor']} project={parsed['project']} · {scope}{traces} · {parsed['query'][:80]}"


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    parsed = parse_link(sys.argv[1])
    if not parsed:
        print("Not a recognised log-explorer link.", file=sys.stderr)
        return 1
    print(json.dumps(parsed, indent=2))
    print(f"\n  {describe(parsed)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
