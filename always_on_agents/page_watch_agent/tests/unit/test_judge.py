from unittest.mock import patch

from always_on_agents.page_watch_agent.judge import (
    call_gemini_for_hunk,
    judge_hunks,
    recorded_judgment,
)
from always_on_agents.page_watch_agent.watch import Hunk, diff_paragraphs, run_page_watch


def _hunk(*, page="Acme Cloud Pricing", before="", after="", kind="changed", url="https://example.invalid/p"):
    return Hunk(
        hunk_id="hunk-test",
        kind=kind,
        before=before,
        after=after,
        page_name=page,
        page_url=url,
    )


def test_recorded_fixture_judgments_cover_pricing_and_terms():
    price = recorded_judgment(
        _hunk(before="The Pro plan is $29 per month.", after="The Pro plan is $49 per month.")
    )
    limits = recorded_judgment(
        _hunk(
            before="The Pro plan includes a rate limit of 100 requests per minute.",
            after="The Pro plan includes a rate limit of 60 requests per minute.",
        )
    )
    legal = recorded_judgment(
        _hunk(
            page="Acme Terms of Service",
            kind="added",
            before="",
            after="Disputes are resolved by binding arbitration in Delaware.",
        )
    )

    assert price and price["classification"] == "material" and price["impact"] == "pricing"
    assert limits and limits["impact"] == "limits"
    assert legal and legal["impact"] == "legal"


def test_sample_judge_uses_prefilter_and_recorded_summaries():
    hunks = diff_paragraphs(
        "The Pro plan is $29 per month.\n\nThe Team plan is $99 per month.",
        "The Pro plan is $49 per month.\n\nThe Team plan is $99 per month.",
        page_name="Acme Cloud Pricing",
        page_url="https://example.invalid/pricing",
    )

    with patch("urllib.request.urlopen") as urlopen:
        judged = judge_hunks(
            hunks,
            keywords=("price", "deprecat", "limit"),
            sample=True,
        )

    urlopen.assert_not_called()
    assert len(judged) == 1
    item = judged[0]
    assert item.classification == "material"
    assert item.impact == "pricing"
    assert item.before == "The Pro plan is $29 per month."
    assert item.after == "The Pro plan is $49 per month."
    assert item.prefilter_verdict == "likely_material"
    assert any(reason.startswith("numeric:") for reason in item.prefilter_reasons)
    assert "$29" in item.summary and "$49" in item.summary


def test_cosmetic_hunk_without_keywords_or_numbers_is_prefiltered():
    hunks = [
        _hunk(
            page="Acme API Docs",
            before="Made with care.",
            after="Made with extra care.",
        )
    ]

    judged = judge_hunks(hunks, keywords=("price", "limit"), sample=True)

    assert judged[0].prefilter_verdict == "likely_cosmetic"
    assert judged[0].classification == "cosmetic"


def test_live_model_path_is_not_used_in_sample_mode(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    with patch(
        "always_on_agents.page_watch_agent.judge.call_gemini_for_hunk"
    ) as gemini:
        payload = run_page_watch(live=False)

    gemini.assert_not_called()
    assert payload["judge_mode"] == "sample"


def test_brief_marks_prefilter_fallback_when_gemini_fails():
    from always_on_agents.page_watch_agent.delivery import render_brief

    hunks = diff_paragraphs(
        "The Pro plan is $29 per month.",
        "The Pro plan is $49 per month.",
        page_name="Acme Cloud Pricing",
        page_url="https://example.invalid/pricing",
    )
    with patch(
        "always_on_agents.page_watch_agent.judge.call_gemini_for_hunk",
        side_effect=RuntimeError("Gemini request failed"),
    ):
        judged = judge_hunks(hunks, keywords=("price", "limit"), sample=False)

    assert judged[0].source == "prefilter_fallback"
    brief = render_brief(
        [
            {
                "name": "Acme Cloud Pricing",
                "url": "https://example.invalid/pricing",
                "status": "material",
                "note": "",
                "hunks": [hunk.to_dict() for hunk in hunks],
                "judgments": [item.to_dict() for item in judged],
            }
        ],
        watch_mode="live_fetch",
        watchlist_path="test",
        pages_checked=1,
        judge_mode="gemini",
    )
    assert "Source: prefilter_fallback (Gemini did not judge this hunk)" in brief.text
    assert "source=prefilter_fallback" in brief.text
    assert "prefilter_fallback" in brief.html
    assert "Gemini did not judge this hunk" in brief.html


def test_call_gemini_requires_an_api_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    try:
        call_gemini_for_hunk(
            _hunk(before="a", after="b"),
            keywords=("price",),
            prefilter_verdict="likely_material",
            prefilter_reasons=("numeric:$1->$2",),
        )
    except RuntimeError as exc:
        assert "GOOGLE_API_KEY" in str(exc)
    else:
        raise AssertionError("expected GOOGLE_API_KEY error")
