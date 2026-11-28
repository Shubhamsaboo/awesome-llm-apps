"""Zero-vector-DB structural PDF indexing and token-bounded progressive navigation.

Uses PyMuPDF (``pymupdf``) and the Python standard library to:
1. Extract a compact structural outline (embedded PDF bookmarks with a font-size
   heading heuristic fallback).
2. Index pages in memory with lightweight BM25 lexical scoring (English + CJK).
3. Serve bounded progressive reads: outline -> search snippets -> exact pages.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pymupdf

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:[._/-][A-Za-z0-9]+)*|[\u4e00-\u9fff]")
_HEADING_NUM_RE = re.compile(
    r"^(?:(?:chapter|section|part|item|appendix)\s+[A-Z0-9]+|\d+(?:\.\d+){0,3}\s+\S)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class OutlineNode:
    """A structural section mapped to 1-based inclusive PDF page bounds."""

    section_id: str
    title: str
    level: int
    start_page: int
    end_page: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SearchHit:
    """A single BM25 search result with section context and a bounded snippet."""

    page: int
    score: float
    section: str
    snippet: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def tokenize(text: str) -> list[str]:
    """Tokenize English words, numbers, and CJK unigrams/bigrams for BM25."""
    raw = _TOKEN_RE.findall((text or "").lower())
    tokens: list[str] = []
    cjk_run: list[str] = []
    for tok in raw:
        if len(tok) == 1 and "\u4e00" <= tok <= "\u9fff":
            tokens.append(tok)
            cjk_run.append(tok)
            if len(cjk_run) >= 2:
                tokens.append(cjk_run[-2] + cjk_run[-1])
        else:
            cjk_run.clear()
            tokens.append(tok)
    return tokens


def _extract_outline(doc: pymupdf.Document) -> list[OutlineNode]:
    """Extract PDF bookmarks, falling back to font-size heading inference."""
    num_pages = doc.page_count
    raw_entries: list[tuple[int, str, int]] = []

    toc = doc.get_toc(simple=True) or []
    for entry in toc:
        if len(entry) < 3:
            continue
        level, title, page = int(entry[0]), str(entry[1]).strip(), int(entry[2])
        if title and 1 <= page <= num_pages:
            raw_entries.append((max(1, level), title[:140], page))

    if not raw_entries:
        raw_entries = _infer_headings_from_fonts(doc)

    if not raw_entries:
        step = 10 if num_pages > 20 else max(1, math.ceil(num_pages / 4))
        nodes: list[OutlineNode] = []
        idx = 1
        for start in range(1, num_pages + 1, step):
            end = min(num_pages, start + step - 1)
            label = f"Pages {start}-{end}" if start != end else f"Page {start}"
            nodes.append(OutlineNode(f"S{idx}", label, 1, start, end))
            idx += 1
        return nodes

    nodes = []
    for i, (level, title, start_page) in enumerate(raw_entries):
        end_page = num_pages
        for j in range(i + 1, len(raw_entries)):
            next_level, _, next_page = raw_entries[j]
            if next_level <= level and next_page >= start_page:
                end_page = max(start_page, next_page - 1 if next_page > start_page else next_page)
                break
        nodes.append(OutlineNode(f"S{i + 1}", title, level, start_page, end_page))
    return nodes


def _infer_headings_from_fonts(doc: pymupdf.Document, max_headings: int = 80) -> list[tuple[int, str, int]]:
    """Heuristic fallback when a PDF lacks embedded TOC bookmarks."""
    size_char_weights: Counter[float] = Counter()
    candidates: list[tuple[float, bool, str, int]] = []

    for page_idx in range(doc.page_count):
        page_dict = doc[page_idx].get_text("dict")
        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                spans = [s for s in line.get("spans", []) if str(s.get("text", "")).strip()]
                if not spans:
                    continue
                line_text = " ".join(str(s["text"]).strip() for s in spans).strip()
                max_size = max(float(s.get("size", 0.0)) for s in spans)
                is_bold = any(bool(int(s.get("flags", 0)) & 16) for s in spans)
                bucket = round(max_size * 2.0) / 2.0
                size_char_weights[bucket] += len(line_text)
                if 3 <= len(line_text) <= 110:
                    candidates.append((max_size, is_bold, line_text, page_idx + 1))

    if not size_char_weights:
        return []

    body_size = size_char_weights.most_common(1)[0][0]
    threshold = max(body_size * 1.15, body_size + 1.5)

    out: list[tuple[int, str, int]] = []
    seen: set[tuple[str, int]] = set()
    for size, is_bold, text, page_no in candidates:
        is_heading = size >= threshold or (is_bold and _HEADING_NUM_RE.match(text))
        if not is_heading:
            continue
        key = (text.lower(), page_no)
        if key in seen:
            continue
        seen.add(key)
        level = 1 if size >= body_size * 1.35 else 2
        out.append((level, text, page_no))
        if len(out) >= max_headings:
            break
    return out


class PDFDocumentIndex:
    """In-memory structural + BM25 index over a single PDF document."""

    def __init__(self, name: str, pages: list[str], outline: list[OutlineNode]) -> None:
        self.name = name
        self.pages = pages  # 0-indexed list; external APIs use 1-based page numbers
        self.outline = outline

        self._page_tokens = [tokenize(p) for p in pages]
        self._page_tf = [Counter(toks) for toks in self._page_tokens]
        self._doc_freq: Counter[str] = Counter()
        for tf in self._page_tf:
            for tok in tf:
                self._doc_freq[tok] += 1
        total_len = sum(len(t) for t in self._page_tokens)
        self._avg_len = (total_len / len(pages)) if pages else 1.0

    @property
    def num_pages(self) -> int:
        return len(self.pages)

    @classmethod
    def from_bytes(cls, pdf_bytes: bytes, name: str = "document.pdf") -> "PDFDocumentIndex":
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        try:
            pages = [doc[i].get_text("text") or "" for i in range(doc.page_count)]
            outline = _extract_outline(doc)
        finally:
            doc.close()
        return cls(name=name, pages=pages, outline=outline)

    @classmethod
    def from_file(cls, path: str | Path) -> "PDFDocumentIndex":
        p = Path(path)
        return cls.from_bytes(p.read_bytes(), name=p.name)

    def section_for_page(self, page: int) -> str:
        """Return the deepest outline section title covering a 1-based page."""
        matches = [n for n in self.outline if n.start_page <= page <= n.end_page]
        if not matches:
            return f"Page {page}"
        best = max(matches, key=lambda n: (n.level, n.start_page))
        return f"{best.section_id}: {best.title}"

    def get_outline(self, max_nodes: int = 80) -> dict[str, Any]:
        """Step 1 of progressive reading: inspect document map without loading body text."""
        capped = self.outline[: max(1, max_nodes)]
        return {
            "document": self.name,
            "num_pages": self.num_pages,
            "total_sections": len(self.outline),
            "truncated": len(self.outline) > len(capped),
            "sections": [n.to_dict() for n in capped],
        }

    def search_pages(
        self,
        query: str,
        top_k: int = 5,
        snippet_chars: int = 280,
    ) -> dict[str, Any]:
        """Step 2 of progressive reading: BM25 lexical search returning bounded snippets."""
        q_tokens = tokenize(query)
        if not q_tokens or not self.pages:
            return {"query": query, "hits": []}

        n_docs = len(self.pages)
        k1, b = 1.5, 0.75
        scored: list[tuple[float, int]] = []

        for idx, tf in enumerate(self._page_tf):
            doc_len = len(self._page_tokens[idx])
            score = 0.0
            for tok in q_tokens:
                freq = tf.get(tok, 0)
                if freq <= 0:
                    continue
                df = self._doc_freq.get(tok, 0)
                idf = math.log((n_docs - df + 0.5) / (df + 0.5) + 1.0)
                denom = freq + k1 * (1.0 - b + b * (doc_len / max(1.0, self._avg_len)))
                score += idf * ((freq * (k1 + 1.0)) / denom)
            if score > 0:
                scored.append((score, idx + 1))

        scored.sort(key=lambda pair: (-pair[0], pair[1]))
        hits: list[SearchHit] = []
        for score, page_no in scored[: max(1, min(top_k, 15))]:
            snippet = self._build_snippet(self.pages[page_no - 1], q_tokens, snippet_chars)
            hits.append(
                SearchHit(
                    page=page_no,
                    score=round(score, 3),
                    section=self.section_for_page(page_no),
                    snippet=snippet,
                )
            )
        return {"query": query, "hits": [h.to_dict() for h in hits]}

    def read_pages(
        self,
        pages: list[int],
        max_pages: int = 6,
        max_chars_per_page: int = 3500,
    ) -> dict[str, Any]:
        """Step 3 of progressive reading: load exact bounded pages on demand."""
        valid: list[int] = []
        invalid: list[int] = []
        seen: set[int] = set()
        for raw_p in pages:
            try:
                p = int(raw_p)
            except (TypeError, ValueError):
                continue
            if 1 <= p <= self.num_pages:
                if p not in seen:
                    seen.add(p)
                    valid.append(p)
            else:
                invalid.append(p)

        selected = valid[: max(1, max_pages)]
        items = []
        for p in selected:
            raw_text = self.pages[p - 1].strip()
            truncated = len(raw_text) > max_chars_per_page
            text = raw_text[:max_chars_per_page]
            if truncated:
                text += "\n... [truncated for context budget]"
            items.append(
                {
                    "page": p,
                    "section": self.section_for_page(p),
                    "truncated": truncated,
                    "text": text,
                }
            )
        return {
            "pages_read": selected,
            "skipped_pages": valid[len(selected) :],
            "out_of_range_pages": invalid,
            "content": items,
        }

    def get_page_text(self, page: int) -> str | None:
        if 1 <= page <= self.num_pages:
            return self.pages[page - 1]
        return None

    @staticmethod
    def _build_snippet(page_text: str, q_tokens: list[str], max_chars: int) -> str:
        compact = re.sub(r"\s+", " ", page_text or "").strip()
        if not compact:
            return ""
        low = compact.lower()
        pos = -1
        for tok in sorted(set(q_tokens), key=len, reverse=True):
            idx = low.find(tok)
            if idx != -1:
                pos = idx
                break
        if pos == -1:
            return compact[:max_chars] + ("..." if len(compact) > max_chars else "")
        start = max(0, pos - max_chars // 3)
        end = min(len(compact), start + max_chars)
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(compact) else ""
        return f"{prefix}{compact[start:end].strip()}{suffix}"


def build_sample_financial_pdf() -> bytes:
    """Generate a realistic 4-page sample annual report PDF for zero-setup demos and tests."""
    doc = pymupdf.open()
    pages_spec = [
        (
            "1. Executive Summary",
            [
                "Acme Robotics Inc. — FY2025 Annual Report",
                "",
                "1. Executive Summary",
                "In fiscal year 2025, Acme Robotics delivered record industrial automation demand",
                "across North America and Europe. Total consolidated revenue reached $480.0 million,",
                "representing a 20.0% increase over FY2024 revenue of $400.0 million.",
                "",
                "Management Quote:",
                "\"All factory deployments met our 99.4% uptime SLA while reducing unit assembly cost",
                "by 14.5% year-over-year.\"",
                "",
                "Headcount ended FY2025 at 1,420 full-time employees across 6 regional offices.",
            ],
        ),
        (
            "2. Segment Performance",
            [
                "2. Segment Performance ($ in millions)",
                "",
                "Segment                        FY2024      FY2025     YoY Change",
                "Warehouse Automation            240.0       300.0         +25.0%",
                "Precision Assembly Arms         110.0       125.0         +13.6%",
                "Maintenance & Cloud SaaS         50.0        55.0         +10.0%",
                "Total Revenue                   400.0       480.0         +20.0%",
                "",
                "Note: Warehouse Automation accounted for 62.5% of consolidated FY2025 revenue.",
                "Backlog as of December 31, 2025 stood at $195.0 million, up from $150.0 million.",
            ],
        ),
        (
            "3. Consolidated Income Statement",
            [
                "3. Consolidated Income Statement ($ in millions, except per-share data)",
                "",
                "Line Item                      FY2024      FY2025",
                "Revenue                         400.0       480.0",
                "Cost of Goods Sold (COGS)       248.0       288.0",
                "Gross Profit                    152.0       192.0",
                "Research & Development           52.0        64.0",
                "Selling, General & Admin         48.0        56.0",
                "Operating Income (EBIT)          52.0        72.0",
                "Interest Expense                 (8.0)       (6.0)",
                "Income Tax Expense              (11.0)      (16.5)",
                "Net Income                       33.0        49.5",
                "",
                "Key Metrics Summary: FY2025 Gross Margin = 40.0%; Operating Margin = 15.0%.",
            ],
        ),
        (
            "4. Debt Covenants and Footnotes",
            [
                "4. Debt Covenants and Footnotes",
                "",
                "Note 8 — Credit Facility Covenants:",
                "Under the 2023 Senior Credit Agreement, Acme Robotics must maintain a maximum",
                "Net Debt to EBITDA leverage ratio of 2.50x and a minimum interest coverage ratio",
                "of 4.00x tested quarterly. As of December 31, 2025, the company remained in full",
                "compliance with all financial covenants.",
                "",
                "Note 9 — Liquidity:",
                "Cash and cash equivalents totaled $92.0 million and total debt was $110.0 million,",
                "resulting in Net Debt of $18.0 million as of December 31, 2025.",
            ],
        ),
    ]

    toc = []
    for idx, (section_title, lines) in enumerate(pages_spec, start=1):
        page = doc.new_page(width=595, height=842)
        y = 64
        for line_idx, line in enumerate(lines):
            fontsize = 15 if line_idx == 0 else 11
            page.insert_text((50, y), line, fontsize=fontsize, fontname="helv")
            y += 22 if line_idx == 0 else 18
        toc.append([1, section_title, idx])

    doc.set_toc(toc)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes
