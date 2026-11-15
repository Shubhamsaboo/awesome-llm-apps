"""Model judgment for Page Watch hunks, with a deterministic pre-filter.

Sample mode uses recorded fixture judgments and makes no network or model
calls. Live mode calls Gemini with the same model name as the ADK agent.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any

try:
    from .watch import Hunk, detect_numeric_changes, prefilter_hunk
except ImportError:
    from watch import Hunk, detect_numeric_changes, prefilter_hunk


GEMINI_MODEL = "gemini-3-flash-preview"
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

IMPACT_TAGS = (
    "pricing",
    "limits",
    "legal",
    "deprecation",
    "availability",
    "other",
)


@dataclass(frozen=True)
class Judgment:
    hunk_id: str
    page_name: str
    page_url: str
    kind: str
    classification: str
    summary: str
    before: str
    after: str
    impact: str
    prefilter_verdict: str
    prefilter_reasons: tuple[str, ...]
    source: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["prefilter_reasons"] = list(self.prefilter_reasons)
        return payload


# Recorded fixture judgments for the sample pricing, docs, and terms pages.
# Matching is by page name plus a distinctive substring of the hunk text.
SAMPLE_JUDGMENTS = [
    {
        "page_substr": "pricing",
        "text_substr": "per month",
        "classification": "material",
        "summary": "The Pro plan monthly price increased from $29 to $49.",
        "impact": "pricing",
    },
    {
        "page_substr": "pricing",
        "text_substr": "rate limit",
        "classification": "material",
        "summary": "The Pro plan rate limit dropped from 100 to 60 requests per minute.",
        "impact": "limits",
    },
    {
        "page_substr": "terms",
        "text_substr": "arbitration",
        "classification": "material",
        "summary": "A new clause sends disputes to binding arbitration in Delaware and waives class actions.",
        "impact": "legal",
    },
    {
        "page_substr": "docs",
        "text_substr": "",
        "classification": "cosmetic",
        "summary": "Only footer chrome changed; the documented API is the same.",
        "impact": "other",
    },
]


def _hunk_text(hunk: Hunk) -> str:
    return f"{hunk.before}\n{hunk.after}"


def recorded_judgment(hunk: Hunk) -> dict[str, str] | None:
    """Return a recorded fixture judgment for a sample-page hunk."""

    page = hunk.page_name.lower()
    blob = _hunk_text(hunk).lower()
    for record in SAMPLE_JUDGMENTS:
        if record["page_substr"] not in page:
            continue
        needle = record["text_substr"].lower()
        if needle and needle not in blob:
            continue
        if not needle and record["page_substr"] != "docs":
            continue
        return {
            "classification": record["classification"],
            "summary": record["summary"],
            "impact": record["impact"],
        }
    return None


def _fallback_from_prefilter(
    hunk: Hunk,
    verdict: str,
    reasons: tuple[str, ...],
) -> dict[str, str]:
    if verdict == "likely_material":
        numeric = detect_numeric_changes(hunk.before, hunk.after)
        if numeric:
            old, new = numeric[0]
            summary = f"A numeric value changed from {old} to {new}."
        elif hunk.kind == "added":
            summary = "New text appeared on the watched page."
        elif hunk.kind == "removed":
            summary = "Watched text was removed from the page."
        else:
            summary = "Watched text changed in a way the pre-filter treats as material."
        impact = "other"
        blob = _hunk_text(hunk).lower()
        if "price" in blob or "$" in _hunk_text(hunk):
            impact = "pricing"
        elif "limit" in blob or "quota" in blob:
            impact = "limits"
        elif "deprecat" in blob:
            impact = "deprecation"
        elif "arbitration" in blob or "liability" in blob or "terms" in blob:
            impact = "legal"
        return {"classification": "material", "summary": summary, "impact": impact}
    return {
        "classification": "cosmetic",
        "summary": "This looks like a non-substantive wording or chrome change.",
        "impact": "other",
    }


def _parse_model_json(text: str) -> dict[str, str] | None:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    classification = str(payload.get("classification") or "").strip().lower()
    if classification not in {"material", "cosmetic"}:
        return None
    impact = str(payload.get("impact") or "other").strip().lower()
    if impact not in IMPACT_TAGS:
        impact = "other"
    summary = str(payload.get("summary") or "").strip()
    if not summary:
        return None
    return {
        "classification": classification,
        "summary": summary,
        "impact": impact,
    }


def _gemini_api_key() -> str | None:
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or None


def call_gemini_for_hunk(
    hunk: Hunk,
    *,
    keywords: tuple[str, ...],
    prefilter_verdict: str,
    prefilter_reasons: tuple[str, ...],
) -> dict[str, str]:
    """Ask Gemini to classify one hunk. Raises RuntimeError on transport failure."""

    api_key = _gemini_api_key()
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set.")
    prompt = (
        "Classify one webpage change hunk. Reply with JSON only:\n"
        '{"classification":"material"|"cosmetic","summary":"one sentence",'
        '"impact":"pricing"|"limits"|"legal"|"deprecation"|"availability"|"other"}\n'
        "Material means a reader who depends on this page should act. Cosmetic means "
        "chrome, timestamps, or wording that does not change the deal.\n"
        "Quote nothing; the caller already has the exact before/after text.\n\n"
        f"Page: {hunk.page_name} ({hunk.page_url})\n"
        f"Kind: {hunk.kind}\n"
        f"Before: {hunk.before or '(none)'}\n"
        f"After: {hunk.after or '(none)'}\n"
        f"Prefilter: {prefilter_verdict} ({', '.join(prefilter_reasons) or 'none'})\n"
        f"Keywords: {', '.join(keywords)}\n"
    )
    body = json.dumps(
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "maxOutputTokens": 256},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{GEMINI_ENDPOINT}?key={urllib.parse.quote(api_key)}",
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "page-watch-agent/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Gemini request failed: {exc}") from exc
    candidates = payload.get("candidates") if isinstance(payload, dict) else None
    if not candidates:
        raise RuntimeError("Gemini returned no candidates.")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(str(part.get("text") or "") for part in parts if isinstance(part, dict))
    parsed = _parse_model_json(text)
    if parsed is None:
        raise RuntimeError("Gemini returned JSON that Page Watch could not parse.")
    return parsed


def judge_hunks(
    hunks: list[Hunk],
    *,
    keywords: tuple[str, ...],
    sample: bool = True,
) -> list[Judgment]:
    """Classify hunks. Sample mode never opens a network connection."""

    judgments: list[Judgment] = []
    for hunk in hunks:
        verdict, reasons = prefilter_hunk(hunk, keywords)
        source = "sample"
        if sample:
            recorded = recorded_judgment(hunk)
            decision = recorded or _fallback_from_prefilter(hunk, verdict, reasons)
            if recorded is None:
                source = "sample_fallback"
        else:
            try:
                decision = call_gemini_for_hunk(
                    hunk,
                    keywords=keywords,
                    prefilter_verdict=verdict,
                    prefilter_reasons=reasons,
                )
                source = "gemini"
            except RuntimeError:
                decision = _fallback_from_prefilter(hunk, verdict, reasons)
                source = "prefilter_fallback"
        judgments.append(
            Judgment(
                hunk_id=hunk.hunk_id,
                page_name=hunk.page_name,
                page_url=hunk.page_url,
                kind=hunk.kind,
                classification=decision["classification"],
                summary=decision["summary"],
                before=hunk.before,
                after=hunk.after,
                impact=decision["impact"],
                prefilter_verdict=verdict,
                prefilter_reasons=reasons,
                source=source,
            )
        )
    return judgments
