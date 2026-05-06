#!/usr/bin/env python3
"""
Research Agent with Cross-Provider Adversarial Fact-Checking
============================================================
Researches any topic using real web search (DuckDuckGo), synthesizes a report
with inline citations, then adversarially fact-checks every claim using a
completely different AI provider — eliminating shared model biases.

Pipeline: topic → research plan → web search → fetch & extract → report → fact-check
Research uses OpenAI. Fact-checking uses Anthropic Claude.
All sessions are logged to SQLite (~/.research_agent/).

Usage:
    python research_agent.py "What are the health effects of intermittent fasting?"
    python research_agent.py --list
    python research_agent.py --show <id-prefix>

Requirements:  pip install -r requirements.txt
Environment:   OPENAI_API_KEY (research) + ANTHROPIC_API_KEY (fact-check)
"""
from __future__ import annotations

import argparse, datetime, json, os, sqlite3, sys, uuid
from pathlib import Path
from typing import Any

import anthropic
import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS
from newspaper import Article
from openai import OpenAI

try:
    from rich.console import Console
    from rich.table import Table
    console = Console()
    HAS_RICH = True
except ImportError:
    console = None  # type: ignore
    HAS_RICH = False

# ─── Config ──────────────────────────────────────────────────────────────────

DATA_DIR  = Path.home() / ".research_agent"
DB_PATH   = DATA_DIR / "research.db"
RESEARCH_MODEL  = os.environ.get("RESEARCH_AGENT_MODEL", "gpt-4o-mini")
FACTCHECK_MODEL = os.environ.get("FACTCHECK_AGENT_MODEL", "claude-sonnet-4-20250514")
THRESHOLD = 0.75   # min fact-check confidence to accept
MAX_FETCH = 50_000  # chars per URL

# ─── Database ────────────────────────────────────────────────────────────────

DDL = """
CREATE TABLE IF NOT EXISTS research (
    id TEXT PRIMARY KEY, topic TEXT NOT NULL, status TEXT NOT NULL,
    report TEXT, sources_json TEXT, verdict TEXT, confidence REAL,
    fact_check_json TEXT, created_at TEXT NOT NULL, finished_at TEXT
);
CREATE TABLE IF NOT EXISTS fetches (
    id TEXT PRIMARY KEY, research_id TEXT NOT NULL, url TEXT NOT NULL,
    title TEXT, content_preview TEXT, fetched_at TEXT NOT NULL
);"""


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(DDL)
    conn.commit()


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# ─── LLM Clients ────────────────────────────────────────────────────────────

def get_research_client() -> OpenAI:
    base_url = os.environ.get("OPENAI_BASE_URL")
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("ERROR: OPENAI_API_KEY not set. Required for research stage.")
    return OpenAI(api_key=key, base_url=base_url) if base_url else OpenAI(api_key=key)


def get_factcheck_client() -> anthropic.Anthropic:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit(
            "ERROR: ANTHROPIC_API_KEY not set. Required for independent fact-checking.\n"
            "The fact-checker uses a different AI provider (Anthropic Claude) to ensure\n"
            "truly independent verification with different training data and biases."
        )
    return anthropic.Anthropic(api_key=key)


def chat(client: OpenAI, messages: list[dict], json_mode: bool = False) -> str:
    kw: dict[str, Any] = {"model": RESEARCH_MODEL, "messages": messages}
    if json_mode:
        kw["response_format"] = {"type": "json_object"}
    return client.chat.completions.create(**kw).choices[0].message.content or ""


# ─── Web Search & Content Extraction ────────────────────────────────────────

def search_web(query: str, max_results: int = 3) -> list[dict]:
    """Search DuckDuckGo and return real URLs with titles."""
    try:
        results = DDGS().text(query, max_results=max_results)
        return results  # [{"title": ..., "href": ..., "body": ...}]
    except Exception as e:
        pr(f"    Search error: {e}", "dim")
        return []


def fetch_url(url: str) -> str:
    """Fetch a URL and extract clean text content."""
    # Try newspaper4k first (best for articles)
    try:
        article = Article(url)
        article.download()
        article.parse()
        if article.text and len(article.text) > 100:
            return article.text[:MAX_FETCH]
    except Exception:
        pass

    # Fallback: fetch raw HTML and extract with BeautifulSoup
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as h:
            r = h.get(url, headers={"User-Agent": "research-agent/2.0"})
            r.raise_for_status()
            soup = BeautifulSoup(r.text[:MAX_FETCH], "html.parser")
            # Remove non-content elements
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            return text[:MAX_FETCH] if text else "ERROR: No text content extracted"
    except httpx.HTTPStatusError as e:
        return f"ERROR: HTTP {e.response.status_code}"
    except Exception as e:
        return f"ERROR: {e}"


# ─── UI ──────────────────────────────────────────────────────────────────────

def pr(msg: str, style: str = "") -> None:
    (console.print(msg, style=style) if HAS_RICH else print(msg))  # type: ignore


def section(title: str) -> None:
    (console.rule(f"[bold]{title}") if HAS_RICH  # type: ignore
     else print(f"\n{'─'*60}\n  {title}\n{'─'*60}"))


# ─── Stage 1: Research Plan ─────────────────────────────────────────────────

PLAN_SYS = """You are a research planner. Given a topic, produce a research plan.

Return ONLY valid JSON:
{"topic_refined":"<clear restatement of the research question>",
 "search_queries":[{"index":0,"query":"<search query>","rationale":"<why this source matters>"}],
 "output_format":"<what the final report should contain>"}

Rules:
- Generate 3-6 search queries that would find authoritative sources
- Prefer official sources, academic references, and reputable publications
- Include at least one query targeting a contrarian or skeptical perspective
- Each query should target a DIFFERENT aspect of the topic"""


def plan_research(client: OpenAI, topic: str) -> dict:
    section("Planning Research")
    raw = chat(client,
               [{"role": "system", "content": PLAN_SYS},
                {"role": "user", "content": topic}],
               json_mode=True)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"topic_refined": topic,
                "search_queries": [{"index": 0, "query": topic, "rationale": "direct search"}],
                "output_format": "structured report with citations"}


# ─── Stage 2: Source Gathering ───────────────────────────────────────────────

def gather_sources(conn: sqlite3.Connection,
                   research_id: str, plan: dict) -> list[dict]:
    section("Gathering Sources")
    sources: list[dict] = []

    for i, sq in enumerate(plan.get("search_queries", [])):
        query = sq.get("query", "")
        pr(f"  Searching: {query}", "dim")

        # Real web search via DuckDuckGo
        results = search_web(query, max_results=3)

        for result in results:
            url = result.get("href", "")
            title = result.get("title", url)
            if not url:
                continue

            pr(f"    Fetching: {url}", "dim")
            content = fetch_url(url)

            if content.startswith("ERROR"):
                pr(f"    {content}", "dim")
                continue

            source = {
                "url": url,
                "title": title,
                "content": content[:4000],
                "query": query,
            }
            sources.append(source)

            conn.execute(
                "INSERT INTO fetches VALUES (?,?,?,?,?,?)",
                (str(uuid.uuid4()), research_id, url, title,
                 content[:500], now()),
            )
            conn.commit()

    pr(f"\n  Gathered {len(sources)} sources", "bold")
    return sources


# ─── Stage 3: Report Synthesis ───────────────────────────────────────────────

SYNTHESIS_SYS = """You are a research report writer. Given a topic and source material,
write a well-structured report with inline citations.

Rules:
- Every factual claim MUST cite a source using [Source N] notation
- Include a "Sources" section at the end listing each [Source N] with its URL
- If sources disagree, note the disagreement explicitly
- Flag any claims you make that are NOT supported by the provided sources
- Structure: Introduction → Key Findings → Analysis → Limitations → Sources
- Be concise but thorough (500-1500 words)"""


def synthesize_report(client: OpenAI, topic: str, sources: list[dict]) -> str:
    section("Synthesizing Report")
    source_text = "\n\n".join(
        f"[Source {i+1}] {s['url']}\n{s['content']}"
        for i, s in enumerate(sources)
    )
    report = chat(client,
                  [{"role": "system", "content": SYNTHESIS_SYS},
                   {"role": "user", "content":
                       f"Topic: {topic}\n\nSource Material:\n{source_text}"}])
    return report


# ─── Stage 4: Cross-Provider Adversarial Fact-Check ─────────────────────────

FACT_CHECK_SYS = """You are a strict adversarial fact-checker. Your default stance is REJECT.
Your job is to find unsupported claims, missing citations, and fabricated sources.

IMPORTANT: You are a DIFFERENT AI system than the one that wrote this report.
You have different training data and different biases. Use this independence
to catch errors the original author's model might be blind to.

For each claim in the report, check:
1. Is it cited with a [Source N] reference?
2. Does the source material actually support the claim, or was it fabricated/exaggerated?
3. Are there important caveats the report omitted?

Mandatory rejection rules — if ANY apply, verdict must be "reject":
1. More than 30% of factual claims lack citations
2. Any cited source URL is clearly fabricated (not a real website)
3. A claim directly contradicts its cited source
4. The report draws conclusions not supported by any provided source

Confidence scale:
- 0.0–0.4: serious factual problems (fabricated claims, missing citations)
- 0.4–0.74: some unsupported claims or weak sourcing
- 0.75+: all major claims are cited and supported by source material

Return ONLY valid JSON:
{"verdict":"accept|reject","confidence":0.0-1.0,
 "claims_checked":[{"claim":"<quote from report>","source_cited":"<Source N or none>",
   "supported":true,"note":"<explanation>"}],
 "unsupported_claims":["<list of claims without adequate support>"],
 "source_quality":"<assessment of source diversity and authority>",
 "overall_reason":"<paragraph explaining the fact-check result>"}"""


def fact_check(topic: str, report: str, sources: list[dict]) -> dict:
    section("Cross-Provider Adversarial Fact-Check")
    pr(f"  Research model: {RESEARCH_MODEL} (OpenAI)", "dim")
    pr(f"  Fact-check model: {FACTCHECK_MODEL} (Anthropic)", "dim")

    client = get_factcheck_client()
    source_list = "\n".join(
        f"[Source {i+1}] {s['url']}: {s['content'][:500]}"
        for i, s in enumerate(sources)
    )

    user_content = (
        f"{FACT_CHECK_SYS}\n\n"
        f"Topic: {topic}\n\n"
        f"Report to fact-check:\n{report}\n\n"
        f"Available source material:\n{source_list}"
    )

    try:
        response = client.messages.create(
            model=FACTCHECK_MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": user_content}],
        )
        raw = response.content[0].text
    except Exception as e:
        return {"verdict": "reject", "confidence": 0.0,
                "claims_checked": [],
                "unsupported_claims": [f"Fact-check failed: {e}"],
                "source_quality": "unknown",
                "overall_reason": f"Anthropic API error: {e}"}

    # Parse JSON from response (Claude may wrap in markdown code blocks)
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1])

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"verdict": "reject", "confidence": 0.0,
                "claims_checked": [],
                "unsupported_claims": ["Fact-check produced malformed output"],
                "source_quality": "unknown",
                "overall_reason": f"Fact-checker returned invalid JSON: {raw[:200]}"}


# ─── Main Pipeline ──────────────────────────────────────────────────────────

def research_topic(client: OpenAI, conn: sqlite3.Connection,
                   topic: str) -> str:
    research_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO research VALUES (?,?,?,?,?,?,?,?,?,?)",
        (research_id, topic, "planning", None, None, None, None, None,
         now(), None),
    )
    conn.commit()
    section("Research Topic")
    pr(topic)

    # 1. Plan
    plan = plan_research(client, topic)
    pr(f"\nRefined topic: {plan.get('topic_refined', topic)}", "bold")
    for i, sq in enumerate(plan.get("search_queries", [])):
        pr(f"  {i+1}. {sq.get('query', '')}", "dim")

    # 2. Gather sources (no LLM needed — uses DuckDuckGo directly)
    conn.execute("UPDATE research SET status='gathering' WHERE id=?",
                 (research_id,))
    conn.commit()
    sources = gather_sources(conn, research_id, plan)

    if not sources:
        pr("[ERROR] No sources could be fetched. Aborting.", "bold red")
        conn.execute(
            "UPDATE research SET status='failed',finished_at=? WHERE id=?",
            (now(), research_id),
        )
        conn.commit()
        return research_id

    conn.execute("UPDATE research SET sources_json=? WHERE id=?",
                 (json.dumps([{"url": s["url"], "title": s["title"]}
                              for s in sources]), research_id))
    conn.commit()

    # 3. Synthesize report (OpenAI)
    conn.execute("UPDATE research SET status='synthesizing' WHERE id=?",
                 (research_id,))
    conn.commit()
    report = synthesize_report(client, plan.get("topic_refined", topic), sources)
    pr(f"\n{report}")

    conn.execute("UPDATE research SET report=? WHERE id=?",
                 (report, research_id))
    conn.commit()

    # 4. Cross-provider fact-check (Anthropic Claude)
    conn.execute("UPDATE research SET status='fact_checking' WHERE id=?",
                 (research_id,))
    conn.commit()
    fc = fact_check(topic, report, sources)

    verdict = fc.get("verdict", "reject")
    try:
        confidence = float(fc.get("confidence", 0))
    except (ValueError, TypeError):
        confidence = 0.0
    reason = fc.get("overall_reason", "")

    if verdict == "accept" and confidence < THRESHOLD:
        verdict = "reject"
        reason = f"Confidence {confidence:.0%} below {THRESHOLD:.0%}. " + reason

    # Display verdict
    section("Fact-Check Verdict")
    if verdict == "accept":
        pr(f"VERIFIED ({confidence:.0%})", "bold green")
    else:
        pr(f"FLAGGED ({confidence:.0%})", "bold red")

    pr(f"\n{reason}")
    pr(f"\nSource quality: {fc.get('source_quality', 'unknown')}", "dim")

    for claim in fc.get("claims_checked", []):
        icon = "✓" if claim.get("supported") else "✗"
        pr(f"  {icon} {claim.get('claim', '')[:80]}", "dim")
        if claim.get("note"):
            pr(f"    → {claim['note']}", "dim")

    unsupported = fc.get("unsupported_claims", [])
    if unsupported:
        pr("\nUnsupported claims:", "bold red")
        for uc in unsupported:
            pr(f"  ✗ {uc}", "dim")

    conn.execute(
        "UPDATE research SET status=?,verdict=?,confidence=?,"
        "fact_check_json=?,finished_at=? WHERE id=?",
        (verdict, verdict, confidence, json.dumps(fc), now(), research_id),
    )
    conn.commit()
    return research_id


# ─── CLI ─────────────────────────────────────────────────────────────────────

def list_research(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        "SELECT id, status, verdict, confidence, created_at, topic "
        "FROM research ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    if not rows:
        pr("No research sessions.")
        return
    if HAS_RICH:
        t = Table(title="Recent Research", show_lines=True)
        for col in ("ID", "Status", "Verdict", "Conf", "Created", "Topic"):
            t.add_column(col)
        for r in rows:
            t.add_row(
                r[0][:8], r[1], r[2] or "—",
                f"{r[3]:.0%}" if r[3] is not None else "—",
                r[4][:16], r[5][:60],
            )
        console.print(t)  # type: ignore
    else:
        for r in rows:
            print(f"{r[0][:8]} | {r[1]:12} | {r[2] or '—':8} | {r[4][:16]} | {r[5][:60]}")


def show_research(conn: sqlite3.Connection, prefix: str) -> None:
    row = conn.execute("SELECT * FROM research WHERE id LIKE ?",
                       (prefix + "%",)).fetchone()
    if not row:
        pr(f"No research matching '{prefix}'", "bold red")
        return
    pr(f"\nID: {row[0]}\nTopic: {row[1]}\nStatus: {row[2]}")
    pr(f"Verdict: {row[5]} | Confidence: {row[6]}")
    if row[3]:
        pr(f"\n{row[3]}")
    fetches = conn.execute(
        "SELECT url, title FROM fetches WHERE research_id=?", (row[0],)
    ).fetchall()
    if fetches:
        pr("\nSources fetched:", "bold")
        for f in fetches:
            pr(f"  • {f[1][:60]} — {f[0]}", "dim")


def main() -> None:
    global RESEARCH_MODEL, FACTCHECK_MODEL
    p = argparse.ArgumentParser(description="Research agent with cross-provider fact-checking")
    p.add_argument("topic", nargs="?", help="Research topic or question")
    p.add_argument("--list", action="store_true", help="List past research")
    p.add_argument("--show", help="Show research by ID prefix")
    p.add_argument("--model", default=RESEARCH_MODEL, help="Research model (OpenAI)")
    p.add_argument("--factcheck-model", default=FACTCHECK_MODEL, help="Fact-check model (Anthropic)")
    args = p.parse_args()

    RESEARCH_MODEL = args.model
    FACTCHECK_MODEL = args.factcheck_model
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    if args.list:
        list_research(conn)
        return
    if args.show:
        show_research(conn, args.show)
        return

    if not args.topic:
        try:
            from rich.prompt import Prompt
            topic = Prompt.ask("[bold]What would you like to research?[/bold]")
        except ImportError:
            topic = input("Research topic: ").strip()
        if not topic:
            sys.exit("No topic provided.")
    else:
        topic = args.topic

    client = get_research_client()
    rid = research_topic(client, conn, topic)
    pr(f"\nResearch ID: {rid}", "dim")
    conn.close()


if __name__ == "__main__":
    main()
