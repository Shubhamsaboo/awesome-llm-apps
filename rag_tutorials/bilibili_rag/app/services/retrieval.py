"""
Retrieval helpers for hybrid recall.

Keep this module dependency-light so the ranking logic can be tested without
initializing embeddings, Chroma, or external model clients.
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Iterable, Mapping, Sequence


_STOPWORDS = {
    "什么", "怎么", "如何", "是否", "可以", "哪个", "哪些", "请问", "一下", "为什么",
    "有没有", "能不能", "能否", "是不是", "是什么", "多少", "哪里", "讲讲", "介绍",
    "总结", "概括", "分析", "解释", "说明", "评价", "区别", "内容", "视频", "收藏",
    "收藏夹", "知识库", "这个", "那个", "里面", "相关", "关于", "一下", "一下子",
}


def extract_keywords(text: str, max_keywords: int = 16) -> list[str]:
    """Extract recall-oriented keywords without adding tokenizer dependencies."""
    if not text:
        return []

    cleaned = text.strip()
    for stopword in sorted(_STOPWORDS, key=len, reverse=True):
        cleaned = cleaned.replace(stopword, " ")

    keywords: list[str] = []
    seen: set[str] = set()

    def add(token: str) -> None:
        token = token.strip()
        if len(token) < 2 or token in _STOPWORDS or token in seen:
            return
        seen.add(token)
        keywords.append(token)

    for token in re.findall(r"[A-Za-z][A-Za-z0-9_+.#-]{1,}|[0-9]{2,}", cleaned):
        add(token)

    for chunk in re.findall(r"[\u4e00-\u9fff]{2,}", cleaned):
        add(chunk)
        # Chinese text often arrives as one long token. Add char n-grams so
        # keyword recall can still hit titles/content without jieba.
        if len(chunk) > 4:
            for size in (4, 3, 2):
                for idx in range(0, len(chunk) - size + 1):
                    add(chunk[idx:idx + size])
                    if len(keywords) >= max_keywords:
                        return keywords
        if len(keywords) >= max_keywords:
            return keywords

    return keywords[:max_keywords]


def keyword_score(
    keywords: Sequence[str],
    *,
    title: str = "",
    description: str = "",
    content: str = "",
    owner_name: str = "",
) -> float:
    """Score text fields for keyword recall. Title/owner matches are boosted."""
    if not keywords:
        return 0.0

    score = 0.0
    fields = (
        (title or "", 8.0),
        (owner_name or "", 5.0),
        (description or "", 3.0),
        (content or "", 1.0),
    )

    for keyword in keywords:
        weight = min(max(len(keyword), 2), 8)
        keyword_lower = keyword.lower()
        for value, field_weight in fields:
            if not value:
                continue
            haystack = value.lower() if re.search(r"[A-Za-z]", keyword) else value
            needle = keyword_lower if re.search(r"[A-Za-z]", keyword) else keyword
            count = haystack.count(needle)
            if count:
                score += count * field_weight * weight
    return score


def build_snippet(text: str, keywords: Sequence[str], max_length: int = 700) -> str:
    """Return a compact snippet around the first keyword hit."""
    value = (text or "").strip()
    if len(value) <= max_length:
        return value

    first_hit = -1
    for keyword in keywords:
        idx = value.lower().find(keyword.lower()) if re.search(r"[A-Za-z]", keyword) else value.find(keyword)
        if idx >= 0 and (first_hit < 0 or idx < first_hit):
            first_hit = idx

    if first_hit < 0:
        return value[:max_length].rstrip() + "..."

    start = max(0, first_hit - max_length // 3)
    end = min(len(value), start + max_length)
    snippet = value[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(value):
        snippet += "..."
    return snippet


def _metadata(doc: Any) -> dict:
    meta = getattr(doc, "metadata", None)
    return meta if isinstance(meta, dict) else {}


def document_identity(doc: Any) -> str:
    """Stable identity for dedupe across retrieval channels."""
    meta = _metadata(doc)
    bvid = meta.get("bvid")
    doc_type = meta.get("doc_type", "chunk")
    chunk_index = meta.get("chunk_index")
    if bvid:
        return f"{bvid}:{doc_type}:{chunk_index}"
    return str(id(doc))


def merge_ranked_documents(
    rankings: Mapping[str, Sequence[Any]],
    *,
    top_k: int,
    channel_weights: Mapping[str, float] | None = None,
    rank_constant: int = 60,
    per_video_limit: int = 2,
) -> list[Any]:
    """Fuse multiple ranked lists with RRF and keep source diversity."""
    if top_k <= 0:
        return []

    weights = channel_weights or {}
    scores: dict[str, float] = defaultdict(float)
    docs_by_key: dict[str, Any] = {}
    best_rank: dict[str, int] = {}

    for channel, docs in rankings.items():
        weight = weights.get(channel, 1.0)
        for rank, doc in enumerate(docs, start=1):
            key = document_identity(doc)
            docs_by_key.setdefault(key, doc)
            scores[key] += weight / (rank_constant + rank)
            best_rank[key] = min(best_rank.get(key, rank), rank)

    ordered_keys = sorted(
        docs_by_key,
        key=lambda key: (-scores[key], best_rank.get(key, 10_000), key),
    )

    results: list[Any] = []
    per_video_counts: dict[str, int] = defaultdict(int)
    deferred: list[str] = []

    for key in ordered_keys:
        doc = docs_by_key[key]
        bvid = _metadata(doc).get("bvid")
        if bvid and per_video_counts[bvid] >= per_video_limit:
            deferred.append(key)
            continue
        results.append(doc)
        if bvid:
            per_video_counts[bvid] += 1
        if len(results) >= top_k:
            break

    if len(results) < top_k:
        existing = {document_identity(doc) for doc in results}
        for key in deferred:
            if key in existing:
                continue
            results.append(docs_by_key[key])
            if len(results) >= top_k:
                break

    for doc in results:
        meta = _metadata(doc)
        if meta:
            meta["retrieval_score"] = round(scores[document_identity(doc)], 6)

    return results
