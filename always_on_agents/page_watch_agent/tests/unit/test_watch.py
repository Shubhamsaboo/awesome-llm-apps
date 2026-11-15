import json
from unittest.mock import patch

from always_on_agents.page_watch_agent.watch import (
    detect_numeric_changes,
    diff_paragraphs,
    fetch_url,
    hunk_id_for,
    load_snapshot,
    load_watchlist,
    normalize_page,
    run_page_watch,
    save_snapshot,
    split_paragraphs,
    strip_volatile_tokens,
    url_key,
)


PRICING_HTML = """
<html><body>
<nav>Home | Pricing</nav>
<div class="promo-banner">50% off today</div>
<main id="plans">
  <h1>Plans</h1>
  <p>The Pro plan is $29 per month.</p>
  <p>Rate limit 100 requests per minute.</p>
</main>
</body></html>
"""


def test_normalization_strips_scripts_styles_nav_and_promo():
    markup = """
    <html><head><style>.hero { color: red; }</style>
    <script>alert("x")</script></head>
    <body>
      <nav>Home Pricing Docs</nav>
      <div class="promo-banner">Flash sale 40% off today only</div>
      <p>Authenticate with an API key.</p>
    </body></html>
    """

    text = normalize_page(markup)

    assert "color: red" not in text
    assert "alert" not in text
    assert "Home Pricing Docs" not in text
    assert "Flash sale" not in text
    assert "Authenticate with an API key." in text


def test_volatile_token_suppression_drops_timestamps_cache_busters_and_csrf():
    first = (
        "Last updated: 2026-01-15T09:00:00Z · cache=a1b2c3 "
        "csrf_token=aa11bb22cc33dd44 app.js?v=abc123"
    )
    second = (
        "Last updated: 2026-11-15T16:41:22Z · cache=9f8e7d "
        "csrf_token=zz99yy88xx77ww66 app.js?v=zzz999"
    )

    assert strip_volatile_tokens(first) == strip_volatile_tokens(second)

    docs_v1 = """
    <html><body>
      <p>Authenticate with an API key in the Authorization header.</p>
      <footer>Last updated: 2026-01-15T09:00:00Z · cache=a1b2c3</footer>
    </body></html>
    """
    docs_v2 = """
    <html><body>
      <p>Authenticate with an API key in the Authorization header.</p>
      <footer>Last updated: 2026-11-15T16:41:22Z · cache=9f8e7d</footer>
    </body></html>
    """
    assert normalize_page(docs_v1) == normalize_page(docs_v2)
    assert diff_paragraphs(
        normalize_page(docs_v1),
        normalize_page(docs_v2),
        page_name="docs",
        page_url="https://example.invalid/docs",
    ) == []


def test_css_selector_and_text_anchors_scope_the_region():
    markup = """
    <html><body>
      <p>Ignore the marketing blurb.</p>
      <section id="plans">
        <p>BEGIN_PLANS The Pro plan is $29 per month. END_PLANS</p>
      </section>
      <p>Ignore the footer CTA.</p>
    </body></html>
    """

    selected = normalize_page(markup, selector="#plans")
    anchored = normalize_page(
        markup,
        start_anchor="BEGIN_PLANS",
        end_anchor="END_PLANS",
    )

    assert "marketing blurb" not in selected
    assert "footer CTA" not in selected
    assert "The Pro plan is $29 per month." in selected
    assert "BEGIN_PLANS" in anchored
    assert "footer CTA" not in anchored
    assert "marketing blurb" not in anchored


def test_diff_hunk_ids_are_stable_across_reorder():
    original = (
        "The Pro plan is $29 per month.\n\n"
        "Unrelated terms apply.\n\n"
        "Rate limit 100 requests per minute."
    )
    changed_same_order = (
        "The Pro plan is $49 per month.\n\n"
        "Unrelated terms apply.\n\n"
        "Rate limit 100 requests per minute."
    )
    changed_reordered = (
        "Rate limit 100 requests per minute.\n\n"
        "The Pro plan is $49 per month.\n\n"
        "Unrelated terms apply."
    )

    same_order = diff_paragraphs(
        original, changed_same_order, page_name="pricing", page_url="https://example.invalid/p"
    )
    reordered = diff_paragraphs(
        original, changed_reordered, page_name="pricing", page_url="https://example.invalid/p"
    )
    untouched_reorder = diff_paragraphs(
        original,
        "Rate limit 100 requests per minute.\n\nUnrelated terms apply.\n\nThe Pro plan is $29 per month.",
        page_name="pricing",
        page_url="https://example.invalid/p",
    )

    assert untouched_reorder == []
    assert [hunk.hunk_id for hunk in same_order] == [hunk.hunk_id for hunk in reordered]
    assert same_order[0].hunk_id == hunk_id_for(
        "changed",
        "The Pro plan is $29 per month.",
        "The Pro plan is $49 per month.",
    )


def test_numeric_change_detection_finds_prices_and_quotas():
    changes = detect_numeric_changes(
        "The Pro plan is $29 per month with 100 requests.",
        "The Pro plan is $49 per month with 60 requests.",
    )

    assert ("$29", "$49") in changes
    assert ("100", "60") in changes


def test_snapshot_store_is_keyed_by_url_hash(tmp_path):
    first = save_snapshot(
        tmp_path,
        url="https://example.invalid/pricing",
        name="pricing",
        normalized_text="The Pro plan is $29 per month.",
    )
    second = save_snapshot(
        tmp_path,
        url="https://example.invalid/terms",
        name="terms",
        normalized_text="You may use the service subject to these terms.",
    )

    loaded = load_snapshot(tmp_path, "https://example.invalid/pricing")

    assert first != second
    assert first.parent.name == url_key("https://example.invalid/pricing")
    assert loaded is not None
    assert loaded["normalized_text"] == "The Pro plan is $29 per month."
    assert loaded["content_sha256"]
    assert load_snapshot(tmp_path, "https://example.invalid/missing") is None


def test_watchlist_yaml_and_json_round_trip(tmp_path):
    yaml_path = tmp_path / "watch.yaml"
    json_path = tmp_path / "watch.json"
    yaml_path.write_text(
        "pages:\n"
        "  - url: https://example.invalid/pricing\n"
        "    name: Vendor pricing\n"
        "    selector: \"#plans\"\n"
        "    keywords:\n"
        "      - price\n"
        "      - limit\n",
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(
            {
                "pages": [
                    {
                        "url": "https://example.invalid/pricing",
                        "name": "Vendor pricing",
                        "selector": "#plans",
                        "keywords": ["price", "limit"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    yaml_targets = load_watchlist(yaml_path)
    json_targets = load_watchlist(json_path)

    assert yaml_targets[0].name == json_targets[0].name == "Vendor pricing"
    assert yaml_targets[0].selector == json_targets[0].selector == "#plans"
    assert yaml_targets[0].keywords == json_targets[0].keywords == ("price", "limit")


def test_sample_run_makes_no_network_calls_and_flags_material_pages():
    with patch("urllib.request.urlopen") as urlopen:
        payload = run_page_watch(live=False, live_model=False)

    urlopen.assert_not_called()
    assert payload["watch_mode"] == "sample"
    assert payload["judge_mode"] == "sample"
    pages = {page["name"]: page for page in payload["pages"]}
    assert pages["Acme Cloud Pricing"]["status"] == "material"
    assert pages["Acme API Docs"]["status"] == "no_material_change"
    assert pages["Acme Terms of Service"]["status"] == "material"
    assert "$29" in payload["text"]
    assert "$49" in payload["text"]
    assert "No material change." in payload["text"]
    assert "arbitration" in payload["text"].lower()
    assert "Page Watch Brief" in payload["text"]
    assert "<h2>Page Watch Brief</h2>" in payload["html"]


def test_fetch_url_enforces_size_cap_and_user_agent():
    class FakeResponse:
        def __init__(self, payload: bytes) -> None:
            self._payload = payload

        def read(self, size: int = -1) -> bytes:
            return self._payload[:size]

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    captured = {}

    def fake_urlopen(request, timeout=15):
        captured["headers"] = dict(request.headers.items())
        captured["timeout"] = timeout
        return FakeResponse(b"hello world")

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        body = fetch_url("https://example.invalid/pricing", timeout_seconds=9, max_bytes=100)

    assert body == "hello world"
    assert captured["timeout"] == 9
    user_agent = captured["headers"].get("User-agent") or captured["headers"].get("User-Agent")
    assert user_agent and user_agent.startswith("page-watch-agent/1.0")


def test_split_paragraphs_drops_blank_chunks():
    assert split_paragraphs("Alpha.\n\n\n  Beta.  \n\n") == ["Alpha.", "Beta."]


def test_live_fetch_captures_baseline_then_briefs_material_changes(tmp_path):
    from always_on_agents.page_watch_agent.watch import SAMPLE_PAGES

    watchlist = tmp_path / "watch.json"
    snapshots = tmp_path / "snapshots"
    pages = []
    html_by_url = {}
    for sample in SAMPLE_PAGES:
        url = f"http://127.0.0.1:8765/{sample.target.filename}"
        pages.append(
            {
                "url": url,
                "name": sample.target.name,
                "selector": sample.target.selector,
                "start_anchor": sample.target.start_anchor,
                "end_anchor": sample.target.end_anchor,
                "keywords": list(sample.target.keywords),
            }
        )
        html_by_url[url] = {"before": sample.before_html, "after": sample.after_html}
    watchlist.write_text(json.dumps({"pages": pages}), encoding="utf-8")

    class FakeResponse:
        def __init__(self, payload: bytes) -> None:
            self._payload = payload

        def read(self, size: int = -1) -> bytes:
            return self._payload[:size]

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    phase = {"name": "before"}

    def fake_urlopen(request, timeout=15):
        url = request.full_url
        markup = html_by_url[url][phase["name"]]
        return FakeResponse(markup.encode("utf-8"))

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        first = run_page_watch(
            watchlist_path=watchlist,
            snapshot_dir=snapshots,
            live=True,
            live_model=False,
        )
        phase["name"] = "after"
        second = run_page_watch(
            watchlist_path=watchlist,
            snapshot_dir=snapshots,
            live=True,
            live_model=False,
        )

    assert first["watch_mode"] == "live_fetch"
    assert {page["status"] for page in first["pages"]} == {"baseline"}
    pages_by_name = {page["name"]: page for page in second["pages"]}
    assert pages_by_name["Acme Cloud Pricing"]["status"] == "material"
    assert pages_by_name["Acme API Docs"]["status"] == "no_material_change"
    assert pages_by_name["Acme Terms of Service"]["status"] == "material"
    assert "$29" in second["text"] and "$49" in second["text"]
    assert "No material change." in second["text"]
    assert "arbitration" in second["text"].lower()


def _live_fetch_harness(tmp_path):
    from always_on_agents.page_watch_agent.watch import SAMPLE_PAGES

    watchlist = tmp_path / "watch.json"
    snapshots = tmp_path / "snapshots"
    pages = []
    html_by_url = {}
    for sample in SAMPLE_PAGES:
        url = f"http://127.0.0.1:8765/{sample.target.filename}"
        pages.append(
            {
                "url": url,
                "name": sample.target.name,
                "selector": sample.target.selector,
                "start_anchor": sample.target.start_anchor,
                "end_anchor": sample.target.end_anchor,
                "keywords": list(sample.target.keywords),
            }
        )
        html_by_url[url] = {"before": sample.before_html, "after": sample.after_html}
    watchlist.write_text(json.dumps({"pages": pages}), encoding="utf-8")

    class FakeResponse:
        def __init__(self, payload: bytes) -> None:
            self._payload = payload

        def read(self, size: int = -1) -> bytes:
            return self._payload[:size]

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    phase = {"name": "before"}

    def fake_urlopen(request, timeout=15):
        url = request.full_url
        markup = html_by_url[url][phase["name"]]
        return FakeResponse(markup.encode("utf-8"))

    return watchlist, snapshots, phase, fake_urlopen


def test_fetch_without_api_key_keeps_sample_judgments(tmp_path, monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("PAGE_WATCH_LIVE_MODEL", raising=False)
    watchlist, snapshots, phase, fake_urlopen = _live_fetch_harness(tmp_path)

    with patch("urllib.request.urlopen", side_effect=fake_urlopen), patch(
        "always_on_agents.page_watch_agent.judge.call_gemini_for_hunk"
    ) as gemini:
        run_page_watch(watchlist_path=watchlist, snapshot_dir=snapshots, live=True)
        phase["name"] = "after"
        second = run_page_watch(watchlist_path=watchlist, snapshot_dir=snapshots, live=True)

    gemini.assert_not_called()
    assert second["judge_mode"] == "sample"
    assert "Source: gemini" not in second["text"]


def test_fetch_defaults_to_gemini_when_api_key_is_set(tmp_path, monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.delenv("PAGE_WATCH_LIVE_MODEL", raising=False)
    watchlist, snapshots, phase, fake_urlopen = _live_fetch_harness(tmp_path)

    def fake_gemini(hunk, **_kwargs):
        return {
            "classification": "material",
            "summary": f"Gemini summary: {hunk.after or hunk.before}",
            "impact": "other",
        }

    with patch("urllib.request.urlopen", side_effect=fake_urlopen), patch(
        "always_on_agents.page_watch_agent.judge.call_gemini_for_hunk",
        side_effect=fake_gemini,
    ) as gemini:
        run_page_watch(watchlist_path=watchlist, snapshot_dir=snapshots, live=True)
        phase["name"] = "after"
        second = run_page_watch(watchlist_path=watchlist, snapshot_dir=snapshots, live=True)

    assert gemini.called
    assert second["judge_mode"] == "gemini"
    sources = {
        item["source"]
        for page in second["pages"]
        for item in page["judgments"]
    }
    assert "gemini" in sources
    assert "Source: gemini" in second["text"]
    assert "<strong>Source:</strong> gemini" in second["html"]
