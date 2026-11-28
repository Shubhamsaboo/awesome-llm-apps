"""Deterministic, zero-API-key claim verification against source PDF pages.

Verifies three classes of claims directly against extracted PDF text:
1. Verbatim quotes (normalized exact match + wrong-page citation detection).
2. Numeric values (currency, commas, parenthesized negatives, and scale headers).
3. Symbolic formulas via safe Python AST arithmetic (no eval/exec), requiring
   every operand to be grounded on its cited page before recomputing.
"""

from __future__ import annotations

import ast
import difflib
import math
import operator
import re
from dataclasses import asdict, dataclass, field
from typing import Any

from pdf_navigator import PDFDocumentIndex

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_MAX_EXPR_CHARS = 500
_MAX_POW_BASE = 1e12
_MAX_POW_EXPONENT = 100.0
_NUM_LIT_RE = re.compile(r"\d+(?:\.\d+)?%?|\.\d+%?")

_SCALE_WORDS = {
    "k": 1e3,
    "thousand": 1e3,
    "m": 1e6,
    "mn": 1e6,
    "million": 1e6,
    "b": 1e9,
    "bn": 1e9,
    "billion": 1e9,
    "t": 1e12,
    "trillion": 1e12,
}

_PAGE_SCALE_RE = re.compile(
    r"\b(?:in\s+)?(thousands|millions|billions)\b",
    re.IGNORECASE,
)

_NUMBER_TOKEN_RE = re.compile(
    r"(?P<neg_open>\()?\s*"
    r"(?P<currency>[$€£¥])?\s*"
    r"(?P<sign>[+-])?"
    r"(?P<digits>\d{1,3}(?:,\d{3})+|\d+)(?P<frac>\.\d+)?"
    r"(?P<pct>%)?"
    r"(?:\s*(?P<scale>trillion|billion|million|thousand|bn|mn|[kmb])\b)?"
    r"\s*(?P<neg_close>\))?",
    re.IGNORECASE,
)


@dataclass
class VerificationResult:
    """Structured result emitted by all deterministic verification checks."""

    kind: str  # "quote" | "number" | "formula"
    status: str  # "verified" | "unverified" | "mismatch" | "unverified_operand" | "invalid_formula"
    detail: str
    page: int | None = None
    evidence: str = ""
    computed_value: float | None = None
    claimed_value: float | None = None
    operand_checks: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_text(text: str) -> str:
    """Normalize PDF line wraps, smart quotes, dashes, and whitespace for quote checks."""
    s = text or ""
    # Rejoin hyphenated line breaks produced by PDF column wrapping
    s = re.sub(r"-\s*\n\s*", "-", s)
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\u00a0": " ",
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def verify_quote(
    index: PDFDocumentIndex,
    quote: str,
    page: int,
    min_chars: int = 8,
) -> VerificationResult:
    """Verify that a claimed quote appears verbatim on the cited 1-based page."""
    clean_quote = normalize_text(quote)
    if len(clean_quote) < min_chars:
        return VerificationResult(
            kind="quote",
            status="unverified",
            page=page,
            detail=f"Quote is too short ({len(clean_quote)} chars; minimum {min_chars}) to verify reliably.",
        )

    page_text = index.get_page_text(page)
    if page_text is None:
        return VerificationResult(
            kind="quote",
            status="unverified",
            page=page,
            detail=f"Cited page {page} is out of range (document has {index.num_pages} pages).",
        )

    norm_page = normalize_text(page_text)
    pos = norm_page.find(clean_quote)
    if pos != -1:
        start = max(0, pos - 40)
        end = min(len(norm_page), pos + len(clean_quote) + 40)
        return VerificationResult(
            kind="quote",
            status="verified",
            page=page,
            detail=f"Verbatim quote verified on page {page}.",
            evidence=norm_page[start:end],
        )

    # Detect wrong-page citations: check whether the exact quote exists elsewhere
    other_pages = [
        p
        for p in range(1, index.num_pages + 1)
        if p != page and clean_quote in normalize_text(index.pages[p - 1])
    ]
    if other_pages:
        return VerificationResult(
            kind="quote",
            status="unverified",
            page=page,
            detail=(
                f"Wrong page citation: quote was NOT found on page {page}, "
                f"but appears verbatim on page(s) {other_pages[:3]}."
            ),
        )

    # Otherwise report closest line on the cited page for human inspection
    lines = [ln.strip() for ln in page_text.splitlines() if ln.strip()]
    best_line = ""
    best_ratio = 0.0
    for ln in lines:
        ratio = difflib.SequenceMatcher(None, clean_quote, normalize_text(ln)).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_line = ln
    return VerificationResult(
        kind="quote",
        status="unverified",
        page=page,
        detail=(
            f"Quote not found verbatim on page {page} "
            f"(closest line similarity: {best_ratio:.0%})."
        ),
        evidence=best_line[:220],
    )


def _page_scale_multipliers(page_text: str) -> list[float]:
    """Detect table-level unit headers like '($ in millions)' on a page."""
    scales = [1.0]
    for m in _PAGE_SCALE_RE.finditer(page_text or ""):
        word = m.group(1).lower().rstrip("s")
        mult = _SCALE_WORDS.get(word)
        if mult and mult not in scales:
            scales.append(mult)
    return scales


def extract_numbers_from_text(page_text: str) -> list[tuple[float, str]]:
    """Extract numeric candidates (value, source_snippet) including unit-scaled forms."""
    results: list[tuple[float, str]] = []
    page_scales = _page_scale_multipliers(page_text)

    for m in _NUMBER_TOKEN_RE.finditer(page_text or ""):
        digits = (m.group("digits") or "").replace(",", "")
        frac = m.group("frac") or ""
        if not digits:
            continue
        try:
            base = float(digits + frac)
        except ValueError:
            continue

        is_neg = m.group("sign") == "-" or (bool(m.group("neg_open")) and bool(m.group("neg_close")))
        if is_neg:
            base = -base

        snippet_start = max(0, m.start() - 35)
        snippet_end = min(len(page_text), m.end() + 35)
        snippet = re.sub(r"\s+", " ", page_text[snippet_start:snippet_end]).strip()

        scale_tok = (m.group("scale") or "").lower()
        is_pct = bool(m.group("pct"))

        # Always record the raw literal value as written on the page
        results.append((base, snippet))
        if is_pct:
            # Allow comparing "40%" against either 40.0 or 0.40
            results.append((base / 100.0, snippet))
        if scale_tok in _SCALE_WORDS:
            results.append((base * _SCALE_WORDS[scale_tok], snippet))
        elif not is_pct and len(page_scales) > 1:
            for mult in page_scales[1:]:
                results.append((base * mult, snippet))

    return results


def _numbers_match(a: float, b: float, rel_tol: float = 1e-3, abs_tol: float = 1e-6) -> bool:
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)


def verify_number(
    index: PDFDocumentIndex,
    value: float,
    page: int,
    rel_tol: float = 1e-3,
) -> VerificationResult:
    """Verify that a numeric value is grounded on the cited 1-based page."""
    try:
        target = float(value)
    except (TypeError, ValueError):
        return VerificationResult(
            kind="number",
            status="unverified",
            page=page,
            detail=f"Claimed value {value!r} is not a valid number.",
        )

    page_text = index.get_page_text(page)
    if page_text is None:
        return VerificationResult(
            kind="number",
            status="unverified",
            page=page,
            claimed_value=target,
            detail=f"Cited page {page} is out of range (document has {index.num_pages} pages).",
        )

    candidates = extract_numbers_from_text(page_text)
    for cand_val, snippet in candidates:
        if _numbers_match(cand_val, target, rel_tol=rel_tol):
            return VerificationResult(
                kind="number",
                status="verified",
                page=page,
                claimed_value=target,
                computed_value=cand_val,
                detail=f"Value {target:g} verified on page {page}.",
                evidence=snippet,
            )

    return VerificationResult(
        kind="number",
        status="unverified",
        page=page,
        claimed_value=target,
        detail=f"Value {target:g} was not found on page {page}.",
    )


def normalize_expression(expr: str) -> str:
    """Normalize arithmetic operators, currency symbols, commas, and percentages."""
    s = (expr or "").strip()
    for old, new in (
        ("\u2212", "-"),
        ("\u2013", "-"),
        ("\u2014", "-"),
        ("\u00d7", "*"),
        ("\u00f7", "/"),
        ("^", "**"),
    ):
        s = s.replace(old, new)
    s = re.sub(r"(?<=\d),(?=\d{3}\b)", "", s)
    s = s.replace(",", "").replace("$", "").replace("¥", "").replace("€", "").replace("£", "")
    lits = _NUM_LIT_RE.findall(s)
    if lits and "%" in s:
        if all(x.endswith("%") for x in lits):
            s = s.replace("%", "")
        else:
            s = re.sub(r"(\d+(?:\.\d+)?|\.\d+)%", r"(\1/100)", s)
    return s


def safe_calc(expr: str, variables: dict[str, float] | None = None) -> float | None:
    """Evaluate a pure arithmetic expression via Python AST (zero eval/exec risk).

    Supports +, -, *, /, unary signs, bounded **, and optional explicit numeric variables.
    Rejects attribute access, function calls, imports, and unbounded exponentiation.
    """
    s = normalize_expression(expr)
    if not s or len(s) > _MAX_EXPR_CHARS:
        return None
    allowed_vars = {k: float(v) for k, v in (variables or {}).items()}
    try:
        tree = ast.parse(s, mode="eval").body
    except SyntaxError:
        return None

    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return float(node.value)
        if isinstance(node, ast.Name) and node.id in allowed_vars:
            return allowed_vars[node.id]
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.operand))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            base, exp = _eval(node.left), _eval(node.right)
            if abs(base) > _MAX_POW_BASE or abs(exp) > _MAX_POW_EXPONENT:
                raise ValueError("Exponentiation out of bounds")
            if base < 0 and not float(exp).is_integer():
                raise ValueError("Complex power not supported")
            if base == 0 and exp < 0:
                raise ZeroDivisionError("Zero raised to negative power")
            return float(base**exp)
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            rhs = _eval(node.right)
            if isinstance(node.op, ast.Div) and abs(rhs) < 1e-12:
                raise ZeroDivisionError("Division by zero")
            return _OPS[type(node.op)](_eval(node.left), rhs)
        raise ValueError(f"Unsupported AST node: {type(node).__name__}")

    try:
        val = _eval(tree)
    except Exception:
        return None
    return val if math.isfinite(val) else None


def verify_formula(
    index: PDFDocumentIndex,
    formula: str,
    operands: dict[str, dict[str, Any]],
    claimed_result: float,
    rel_tol: float = 1e-2,
) -> VerificationResult:
    """Verify every operand against its cited PDF page, then recompute the formula via AST.

    ``operands`` maps variable names in ``formula`` to ``{"value": float, "page": int}``.
    """
    try:
        claimed = float(claimed_result)
    except (TypeError, ValueError):
        return VerificationResult(
            kind="formula",
            status="invalid_formula",
            detail=f"Claimed result {claimed_result!r} is not numeric.",
        )

    if not operands:
        return VerificationResult(
            kind="formula",
            status="unverified_operand",
            claimed_value=claimed,
            detail="Formula verification requires at least one page-cited operand.",
        )

    operand_checks: dict[str, dict[str, Any]] = {}
    verified_vars: dict[str, float] = {}
    failed_names: list[str] = []

    for name, spec in operands.items():
        if not isinstance(spec, dict) or "value" not in spec or "page" not in spec:
            failed_names.append(name)
            operand_checks[name] = {
                "status": "unverified",
                "detail": "Operand must specify both 'value' and 'page'.",
            }
            continue
        try:
            op_val = float(spec["value"])
            op_page = int(spec["page"])
        except (TypeError, ValueError):
            failed_names.append(name)
            operand_checks[name] = {
                "status": "unverified",
                "detail": "Operand value/page could not be parsed as numeric.",
            }
            continue

        check = verify_number(index, op_val, op_page)
        operand_checks[name] = check.to_dict()
        if check.status != "verified":
            failed_names.append(name)
        else:
            verified_vars[name] = op_val

    if failed_names:
        return VerificationResult(
            kind="formula",
            status="unverified_operand",
            claimed_value=claimed,
            operand_checks=operand_checks,
            detail=(
                f"Cannot verify formula because operand(s) {failed_names} "
                "were not found on their cited PDF pages."
            ),
        )

    computed = safe_calc(formula, variables=verified_vars)
    if computed is None:
        return VerificationResult(
            kind="formula",
            status="invalid_formula",
            claimed_value=claimed,
            operand_checks=operand_checks,
            detail=f"Formula {formula!r} could not be safely evaluated with operands {list(verified_vars)}.",
        )

    # Accept exact match OR percent-vs-decimal equivalent (e.g. 0.40 vs 40.0)
    matches = _numbers_match(computed, claimed, rel_tol=rel_tol, abs_tol=1e-4) or (
        abs(computed) <= 1.0 and _numbers_match(computed * 100.0, claimed, rel_tol=rel_tol, abs_tol=1e-4)
    )
    if matches:
        return VerificationResult(
            kind="formula",
            status="verified",
            claimed_value=claimed,
            computed_value=round(computed, 6),
            operand_checks=operand_checks,
            detail=(
                f"All {len(verified_vars)} operands verified on source pages; "
                f"recomputed {formula} = {computed:.6g} matches claimed {claimed:g}."
            ),
        )

    return VerificationResult(
        kind="formula",
        status="mismatch",
        claimed_value=claimed,
        computed_value=round(computed, 6),
        operand_checks=operand_checks,
        detail=(
            f"Arithmetic mismatch: operands verified on source pages, "
            f"but {formula} evaluates to {computed:.6g} (claimed {claimed:g})."
        ),
    )
