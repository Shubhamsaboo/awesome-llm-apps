"""Fetch, normalize, snapshot, and diff watched pages for Page Watch.

Source modules use the Python standard library. Sample mode loads recorded
page pairs and never opens a network connection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


USER_AGENT = (
    "page-watch-agent/1.0 "
    "(+https://github.com/Shubhamsaboo/awesome-llm-apps; polite page snapshotter)"
)
DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_MAX_BYTES = 1_500_000
DEFAULT_KEYWORDS = (
    "price",
    "pricing",
    "deprecat",
    "limit",
    "quota",
    "arbitration",
    "liability",
    "unavailable",
    "sunset",
    "breaking",
)

SKIP_TAGS = {"script", "style", "noscript", "svg", "template", "iframe"}
CHROME_TAGS = {"nav"}
VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}
BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "div",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "li",
    "main",
    "p",
    "pre",
    "section",
    "table",
    "tr",
    "ul",
    "ol",
}
PROMO_RE = re.compile(
    r"(promo|rotating-banner|marketing-banner|cookie-banner|flash-sale)",
    re.IGNORECASE,
)
ISO_TIMESTAMP_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\b"
)
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
CLOCK_RE = re.compile(r"\b\d{1,2}:\d{2}:\d{2}(?:\s*(?:AM|PM))?\b", re.IGNORECASE)
CACHEBUST_QUERY_RE = re.compile(
    r"[?&](?:v|ver|version|cachebust|cb|t|_)=[A-Za-z0-9._-]+"
)
CACHE_ASSIGN_RE = re.compile(
    r"\b(?:cache(?:bust)?|cb|etag)\s*[:=]\s*[A-Za-z0-9._-]+\b",
    re.IGNORECASE,
)
CSRF_RE = re.compile(
    r"(?i)(?:csrf(?:_token|token)?|authenticity_token)[\"'\s:=]+[A-Za-z0-9+/=_-]{8,}"
)
NUMBER_RE = re.compile(r"(?:\$|€|£)\s*\d{1,3}(?:,\d{3})*(?:\.\d+)?|\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b")
SIGNATURE_NUMBER_RE = re.compile(
    r"(?:\$|€|£)\s*\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d{1,3}(?:,\d{3})*(?:\.\d+)?"
)


@dataclass(frozen=True)
class WatchTarget:
    url: str
    name: str
    selector: str | None = None
    start_anchor: str | None = None
    end_anchor: str | None = None
    keywords: tuple[str, ...] = ()
    filename: str = ""

    def merged_keywords(self) -> tuple[str, ...]:
        combined = list(DEFAULT_KEYWORDS)
        for keyword in self.keywords:
            if keyword and keyword.lower() not in {item.lower() for item in combined}:
                combined.append(keyword)
        return tuple(combined)


@dataclass(frozen=True)
class SamplePage:
    target: WatchTarget
    before_html: str
    after_html: str


@dataclass(frozen=True)
class Hunk:
    hunk_id: str
    kind: str
    before: str
    after: str
    page_name: str
    page_url: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class _HTMLTextExtractor(HTMLParser):
    """Pull readable text, skipping scripts, styles, nav, and promo chrome."""

    def __init__(
        self,
        *,
        selector_tag: str | None = None,
        selector_id: str | None = None,
        selector_class: str | None = None,
        use_selector: bool = False,
    ) -> None:
        super().__init__(convert_charrefs=True)
        self.selector_tag = selector_tag
        self.selector_id = selector_id
        self.selector_class = selector_class
        self.use_selector = use_selector
        self.skip_depth = 0
        self.capture_depth = 0
        self.matched = not use_selector
        self.chunks: list[str] = []

    def _classes(self, attrs: dict[str, str]) -> list[str]:
        return [token for token in attrs.get("class", "").split() if token]

    def _is_promo(self, attrs: dict[str, str]) -> bool:
        blob = " ".join([attrs.get("id", ""), attrs.get("class", ""), attrs.get("role", "")])
        return bool(PROMO_RE.search(blob))

    def _selector_match(self, tag: str, attrs: dict[str, str]) -> bool:
        if self.selector_tag and tag != self.selector_tag:
            return False
        if self.selector_id and attrs.get("id") != self.selector_id:
            return False
        if self.selector_class and self.selector_class not in self._classes(attrs):
            return False
        return True

    def _collecting(self) -> bool:
        if self.skip_depth:
            return False
        if self.use_selector:
            return self.capture_depth > 0
        return True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_d = {key: (value or "") for key, value in attrs}
        void = tag in VOID_TAGS
        if self.skip_depth:
            if not void:
                self.skip_depth += 1
            return
        if tag in SKIP_TAGS or tag in CHROME_TAGS or self._is_promo(attrs_d):
            if not void:
                self.skip_depth = 1
            return
        if self.use_selector and self.capture_depth == 0 and self._selector_match(tag, attrs_d):
            self.matched = True
            if not void:
                self.capture_depth = 1
            return
        if self.use_selector and self.capture_depth:
            if not void:
                self.capture_depth += 1
        if tag == "br" and self._collecting():
            self.chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self.skip_depth:
            if tag in SKIP_TAGS or tag in CHROME_TAGS or tag not in VOID_TAGS:
                self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.use_selector and self.capture_depth:
            self.capture_depth -= 1
        if tag in BLOCK_TAGS and self._collecting():
            self.chunks.append("\n\n")
        elif tag in BLOCK_TAGS and not self.use_selector:
            self.chunks.append("\n\n")

    def handle_data(self, data: str) -> None:
        if self._collecting() and data:
            self.chunks.append(data)

    def text(self) -> str:
        return "".join(self.chunks)


def parse_selector(selector: str | None) -> tuple[str | None, str | None, str | None]:
    """Parse a tiny CSS subset: tag, #id, .class, tag#id, tag.class."""

    if not selector:
        return None, None, None
    value = selector.strip()
    tag: str | None = None
    ident: str | None = None
    class_name: str | None = None
    if value.startswith("#"):
        ident = value[1:]
    elif value.startswith("."):
        class_name = value[1:]
    elif "#" in value:
        tag, ident = value.split("#", 1)
    elif "." in value:
        tag, class_name = value.split(".", 1)
    else:
        tag = value
    return (tag.lower() if tag else None), ident or None, class_name or None


def html_to_text(markup: str, *, selector: str | None = None) -> tuple[str, bool]:
    """Convert HTML to readable text. Returns (text, selector_matched)."""

    tag, ident, class_name = parse_selector(selector)
    parser = _HTMLTextExtractor(
        selector_tag=tag,
        selector_id=ident,
        selector_class=class_name,
        use_selector=bool(selector),
    )
    parser.feed(markup)
    parser.close()
    if selector and not parser.matched:
        fallback = _HTMLTextExtractor()
        fallback.feed(markup)
        fallback.close()
        return fallback.text(), False
    return parser.text(), True if not selector else parser.matched


def apply_text_anchors(text: str, start_anchor: str | None, end_anchor: str | None) -> str:
    """Keep the region between optional start and end anchors."""

    scoped = text
    if start_anchor:
        index = scoped.find(start_anchor)
        if index >= 0:
            scoped = scoped[index:]
    if end_anchor:
        index = scoped.find(end_anchor)
        if index >= 0:
            scoped = scoped[:index]
    return scoped


def strip_volatile_tokens(text: str) -> str:
    """Replace timestamps, cache-busters, and CSRF tokens with stable placeholders."""

    cleaned = CSRF_RE.sub("<CSRF>", text)
    cleaned = CACHEBUST_QUERY_RE.sub("<CACHE>", cleaned)
    cleaned = CACHE_ASSIGN_RE.sub("<CACHE>", cleaned)
    cleaned = ISO_TIMESTAMP_RE.sub("<TIMESTAMP>", cleaned)
    cleaned = CLOCK_RE.sub("<TIMESTAMP>", cleaned)
    cleaned = DATE_RE.sub("<TIMESTAMP>", cleaned)
    return cleaned


def collapse_whitespace(text: str) -> str:
    """Collapse internal whitespace while keeping paragraph breaks."""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t\f\v]+", " ", normalized)
    normalized = re.sub(r" *\n *", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def normalize_page(
    markup: str,
    *,
    selector: str | None = None,
    start_anchor: str | None = None,
    end_anchor: str | None = None,
) -> str:
    """Turn a page into stable, comparable text."""

    extracted, _matched = html_to_text(markup, selector=selector)
    scoped = apply_text_anchors(extracted, start_anchor, end_anchor)
    return collapse_whitespace(strip_volatile_tokens(scoped))


def split_paragraphs(text: str) -> list[str]:
    """Split normalized text into paragraph units."""

    paragraphs = []
    for chunk in re.split(r"\n\s*\n", text):
        collapsed = re.sub(r"\s+", " ", chunk).strip()
        if collapsed:
            paragraphs.append(collapsed)
    return paragraphs


def paragraph_signature(text: str) -> str:
    """Stable signature that ignores numeric tokens so price/limit edits still match."""

    return SIGNATURE_NUMBER_RE.sub("#", text).strip()


def hunk_id_for(kind: str, before: str, after: str) -> str:
    payload = f"{kind}\n{before}\n{after}".encode("utf-8")
    return "hunk-" + hashlib.sha256(payload).hexdigest()[:12]


def detect_numeric_changes(before: str, after: str) -> list[tuple[str, str]]:
    """Return paired numeric tokens that changed between two strings."""

    old_numbers = NUMBER_RE.findall(before or "")
    new_numbers = NUMBER_RE.findall(after or "")
    changes: list[tuple[str, str]] = []
    if len(old_numbers) == len(new_numbers):
        for old, new in zip(old_numbers, new_numbers):
            if old.replace(" ", "") != new.replace(" ", ""):
                changes.append((old, new))
        return changes
    old_set = [item.replace(" ", "") for item in old_numbers]
    new_set = [item.replace(" ", "") for item in new_numbers]
    if old_set != new_set:
        longest = max(len(old_numbers), len(new_numbers))
        for index in range(longest):
            old = old_numbers[index] if index < len(old_numbers) else ""
            new = new_numbers[index] if index < len(new_numbers) else ""
            if old.replace(" ", "") != new.replace(" ", ""):
                changes.append((old, new))
    return changes


def prefilter_hunk(hunk: Hunk, keywords: tuple[str, ...]) -> tuple[str, tuple[str, ...]]:
    """Deterministic first-pass verdict shown next to the model judgment."""

    blob = f"{hunk.before}\n{hunk.after}".lower()
    reasons: list[str] = []
    hits = [keyword for keyword in keywords if keyword.lower() in blob]
    if hits:
        reasons.append("keyword:" + ",".join(hits))
    numeric = detect_numeric_changes(hunk.before, hunk.after)
    if numeric:
        rendered = ",".join(f"{old}->{new}" if old and new else (new or old) for old, new in numeric)
        reasons.append("numeric:" + rendered)
    return ("likely_material" if reasons else "likely_cosmetic"), tuple(reasons)


def diff_paragraphs(
    old_text: str,
    new_text: str,
    *,
    page_name: str,
    page_url: str,
) -> list[Hunk]:
    """Paragraph-level diff whose hunk ids stay stable across reordering."""

    old_paragraphs = split_paragraphs(old_text)
    new_paragraphs = split_paragraphs(new_text)
    common = Counter(old_paragraphs) & Counter(new_paragraphs)
    old_remain = list((Counter(old_paragraphs) - common).elements())
    new_remain = list((Counter(new_paragraphs) - common).elements())

    used_new: set[int] = set()
    hunks: list[Hunk] = []
    for old in old_remain:
        match_index = None
        old_signature = paragraph_signature(old)
        for index, new in enumerate(new_remain):
            if index in used_new:
                continue
            if paragraph_signature(new) == old_signature:
                match_index = index
                break
        if match_index is None:
            hunks.append(
                Hunk(
                    hunk_id=hunk_id_for("removed", old, ""),
                    kind="removed",
                    before=old,
                    after="",
                    page_name=page_name,
                    page_url=page_url,
                )
            )
            continue
        used_new.add(match_index)
        new = new_remain[match_index]
        if new == old:
            continue
        hunks.append(
            Hunk(
                hunk_id=hunk_id_for("changed", old, new),
                kind="changed",
                before=old,
                after=new,
                page_name=page_name,
                page_url=page_url,
            )
        )
    for index, new in enumerate(new_remain):
        if index in used_new:
            continue
        hunks.append(
            Hunk(
                hunk_id=hunk_id_for("added", "", new),
                kind="added",
                before="",
                after=new,
                page_name=page_name,
                page_url=page_url,
            )
        )
    return hunks


def url_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def snapshot_path(snapshot_dir: Path, url: str) -> Path:
    return Path(snapshot_dir) / url_key(url) / "snapshot.json"


def load_snapshot(snapshot_dir: Path, url: str) -> dict[str, Any] | None:
    path = snapshot_path(snapshot_dir, url)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def save_snapshot(
    snapshot_dir: Path,
    *,
    url: str,
    name: str,
    normalized_text: str,
) -> Path:
    path = snapshot_path(snapshot_dir, url)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "url": url,
        "name": name,
        "normalized_text": normalized_text,
        "content_sha256": hashlib.sha256(normalized_text.encode("utf-8")).hexdigest(),
        "paragraphs": split_paragraphs(normalized_text),
    }
    tmp_path = path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)
    return path


def _yaml_scalar(value: str) -> str:
    stripped = value.strip()
    if stripped in {"", "null", "~"}:
        return ""
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {"'", '"'}:
        return stripped[1:-1]
    return stripped


def _parse_inline_list(value: str) -> list[str]:
    inner = value.strip()[1:-1].strip()
    if not inner:
        return []
    return [_yaml_scalar(part) for part in inner.split(",") if _yaml_scalar(part)]


def parse_watchlist_yaml(text: str) -> dict[str, Any]:
    """Parse the small watch-list YAML subset used by this app."""

    pages: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_keywords = False
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if line.rstrip(":") == "pages" and line.endswith(":"):
            current = None
            in_keywords = False
            continue
        if line.startswith("- ") and indent <= 2:
            current = {}
            pages.append(current)
            in_keywords = False
            rest = line[2:].strip()
            if rest and ":" in rest:
                key, value = rest.split(":", 1)
                key = key.strip()
                value = value.strip()
                if key == "keywords":
                    current["keywords"] = _parse_inline_list(value) if value.startswith("[") else []
                    in_keywords = not value.startswith("[")
                else:
                    current[key] = _yaml_scalar(value)
            continue
        if current is None:
            continue
        if in_keywords and line.startswith("- "):
            current.setdefault("keywords", []).append(_yaml_scalar(line[2:]))
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key == "keywords":
            in_keywords = True
            current["keywords"] = _parse_inline_list(value) if value.startswith("[") else []
            if value.startswith("["):
                in_keywords = False
        else:
            in_keywords = False
            current[key] = _yaml_scalar(value)
    return {"pages": pages}


def _target_from_mapping(raw: dict[str, Any]) -> WatchTarget:
    keywords_raw = raw.get("keywords") or []
    if isinstance(keywords_raw, str):
        keywords = tuple(part.strip() for part in keywords_raw.split(",") if part.strip())
    else:
        keywords = tuple(str(part) for part in keywords_raw if str(part).strip())
    selector = str(raw.get("selector") or "") or None
    start_anchor = str(raw.get("start_anchor") or "") or None
    end_anchor = str(raw.get("end_anchor") or "") or None
    url = str(raw.get("url") or "").strip()
    name = str(raw.get("name") or url or "Untitled page").strip()
    if not url:
        raise ValueError("Each watch-list entry needs a url.")
    return WatchTarget(
        url=url,
        name=name,
        selector=selector,
        start_anchor=start_anchor,
        end_anchor=end_anchor,
        keywords=keywords,
        filename=str(raw.get("filename") or ""),
    )


def load_watchlist(path: str | Path) -> list[WatchTarget]:
    """Load a YAML or JSON watch list of pages."""

    watchlist_path = Path(path).expanduser()
    if not watchlist_path.is_file():
        raise FileNotFoundError(f"Watch list not found: {watchlist_path}")
    raw_text = watchlist_path.read_text(encoding="utf-8")
    stripped = raw_text.lstrip()
    if watchlist_path.suffix.lower() == ".json" or stripped.startswith("{") or stripped.startswith("["):
        document: Any = json.loads(raw_text)
    else:
        document = parse_watchlist_yaml(raw_text)
    if isinstance(document, list):
        pages = document
    elif isinstance(document, dict):
        pages = document.get("pages") or document.get("watch") or []
    else:
        raise ValueError(f"Could not parse watch list: {watchlist_path}")
    return [_target_from_mapping(item) for item in pages if isinstance(item, dict)]


def fetch_url(
    url: str,
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> str:
    """Fetch a page with a timeout, size cap, and polite User-Agent."""

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            payload = response.read(max_bytes + 1)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Could not fetch {url}: {exc}") from exc
    if len(payload) > max_bytes:
        raise RuntimeError(f"Response for {url} exceeded the {max_bytes} byte cap.")
    return payload.decode("utf-8", errors="replace")


SAMPLE_PAGES = [
    SamplePage(
        target=WatchTarget(
            url="https://example.invalid/pricing",
            name="Acme Cloud Pricing",
            selector="#plans",
            keywords=("price", "deprecat", "limit"),
            filename="pricing.html",
        ),
        before_html="""<!DOCTYPE html>
<html lang="en">
<head>
  <title>Acme Cloud Pricing</title>
  <style>.hero { color: red; }</style>
  <script>window.csrf = "aa11bb22cc33dd44ee55ff6677889900";</script>
</head>
<body>
  <nav>Home | Pricing | Docs | Terms</nav>
  <div class="promo-banner">Flash sale 40% off today only</div>
  <main id="plans">
    <h1>Acme Cloud Pricing</h1>
    <p>The Pro plan is $29 per month.</p>
    <p>The Pro plan includes a rate limit of 100 requests per minute.</p>
    <p>The Team plan is $99 per month.</p>
  </main>
  <footer>Last updated: 2026-01-15T09:00:00Z</footer>
</body>
</html>
""",
        after_html="""<!DOCTYPE html>
<html lang="en">
<head>
  <title>Acme Cloud Pricing</title>
  <style>.hero { color: blue; }</style>
  <script>window.csrf = "99aa88bb77cc66dd55ee44ff33221100";</script>
</head>
<body>
  <nav>Home | Pricing | Docs | Terms | Blog</nav>
  <div class="promo-banner">Flash sale 15% off this weekend</div>
  <main id="plans">
    <h1>Acme Cloud Pricing</h1>
    <p>The Pro plan is $49 per month.</p>
    <p>The Pro plan includes a rate limit of 60 requests per minute.</p>
    <p>The Team plan is $99 per month.</p>
  </main>
  <footer>Last updated: 2026-11-15T16:41:22Z</footer>
</body>
</html>
""",
    ),
    SamplePage(
        target=WatchTarget(
            url="https://example.invalid/docs",
            name="Acme API Docs",
            keywords=("deprecat", "limit"),
            filename="docs.html",
        ),
        before_html="""<!DOCTYPE html>
<html lang="en">
<head>
  <title>Acme API Docs</title>
  <script src="/assets/app.js?v=abc123"></script>
</head>
<body>
  <nav>Docs home</nav>
  <div class="cookie-banner">We use cookies. csrf_token=zzxxyy1122334455</div>
  <main>
    <h1>Acme API Docs</h1>
    <p>Authenticate with an API key in the Authorization header.</p>
    <p>List projects with GET /v1/projects.</p>
  </main>
  <footer>Last updated: 2026-01-15T09:00:00Z · cache=a1b2c3</footer>
</body>
</html>
""",
        after_html="""<!DOCTYPE html>
<html lang="en">
<head>
  <title>Acme API Docs</title>
  <script src="/assets/app.js?v=zzz999"></script>
</head>
<body>
  <nav>Docs home | Changelog</nav>
  <div class="cookie-banner">We use cookies. csrf_token=mmnnoo9988776655</div>
  <main>
    <h1>Acme API Docs</h1>
    <p>Authenticate with an API key in the Authorization header.</p>
    <p>List projects with GET /v1/projects.</p>
  </main>
  <footer>Last updated: 2026-11-15T16:41:22Z · cache=9f8e7d</footer>
</body>
</html>
""",
    ),
    SamplePage(
        target=WatchTarget(
            url="https://example.invalid/terms",
            name="Acme Terms of Service",
            selector="#terms",
            keywords=("arbitration", "liability", "terms"),
            filename="terms.html",
        ),
        before_html="""<!DOCTYPE html>
<html lang="en">
<head><title>Acme Terms of Service</title></head>
<body>
  <nav>Legal</nav>
  <main id="terms">
    <h1>Acme Terms of Service</h1>
    <p>You may use the service subject to these terms.</p>
    <p>We may update these terms with notice by email.</p>
  </main>
</body>
</html>
""",
        after_html="""<!DOCTYPE html>
<html lang="en">
<head><title>Acme Terms of Service</title></head>
<body>
  <nav>Legal | Privacy</nav>
  <main id="terms">
    <h1>Acme Terms of Service</h1>
    <p>You may use the service subject to these terms.</p>
    <p>Disputes are resolved by binding arbitration in Delaware. Class actions are waived.</p>
    <p>We may update these terms with notice by email.</p>
  </main>
</body>
</html>
""",
    ),
]


def sample_targets() -> list[WatchTarget]:
    return [page.target for page in SAMPLE_PAGES]


def _live_fetch_enabled(live: bool | None) -> bool:
    if live is not None:
        return live
    return os.environ.get("PAGE_WATCH_LIVE", "").lower() in {"1", "true", "yes"}


def has_gemini_key() -> bool:
    """True when GOOGLE_API_KEY or GEMINI_API_KEY is set."""

    return bool(os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"))


def _live_model_enabled(live_model: bool | None) -> bool:
    """Gemini is the default judge whenever an API key is set.

    Sample/offline mode passes live_model=False. An explicit True forces a
    model call; an explicit False keeps recorded judgments. PAGE_WATCH_LIVE_MODEL
    can override the key-based default.
    """

    if live_model is True:
        return True
    if live_model is False:
        return False
    flagged = os.environ.get("PAGE_WATCH_LIVE_MODEL", "").lower()
    if flagged in {"0", "false", "no"}:
        return False
    if flagged in {"1", "true", "yes"}:
        return True
    return has_gemini_key()


def _configured_watchlist_path(watchlist_path: str | Path | None) -> str | None:
    if watchlist_path:
        return str(watchlist_path)
    return os.environ.get("PAGE_WATCH_WATCHLIST") or None


def _configured_snapshot_dir(snapshot_dir: str | Path | None) -> Path:
    if snapshot_dir:
        return Path(snapshot_dir)
    return Path(os.environ.get("PAGE_WATCH_SNAPSHOT_DIR", ".page_watch_snapshots"))


def _normalize_target(target: WatchTarget, markup: str) -> str:
    return normalize_page(
        markup,
        selector=target.selector,
        start_anchor=target.start_anchor,
        end_anchor=target.end_anchor,
    )


def _page_result(
    *,
    target: WatchTarget,
    status: str,
    hunks: list[Hunk],
    judgments: list[Any],
    note: str = "",
) -> dict[str, Any]:
    return {
        "name": target.name,
        "url": target.url,
        "status": status,
        "note": note,
        "hunks": [hunk.to_dict() for hunk in hunks],
        "judgments": [
            judgment.to_dict() if hasattr(judgment, "to_dict") else judgment
            for judgment in judgments
        ],
        "keywords": list(target.merged_keywords()),
    }


def run_page_watch(
    *,
    watchlist_path: str | Path | None = None,
    snapshot_dir: str | Path | None = None,
    live: bool | None = None,
    live_model: bool | None = None,
    page_name: str = "",
) -> dict[str, Any]:
    """Run fetch/normalize/diff (or sample fixtures) and render a brief."""

    try:
        from .delivery import render_brief
        from .judge import judge_hunks
    except ImportError:
        from delivery import render_brief
        from judge import judge_hunks

    live_fetch = _live_fetch_enabled(live)
    use_model = _live_model_enabled(live_model) and live_fetch
    configured_watchlist = _configured_watchlist_path(watchlist_path)
    errors: list[str] = []
    page_results: list[dict[str, Any]] = []
    material_judgments: list[Any] = []

    if live_fetch:
        if not configured_watchlist:
            raise FileNotFoundError(
                "Set PAGE_WATCH_WATCHLIST or pass watchlist_path to fetch live pages."
            )
        targets = load_watchlist(configured_watchlist)
        snapshots = _configured_snapshot_dir(snapshot_dir)
        snapshots.mkdir(parents=True, exist_ok=True)
        if page_name:
            targets = [target for target in targets if page_name.lower() in target.name.lower()]
        for target in targets:
            try:
                markup = fetch_url(target.url)
                current = _normalize_target(target, markup)
            except RuntimeError as exc:
                errors.append(str(exc))
                page_results.append(
                    _page_result(
                        target=target,
                        status="error",
                        hunks=[],
                        judgments=[],
                        note=str(exc),
                    )
                )
                continue
            previous = load_snapshot(snapshots, target.url)
            save_snapshot(
                snapshots,
                url=target.url,
                name=target.name,
                normalized_text=current,
            )
            if previous is None:
                page_results.append(
                    _page_result(
                        target=target,
                        status="baseline",
                        hunks=[],
                        judgments=[],
                        note="Baseline captured. Future runs will brief material changes.",
                    )
                )
                continue
            hunks = diff_paragraphs(
                str(previous.get("normalized_text") or ""),
                current,
                page_name=target.name,
                page_url=target.url,
            )
            judgments = judge_hunks(
                hunks,
                keywords=target.merged_keywords(),
                sample=not use_model,
            )
            material = [item for item in judgments if item.classification == "material"]
            material_judgments.extend(material)
            status = "material" if material else "no_material_change"
            page_results.append(
                _page_result(
                    target=target,
                    status=status,
                    hunks=hunks,
                    judgments=judgments,
                    note="" if material else "No material change.",
                )
            )
        watch_mode = "live_fetch"
        watchlist_label = configured_watchlist
    else:
        pages = SAMPLE_PAGES
        if page_name:
            pages = [page for page in pages if page_name.lower() in page.target.name.lower()]
        for page in pages:
            target = page.target
            before = _normalize_target(target, page.before_html)
            after = _normalize_target(target, page.after_html)
            hunks = diff_paragraphs(
                before,
                after,
                page_name=target.name,
                page_url=target.url,
            )
            judgments = judge_hunks(
                hunks,
                keywords=target.merged_keywords(),
                sample=True,
            )
            material = [item for item in judgments if item.classification == "material"]
            material_judgments.extend(material)
            status = "material" if material else "no_material_change"
            page_results.append(
                _page_result(
                    target=target,
                    status=status,
                    hunks=hunks,
                    judgments=judgments,
                    note="" if material else "No material change.",
                )
            )
        watch_mode = "sample"
        watchlist_label = "deterministic sample pages"

    judge_mode = "gemini" if use_model else "sample"
    brief = render_brief(
        page_results,
        watch_mode=watch_mode,
        watchlist_path=watchlist_label,
        pages_checked=len(page_results),
        errors=errors,
        judge_mode=judge_mode,
    ).to_dict()
    brief["judge_mode"] = judge_mode
    brief["delivery_note"] = (
        "The brief is rendered only. Scheduled delivery stays off until dry_run=false "
        "and Gmail or webhook settings are present."
    )
    return brief


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Page Watch: brief me when watched pages change in ways that matter."
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Run deterministic sample pages (no fetch, no model).",
    )
    parser.add_argument("--watchlist", default=None, help="YAML or JSON watch list.")
    parser.add_argument(
        "--snapshot-dir",
        default=None,
        help="Directory for URL-keyed snapshots.",
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Fetch watch-list URLs and compare them to stored snapshots.",
    )
    parser.add_argument(
        "--live-model",
        action="store_true",
        help=(
            "Force Gemini hunk judgments. --fetch already uses Gemini when "
            "GOOGLE_API_KEY or GEMINI_API_KEY is set; --sample never calls the model."
        ),
    )
    parser.add_argument("--page", default="", help="Optional page-name filter.")
    parser.add_argument("--json", action="store_true", help="Print the full JSON payload.")
    args = parser.parse_args(argv)
    live = False if args.sample else (True if args.fetch else None)
    if args.sample:
        live_model: bool | None = False
    elif args.live_model:
        live_model = True
    else:
        live_model = None
    payload = run_page_watch(
        watchlist_path=args.watchlist,
        snapshot_dir=args.snapshot_dir,
        live=live,
        live_model=live_model,
        page_name=args.page,
    )
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(payload["text"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
