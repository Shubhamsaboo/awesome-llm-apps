"""Grounding: is an RCA tied to the log links and code it was given?

Third score, reported beside correctness and quality and never averaged into either.
Most of it is decided in code, not by a judge: whether a cited link was really
attached, whether a cited `path:line` really exists in the attached snippets, whether
a quoted line is verbatim. A string match is not a judgment call, and letting a
judge make it adds variance and lets a fluent invention through.

Inputs live on the evidence bundle (see references/evidence-schema.md):

    "links": [{"url": "https://console.cloud.google.com/logs/query;...", "label": "..."}]
    "code":  [{"path": "src/db/pool.py", "ref": "a1b2c3d", "start_line": 40, "text": "..."}]

What the RCA must do (see references/grounding.md):

    cite a link verbatim ............ as a URL anywhere in the document
    cite code ....................... `path:line` or `path:start-end`, in backticks
    quote code ...................... under "## Code":  - `path:line` — `quoted line` — why

Checks are declared in references/rca-rubric.json under "grounding". Ids marked
`deterministic` there are implemented below; `judged` ones go to the judge.
"""

import re
from typing import Optional

import log_links

# A backticked `token:N` or `token:N-M`. Whether it is a code citation is decided
# afterwards (_is_code_path): `db-primary.internal:5432` matches this shape too.
CODE_CITATION = re.compile(r"`([A-Za-z0-9_./\-]+\.[A-Za-z0-9]+):(\d+)(?:-(\d+))?`")
_CODE_HEADING = re.compile(r"^##\s+Code\s*$", re.MULTILINE | re.IGNORECASE)
_ANY_HEADING = re.compile(r"^##\s+", re.MULTILINE)
_ELLIPSIS = re.compile(r"…|\.\.\.")
# In a `## Code` entry: the separator before the quote, a quote fragment, and the
# ellipsis that may join fragments. Matched in sequence, so a hyphen *inside*
# backticks (`total - used`) is part of the quote, never a separator.
_QUOTE_LEAD = re.compile(r"\s*(?:[—–:\-]+\s*)?")
_QUOTE_FRAGMENT = re.compile(r"`([^`]+)`")
_QUOTE_JOIN = re.compile(r"\s*(?:…|\.\.\.)\s*(?=`)")

# Extensions a source, config or build file can carry. `host.internal:5432` and
# `10.0.4.12:8080` end in something else, so they are never read as code. A cited
# token with a `/` is a file path whatever its extension: hosts have no slashes.
SOURCE_EXTENSIONS = frozenset(
    "py java kt kts go ts tsx js jsx mjs cjs rb rs cs fs vb cpp cc cxx c h hpp m mm sql "
    "scala clj ex exs erl php swift dart lua pl r groovy gradle sbt "
    "yaml yml json jsonc toml ini cfg conf properties env xml xsd plist "
    "tf tfvars hcl sh bash zsh ps1 bat cmd mk cmake proto graphql gql vue svelte "
    "html htm css scss sass less md rst txt lock mod sum dockerfile".split())


def _norm(text: str) -> str:
    return " ".join((text or "").split())


# -- Bundle side --------------------------------------------------------------


def snippets(bundle: Optional[dict]) -> list:
    """Attached code, each with the line range it covers."""
    out = []
    for s in (bundle or {}).get("code") or []:
        lines = (s.get("text") or "").splitlines()
        start = int(s.get("start_line") or 1)
        out.append({"path": s.get("path", ""), "ref": s.get("ref"), "start": start,
                    "end": start + max(len(lines), 1) - 1, "lines": lines})
    return out


def bundle_links(bundle: Optional[dict]) -> list:
    out = []
    for item in (bundle or {}).get("links") or []:
        parsed = log_links.parse_link(item.get("url", ""))
        if parsed:
            out.append(parsed)
    return out


def _same_file(cited: str, attached: str) -> bool:
    """`pool.py` and `db/pool.py` match `src/db/pool.py`. `ool.py` does not, and
    neither does `fake/src/db/pool.py`: a cited path may drop leading directories,
    never add them."""
    cited, attached = cited.lstrip("./"), attached.lstrip("./")
    return cited == attached or attached.endswith("/" + cited)


def _is_code_path(path: str, code: list) -> bool:
    """A cited token is code if it names an attached file or looks like a source file."""
    if any(_same_file(path, s["path"]) for s in code):
        return True
    return "/" in path or path.rsplit(".", 1)[-1].lower() in SOURCE_EXTENSIONS


def _log_text(bundle: Optional[dict]) -> str:
    """Everything the evidence logs say, to recognise stack frames quoted from them."""
    import json

    parts = []
    for e in (bundle or {}).get("entries") or []:
        parts.append(e.get("message") or "")
        parts.append(json.dumps(e.get("attributes") or {}, default=str))
    return "\n".join(parts)


# -- RCA side -----------------------------------------------------------------


def _code_section_span(rca: str) -> Optional[tuple]:
    """(start, end) offsets of the `## Code` section's body, or None."""
    m = _CODE_HEADING.search(rca or "")
    if not m:
        return None
    nxt = _ANY_HEADING.search(rca, m.end())
    return m.end(), (nxt.start() if nxt else len(rca))


def cited_code(rca: str, code: Optional[list] = None) -> list:
    """Code citations in the RCA. Each says whether it sits in the `## Code` section."""
    code = code or []
    span = _code_section_span(rca or "")
    out = []
    for m in CODE_CITATION.finditer(rca or ""):
        if not _is_code_path(m.group(1), code):
            continue  # a host:port, an IP:port, or other non-code token
        start = int(m.group(2))
        out.append({"path": m.group(1), "start": start, "end": int(m.group(3) or start),
                    "text": m.group(0),
                    "in_code_section": bool(span and span[0] <= m.start() < span[1])})
    return out


def code_quotes(rca: str) -> list:
    """(citation, quote) pairs from the `## Code` section.

    Each entry reads `path:line` — `quote` — why. The quote is the backticked run
    right after the citation: one fragment, or several joined by an ellipsis.
    Backticks in the "why" are inline code (`tenant_id`), not a quote. A hyphen
    inside backticks is part of the quote. An entry whose quote cannot be found
    yields quote None, which the verbatim check fails rather than skips.
    Limiting this to the section keeps log messages quoted in the Evidence table
    from being mistaken for code.
    """
    span = _code_section_span(rca or "")
    if not span:
        return []
    pairs = []
    for line in rca[span[0]:span[1]].splitlines():
        cite = CODE_CITATION.search(line)
        if not cite:
            continue
        pos = _QUOTE_LEAD.match(line, cite.end()).end()
        fragments = []
        while True:
            frag = _QUOTE_FRAGMENT.match(line, pos)
            if not frag:
                break
            fragments.append(frag.group(1))
            join = _QUOTE_JOIN.match(line, frag.end())
            if not join:
                break
            pos = join.end()
        pairs.append(({"path": cite.group(1), "start": int(cite.group(2)),
                       "end": int(cite.group(3) or cite.group(2))},
                      fragments or None))
    return pairs


def _range_text(code: list, cite: dict) -> Optional[str]:
    """Attached text for a cited range, or None if no snippet covers it."""
    for s in code:
        if _same_file(cite["path"], s["path"]) and s["start"] <= cite["start"] and cite["end"] <= s["end"]:
            return "\n".join(s["lines"][cite["start"] - s["start"]: cite["end"] - s["start"] + 1])
    return None


# -- Deterministic checks -----------------------------------------------------
# Each returns (verdict, detail). verdict is True, False, or "na" when its
# precondition is absent — "na" leaves the check out of the score entirely.

NA = "na"


def gr_link_cited(rca, bundle):
    attached = bundle_links(bundle)
    if not attached:
        return NA, "no links attached"
    keys = {log_links.link_key(p) for p in attached}
    hit = [p for p in log_links.find_links(rca) if log_links.link_key(p) in keys]
    return bool(hit), (f"cites {len(hit)} attached link(s)" if hit else
                       f"cites none of the {len(attached)} attached link(s)")


def _cited_attached(rca, bundle) -> list:
    keys = {log_links.link_key(p) for p in bundle_links(bundle)}
    return [p for p in log_links.find_links(rca) if log_links.link_key(p) in keys]


def gr_no_invented_link(rca, bundle):
    attached = {log_links.link_key(p) for p in bundle_links(bundle)}
    in_rca = log_links.find_links(rca)
    if not attached and not in_rca:
        return NA, "no links attached or cited"
    invented = [p for p in in_rca if log_links.link_key(p) not in attached]
    return not invented, ("every cited link was attached" if not invented else
                          "cites a link that was never attached: " + log_links.describe(invented[0]))


def gr_link_pinned(rca, bundle):
    cited = _cited_attached(rca, bundle)
    if not cited:
        return NA, "no attached link cited"
    loose = [p for p in cited if not p["pinned"]]
    return not loose, ("all cited links pin an absolute time" if not loose else
                       "relative time range, will show different logs later: " + log_links.describe(loose[0]))


def gr_link_scopes_evidence(rca, bundle):
    cited = _cited_attached(rca, bundle)
    if not cited:
        return NA, "no attached link cited"
    known = set((bundle or {}).get("trace_ids") or [])
    if not known and not (bundle or {}).get("symptom_window"):
        return NA, "no symptom window or trace IDs to compare the links against"
    for p in cited:
        if p["trace_ids"] and known and not (set(p["trace_ids"]) & known):
            return False, f"link filters on trace {p['trace_ids']}, which is not in the evidence"
        if log_links.covers_symptom(p, (bundle or {}).get("symptom_window")) is False:
            return False, "link's time scope does not include the symptom window"
    return True, "cited links cover the symptom window and the evidence's traces"


def gr_code_cited(rca, bundle):
    code = snippets(bundle)
    if not code:
        return NA, "no code attached"
    good = [c for c in cited_code(rca, code) if _range_text(code, c) is not None]
    return bool(good), (f"cites {len(good)} attached location(s)" if good else
                        "cites no location inside the attached code")


def _logged_frame(cite: dict, logs: str) -> bool:
    """The citation is a stack frame the logs contain, token for token.

    A frame names one line, so a range is never one. Boundaries keep `:88` from
    matching inside `:881` and `Client.java` from matching inside `PaymentClient.java`.
    """
    if cite["end"] != cite["start"]:
        return False
    frame = re.escape(f"{cite['path']}:{cite['start']}")
    return re.search(rf"(?<![\w.\-]){frame}(?!\d)", logs) is not None


def gr_no_invented_code(rca, bundle):
    code = snippets(bundle)
    cites = cited_code(rca, code)
    if not code and not cites:
        return NA, "no code attached or cited"
    logs = _log_text(bundle)
    # A stack frame copied from the logs (`PaymentClient.java:88`) is evidence, not
    # an invented citation. Under `## Code` there is no such exemption: that section
    # claims the line was read in the attached code.
    bad = [c for c in cites if _range_text(code, c) is None
           and (c["in_code_section"] or not _logged_frame(c, logs))]
    if not bad:
        return True, "every cited location exists in the attached code"
    c = bad[0]
    where = f"{c['path']}:{c['start']}" + (f"-{c['end']}" if c["end"] != c["start"] else "")
    return False, f"cites {where}, which is not in the attached code"


def gr_quotes_verbatim(rca, bundle):
    pairs = code_quotes(rca)
    if not pairs:
        return NA, "no code quoted under ## Code"
    code = snippets(bundle)
    for cite, fragments in pairs:
        where = f"{cite['path']}:{cite['start']}"
        if not fragments:
            return False, f"{where} under ## Code has no quote in backticks after it"
        quote = " … ".join(fragments)
        text = _range_text(code, cite)
        if text is None:
            return False, f"quotes `{quote[:50]}` from a location that is not attached"
        if not _in_order(text, fragments):
            return False, f"`{quote[:60]}` is not verbatim in {where}"
    return True, "every quoted line is verbatim in the attached code"


def _in_order(text: str, fragments: list) -> bool:
    """Each fragment (and each ellipsis-separated piece of one) appears verbatim,
    whitespace-normalised, after the previous one."""
    haystack, pos = _norm(text), 0
    for fragment in fragments:
        for piece in (_norm(p) for p in _ELLIPSIS.split(fragment)):
            if not piece:
                continue
            at = haystack.find(piece, pos)
            if at < 0:
                return False
            pos = at + len(piece)
    return True


DETERMINISTIC = {f.__name__: f for f in (
    gr_link_cited, gr_no_invented_link, gr_link_pinned, gr_link_scopes_evidence,
    gr_code_cited, gr_no_invented_code, gr_quotes_verbatim)}


def run_deterministic(rca: str, bundle: Optional[dict], spec: dict) -> list:
    out = []
    for c in spec["checks"]:
        if c["kind"] != "deterministic":
            continue
        verdict, detail = DETERMINISTIC[c["id"]](rca, bundle)
        out.append({"id": c["id"], "kind": "deterministic", "passed": verdict, "detail": detail,
                    "question": c["question"], "hard_fail": c["id"] in spec["hard_fail"]})
    return out


# -- Judged checks: applicability and combining -------------------------------


def applicable_judged(bundle: Optional[dict], spec: dict) -> list:
    """Judged checks whose inputs exist on this bundle; the rest are n/a."""
    have = {"code": bool(snippets(bundle)), "links": bool(bundle_links(bundle))}
    return [c for c in spec["checks"] if c["kind"] == "judged" and have[c["requires"]]]


def summarize(det: list, judged: list, spec: dict) -> dict:
    """Fold both kinds into the third score.

    `judged` items: {"id", "passed", "quote"}. Checks absent from both lists are n/a.
    Score is the pass rate over applicable checks, or None when none applies (a
    ticket-only case has nothing to be grounded in, and must not be marked down for it).
    """
    by_id = {c["id"]: c for c in spec["checks"]}
    checks = list(det)
    seen = {c["id"] for c in det}
    for j in judged:
        c = by_id[j["id"]]
        checks.append({"id": j["id"], "kind": "judged", "passed": j["passed"],
                       "detail": j.get("quote", ""), "question": c["question"], "hard_fail": False})
        seen.add(j["id"])
    for c in spec["checks"]:
        if c["id"] not in seen:
            checks.append({"id": c["id"], "kind": c["kind"], "passed": NA,
                           "detail": "inputs not attached", "question": c["question"],
                           "hard_fail": False})
    order = {c["id"]: i for i, c in enumerate(spec["checks"])}
    checks.sort(key=lambda c: order[c["id"]])

    live = [c for c in checks if c["passed"] != NA]
    passed = sum(1 for c in live if c["passed"] is True)
    fabricated = [c["id"] for c in live if c["hard_fail"] and c["passed"] is not True]
    return {
        "score": round(100 * passed / len(live), 1) if live else None,
        "passed": passed,
        "total": len(live),
        "na": len(checks) - len(live),
        "hard_fail": bool(fabricated),
        "fabricated": fabricated,
        "checks": checks,
    }
