"""Review queue for human verification of news and content.

SQLite-backed queue that holds news items and generated content
for human approval before publication.
"""

import sqlite3
import json
import os
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

DB_PATH = os.getenv("CONTENT_FACTORY_DB", "content_factory.db")


class ReviewStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    published = "published"


class NewsForReview(BaseModel):
    id: Optional[int] = None
    title: str
    link: str
    summary: str = ""
    source: str = ""
    category: str = ""
    language: str = ""
    status: ReviewStatus = ReviewStatus.pending
    reviewer_notes: str = ""
    created_at: str = ""
    reviewed_at: str = ""


class ContentForReview(BaseModel):
    id: Optional[int] = None
    news_id: Optional[int] = Field(None, description="ID of the source news item")
    topic: str
    content_type: str
    service_focus: str
    language: str
    target_keywords: str = ""
    content_markdown: str = ""
    meta_title: str = ""
    meta_description: str = ""
    image_url: str = ""
    image_prompt: str = ""
    status: ReviewStatus = ReviewStatus.pending
    reviewer_notes: str = ""
    created_at: str = ""
    reviewed_at: str = ""


class ReviewDecision(BaseModel):
    status: ReviewStatus = Field(..., description="approved or rejected")
    reviewer_notes: str = Field("", description="Optional reviewer comments")


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS news_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            link TEXT NOT NULL,
            summary TEXT DEFAULT '',
            source TEXT DEFAULT '',
            category TEXT DEFAULT '',
            language TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            reviewer_notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            reviewed_at TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS content_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id INTEGER,
            topic TEXT NOT NULL,
            content_type TEXT DEFAULT '',
            service_focus TEXT DEFAULT '',
            language TEXT DEFAULT 'German',
            target_keywords TEXT DEFAULT '',
            content_markdown TEXT DEFAULT '',
            meta_title TEXT DEFAULT '',
            meta_description TEXT DEFAULT '',
            image_url TEXT DEFAULT '',
            image_prompt TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            reviewer_notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            reviewed_at TEXT DEFAULT '',
            FOREIGN KEY (news_id) REFERENCES news_queue(id)
        );

        CREATE TABLE IF NOT EXISTS social_media_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            post_text TEXT DEFAULT '',
            image_url TEXT DEFAULT '',
            video_url TEXT DEFAULT '',
            voiceover_url TEXT DEFAULT '',
            voiceover_text TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            reviewer_notes TEXT DEFAULT '',
            scheduled_at TEXT DEFAULT '',
            published_at TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            reviewed_at TEXT DEFAULT '',
            FOREIGN KEY (content_id) REFERENCES content_queue(id)
        );
    """)
    conn.commit()
    conn.close()


# ── News Queue ──────────────────────────────────────────────────────────


def add_news_to_queue(items: list[dict]) -> list[int]:
    """Add news items to the review queue. Returns list of new IDs."""
    conn = _get_db()
    ids = []
    for item in items:
        # Skip duplicates by link
        existing = conn.execute(
            "SELECT id FROM news_queue WHERE link = ?", (item.get("link", ""),)
        ).fetchone()
        if existing:
            continue
        cur = conn.execute(
            "INSERT INTO news_queue (title, link, summary, source, category, language) VALUES (?, ?, ?, ?, ?, ?)",
            (item.get("title", ""), item.get("link", ""), item.get("summary", ""),
             item.get("source", ""), item.get("category", ""), item.get("language", "")),
        )
        ids.append(cur.lastrowid)
    conn.commit()
    conn.close()
    return ids


def get_news_queue(status: Optional[str] = None, limit: int = 50) -> list[dict]:
    """Get news items from the queue, optionally filtered by status."""
    conn = _get_db()
    if status:
        rows = conn.execute(
            "SELECT * FROM news_queue WHERE status = ? ORDER BY created_at DESC LIMIT ?",
            (status, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM news_queue ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def review_news(news_id: int, decision: ReviewDecision) -> dict:
    """Approve or reject a news item."""
    conn = _get_db()
    conn.execute(
        "UPDATE news_queue SET status = ?, reviewer_notes = ?, reviewed_at = datetime('now') WHERE id = ?",
        (decision.status.value, decision.reviewer_notes, news_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM news_queue WHERE id = ?", (news_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


# ── Content Queue ───────────────────────────────────────────────────────


def add_content_to_queue(content: dict) -> int:
    """Add generated content to the review queue. Returns new ID."""
    conn = _get_db()
    cur = conn.execute(
        """INSERT INTO content_queue
        (news_id, topic, content_type, service_focus, language, target_keywords,
         content_markdown, meta_title, meta_description, image_url, image_prompt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (content.get("news_id"), content.get("topic", ""), content.get("content_type", ""),
         content.get("service_focus", ""), content.get("language", "German"),
         content.get("target_keywords", ""), content.get("content_markdown", ""),
         content.get("meta_title", ""), content.get("meta_description", ""),
         content.get("image_url", ""), content.get("image_prompt", "")),
    )
    conn.commit()
    content_id = cur.lastrowid
    conn.close()
    return content_id


def get_content_queue(status: Optional[str] = None, limit: int = 50) -> list[dict]:
    """Get content items from the queue."""
    conn = _get_db()
    if status:
        rows = conn.execute(
            "SELECT * FROM content_queue WHERE status = ? ORDER BY created_at DESC LIMIT ?",
            (status, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM content_queue ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def review_content(content_id: int, decision: ReviewDecision) -> dict:
    """Approve or reject content."""
    conn = _get_db()
    conn.execute(
        "UPDATE content_queue SET status = ?, reviewer_notes = ?, reviewed_at = datetime('now') WHERE id = ?",
        (decision.status.value, decision.reviewer_notes, content_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM content_queue WHERE id = ?", (content_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


def mark_content_published(content_id: int) -> dict:
    conn = _get_db()
    conn.execute(
        "UPDATE content_queue SET status = 'published', reviewed_at = datetime('now') WHERE id = ?",
        (content_id,),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM content_queue WHERE id = ?", (content_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


# ── Social Media Queue ──────────────────────────────────────────────────


def add_social_media_to_queue(items: list[dict]) -> list[int]:
    """Add social media posts to the review queue."""
    conn = _get_db()
    ids = []
    for item in items:
        cur = conn.execute(
            """INSERT INTO social_media_queue
            (content_id, platform, post_text, image_url, video_url, voiceover_url,
             voiceover_text, scheduled_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (item.get("content_id"), item.get("platform", ""), item.get("post_text", ""),
             item.get("image_url", ""), item.get("video_url", ""),
             item.get("voiceover_url", ""), item.get("voiceover_text", ""),
             item.get("scheduled_at", "")),
        )
        ids.append(cur.lastrowid)
    conn.commit()
    conn.close()
    return ids


def get_social_media_queue(status: Optional[str] = None, content_id: Optional[int] = None, limit: int = 50) -> list[dict]:
    """Get social media items from the queue."""
    conn = _get_db()
    conditions = []
    params = []
    if status:
        conditions.append("status = ?")
        params.append(status)
    if content_id:
        conditions.append("content_id = ?")
        params.append(content_id)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)
    rows = conn.execute(
        f"SELECT * FROM social_media_queue {where} ORDER BY created_at DESC LIMIT ?", params
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def review_social_media(sm_id: int, decision: ReviewDecision) -> dict:
    """Approve or reject a social media post."""
    conn = _get_db()
    conn.execute(
        "UPDATE social_media_queue SET status = ?, reviewer_notes = ?, reviewed_at = datetime('now') WHERE id = ?",
        (decision.status.value, decision.reviewer_notes, sm_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM social_media_queue WHERE id = ?", (sm_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


def mark_social_media_published(sm_id: int) -> dict:
    conn = _get_db()
    conn.execute(
        "UPDATE social_media_queue SET status = 'published', published_at = datetime('now') WHERE id = ?",
        (sm_id,),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM social_media_queue WHERE id = ?", (sm_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


# Initialize DB on import
init_db()
