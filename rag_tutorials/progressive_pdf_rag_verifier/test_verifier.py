"""Self-contained offline unit tests for Progressive PDF RAG & Deterministic Verifier."""

from __future__ import annotations

from types import SimpleNamespace

import pymupdf
import pytest

from agent import ProgressivePDFAgent, dispatch_tool
from claim_verifier import safe_calc, verify_formula, verify_number, verify_quote
from pdf_navigator import PDFDocumentIndex, build_sample_financial_pdf


@pytest.fixture(scope="module")
def sample_index() -> PDFDocumentIndex:
    return PDFDocumentIndex.from_bytes(build_sample_financial_pdf(), name="acme_fy2025.pdf")


def test_outline_and_bm25_navigation(sample_index: PDFDocumentIndex) -> None:
    outline = sample_index.get_outline()
    assert outline["num_pages"] == 4
    assert len(outline["sections"]) == 4
    assert outline["sections"][2]["title"] == "3. Consolidated Income Statement"

    hits = sample_index.search_pages("Net Debt EBITDA covenant", top_k=2)["hits"]
    assert hits
    assert hits[0]["page"] == 4

    read_res = sample_index.read_pages([3, 99], max_chars_per_page=120)
    assert read_res["pages_read"] == [3]
    assert read_res["out_of_range_pages"] == [99]
    assert read_res["content"][0]["truncated"] is True


def test_font_heuristic_outline_for_bookmarkless_pdf() -> None:
    doc = pymupdf.open()
    p1 = doc.new_page()
    p1.insert_text((50, 60), "1. Overview", fontsize=16)
    p1.insert_text((50, 90), "Normal body paragraph explaining architecture details.", fontsize=10)
    p2 = doc.new_page()
    p2.insert_text((50, 60), "2. Financial Results", fontsize=16)
    p2.insert_text((50, 90), "Revenue grew to $120 million in Q4.", fontsize=10)
    raw = doc.tobytes()
    doc.close()

    idx = PDFDocumentIndex.from_bytes(raw, name="no_bookmarks.pdf")
    titles = [s["title"] for s in idx.get_outline()["sections"]]
    assert "1. Overview" in titles
    assert "2. Financial Results" in titles


def test_verify_quote_exact_and_wrong_page(sample_index: PDFDocumentIndex) -> None:
    ok = verify_quote(
        sample_index,
        "All factory deployments met our 99.4% uptime SLA while reducing unit assembly cost by 14.5% year-over-year.",
        page=1,
    )
    assert ok.status == "verified"

    wrong_page = verify_quote(
        sample_index,
        "All factory deployments met our 99.4% uptime SLA",
        page=3,
    )
    assert wrong_page.status == "unverified"
    assert "page(s) [1]" in wrong_page.detail

    fabricated = verify_quote(sample_index, "Acme Robotics acquired Mars Logistics for $9 billion.", page=1)
    assert fabricated.status == "unverified"


def test_verify_number_raw_scaled_and_negative(sample_index: PDFDocumentIndex) -> None:
    assert verify_number(sample_index, 480.0, page=3).status == "verified"
    # Page 3 header declares ($ in millions), so 480,000,000 must also match
    assert verify_number(sample_index, 480_000_000.0, page=3).status == "verified"
    # Parenthesized accounting negative (6.0) -> -6.0
    assert verify_number(sample_index, -6.0, page=3).status == "verified"
    assert verify_number(sample_index, 999.9, page=3).status == "unverified"


def test_safe_calc_and_injection_rejection() -> None:
    assert safe_calc("(480 - 288) / 480 * 100") == pytest.approx(40.0)
    assert safe_calc("(1 + 0.2) ^ 2") == pytest.approx(1.44)
    assert safe_calc("12.5% * 400") == pytest.approx(50.0)
    # Security guards: disallow calls, imports, attributes, huge powers, division by zero
    assert safe_calc("__import__('os').system('echo hi')") is None
    assert safe_calc("9 ** 999") is None
    assert safe_calc("1 / 0") is None


def test_verify_formula_catches_bad_math_and_fabricated_operands(sample_index: PDFDocumentIndex) -> None:
    good = verify_formula(
        sample_index,
        formula="(revenue - cogs) / revenue * 100",
        operands={"revenue": {"value": 480.0, "page": 3}, "cogs": {"value": 288.0, "page": 3}},
        claimed_result=40.0,
    )
    assert good.status == "verified"
    assert good.computed_value == pytest.approx(40.0)

    bad_math = verify_formula(
        sample_index,
        formula="(revenue - cogs) / revenue * 100",
        operands={"revenue": {"value": 480.0, "page": 3}, "cogs": {"value": 288.0, "page": 3}},
        claimed_result=45.0,
    )
    assert bad_math.status == "mismatch"
    assert bad_math.computed_value == pytest.approx(40.0)

    bad_operand = verify_formula(
        sample_index,
        formula="(revenue - cogs) / revenue * 100",
        operands={"revenue": {"value": 550.0, "page": 3}, "cogs": {"value": 288.0, "page": 3}},
        claimed_result=47.64,
    )
    assert bad_operand.status == "unverified_operand"
    assert "revenue" in bad_operand.detail


def test_agent_loop_handles_tool_calls_malformed_json_and_empty_choices(sample_index: PDFDocumentIndex) -> None:
    class _FakeCompletions:
        def __init__(self, responses):
            self._responses = list(responses)

        def create(self, **kwargs):
            return self._responses.pop(0)

    class _FakeClient:
        def __init__(self, responses):
            self.chat = SimpleNamespace(completions=_FakeCompletions(responses))

    # Step 1: malformed JSON args + valid verify_claim; Step 2: final answer
    tc_bad = SimpleNamespace(
        id="call_1",
        function=SimpleNamespace(name="read_pages", arguments="{not valid json"),
    )
    tc_ok = SimpleNamespace(
        id="call_2",
        function=SimpleNamespace(
            name="verify_claim",
            arguments='{"kind":"number","value":480.0,"page":3}',
        ),
    )
    r1 = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="", tool_calls=[tc_bad, tc_ok]))])
    r2 = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Revenue is $480.0M (p.3).", tool_calls=[]))])

    agent = ProgressivePDFAgent(index=sample_index, client=_FakeClient([r1, r2]), max_steps=4)
    res = agent.ask("What was FY2025 revenue?")
    assert res.stopped_reason == "completed"
    assert "480.0M" in res.answer
    assert len(res.verifications) == 1 and res.verifications[0]["status"] == "verified"
    assert "error" in res.trace[0].result

    # Empty choices guard
    empty_agent = ProgressivePDFAgent(
        index=sample_index,
        client=_FakeClient([SimpleNamespace(choices=[])]),
        max_steps=2,
    )
    empty_res = empty_agent.ask("Test empty reply")
    assert empty_res.stopped_reason == "empty_model_response"

    # Unknown tool guard
    assert "error" in dispatch_tool(sample_index, "nonexistent_tool", {})
