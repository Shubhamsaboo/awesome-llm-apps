"""
Streamlit frontend for the Research Agent with Adversarial Fact-Checking.

Enter a research topic → agent fetches real sources → writes a cited report →
adversarial fact-checker verifies every claim has supporting evidence.
"""
from __future__ import annotations

import json
import os
import sqlite3
import uuid

import streamlit as st

import research_agent as ra

# ─── Page Config ────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Research Fact-Checker",
    page_icon="🔍",
    layout="wide",
)
st.title("AI Research Agent with Fact-Checking")
st.caption(
    "Research any topic with real web sources, then adversarially verify "
    "that every claim is properly cited and supported."
)

# ─── Sidebar ────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=os.environ.get("OPENAI_API_KEY", ""),
        help="Required. Supports any OpenAI-compatible provider via Base URL.",
    )
    base_url = st.text_input(
        "Base URL (optional)",
        value=os.environ.get("OPENAI_BASE_URL", ""),
        help="For alternate providers (e.g. Ollama, Together, DeepInfra).",
    )
    model = st.selectbox(
        "Model",
        ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1-nano"],
        index=0,
    )
    threshold = st.slider(
        "Fact-check confidence threshold",
        min_value=0.0, max_value=1.0, value=0.75, step=0.05,
        help="Minimum confidence to mark research as verified.",
    )

# ─── Tabs ───────────────────────────────────────────────────────────────────

tab_research, tab_history = st.tabs(["Research", "History"])

# ─── Database ───────────────────────────────────────────────────────────────

ra.DATA_DIR.mkdir(parents=True, exist_ok=True)


@st.cache_resource
def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(ra.DB_PATH), check_same_thread=False)
    ra.init_db(conn)
    return conn


conn = get_db()

# ─── Research Tab ───────────────────────────────────────────────────────────

with tab_research:
    topic = st.text_area(
        "What would you like to research?",
        placeholder="What are the health effects of intermittent fasting?",
        height=80,
    )

    if st.button("Research & Fact-Check", type="primary", disabled=not api_key):
        if not api_key:
            st.error("Enter an OpenAI API key in the sidebar.")
            st.stop()
        if not topic.strip():
            st.warning("Enter a research topic.")
            st.stop()

        # Configure
        ra.MODEL = model
        ra.THRESHOLD = threshold

        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url=base_url or None,
        )

        research_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO research VALUES (?,?,?,?,?,?,?,?,?,?)",
            (research_id, topic, "planning", None, None, None, None, None,
             ra.now(), None),
        )
        conn.commit()

        # ── Stage 1: Research Plan ──
        with st.status("Planning research...", expanded=True) as status:
            plan = ra.plan_research(client, topic)
            status.update(label="Research plan ready", state="complete")

        st.markdown(f"**Refined topic:** {plan.get('topic_refined', topic)}")
        for sq in plan.get("search_queries", []):
            st.markdown(f"- {sq['query']}")

        # ── Stage 2: Gather Sources ──
        with st.status("Fetching sources...", expanded=True) as status:
            conn.execute(
                "UPDATE research SET status='gathering' WHERE id=?",
                (research_id,),
            )
            conn.commit()
            sources = ra.gather_sources(client, conn, research_id, plan)

            if not sources:
                status.update(label="No sources found", state="error")
                st.error("Could not fetch any sources. Try a different topic.")
                conn.execute(
                    "UPDATE research SET status='failed',finished_at=? WHERE id=?",
                    (ra.now(), research_id),
                )
                conn.commit()
                st.stop()

            status.update(
                label=f"Gathered {len(sources)} sources", state="complete"
            )

        conn.execute(
            "UPDATE research SET sources_json=? WHERE id=?",
            (json.dumps([{"url": s["url"], "title": s["title"]}
                         for s in sources]), research_id),
        )
        conn.commit()

        with st.expander(f"Sources ({len(sources)})", expanded=False):
            for i, s in enumerate(sources):
                st.markdown(f"**[Source {i+1}]** [{s['title'][:80]}]({s['url']})")

        # ── Stage 3: Synthesize Report ──
        with st.status("Writing report...", expanded=True) as status:
            conn.execute(
                "UPDATE research SET status='synthesizing' WHERE id=?",
                (research_id,),
            )
            conn.commit()
            report = ra.synthesize_report(
                client, plan.get("topic_refined", topic), sources
            )
            conn.execute(
                "UPDATE research SET report=? WHERE id=?",
                (report, research_id),
            )
            conn.commit()
            status.update(label="Report written", state="complete")

        st.markdown("---")
        st.markdown(report)
        st.markdown("---")

        # ── Stage 4: Fact-Check ──
        with st.status(
            "Running adversarial fact-check...", expanded=True
        ) as status:
            conn.execute(
                "UPDATE research SET status='fact_checking' WHERE id=?",
                (research_id,),
            )
            conn.commit()
            fc = ra.fact_check(client, topic, report, sources)

            verdict = fc.get("verdict", "reject")
            try:
                confidence = float(fc.get("confidence", 0))
            except (ValueError, TypeError):
                confidence = 0.0
            reason = fc.get("overall_reason", "")

            if verdict == "accept" and confidence < threshold:
                verdict = "reject"
                reason = (
                    f"Confidence {confidence:.0%} below "
                    f"{threshold:.0%}. " + reason
                )

            if verdict == "accept":
                status.update(
                    label=f"Verified ({confidence:.0%})", state="complete"
                )
            else:
                status.update(
                    label=f"Flagged ({confidence:.0%})", state="error"
                )

        # ── Verdict Display ──
        if verdict == "accept":
            st.success(f"**VERIFIED** — Confidence: {confidence:.0%}")
        else:
            st.error(f"**FLAGGED** — Confidence: {confidence:.0%}")

        st.markdown(f"**Reason:** {reason}")
        st.markdown(
            f"**Source quality:** {fc.get('source_quality', 'unknown')}"
        )

        claims = fc.get("claims_checked", [])
        if claims:
            st.markdown("### Claim-by-Claim Check")
            for claim in claims:
                supported = claim.get("supported", False)
                icon = "✅" if supported else "❌"
                src = claim.get("source_cited", "none")
                st.markdown(
                    f"{icon} *\"{claim.get('claim', '')[:120]}\"* "
                    f"— Source: {src}"
                )
                if claim.get("note"):
                    st.caption(f"→ {claim['note']}")

        unsupported = fc.get("unsupported_claims", [])
        if unsupported:
            st.markdown("### Unsupported Claims")
            for uc in unsupported:
                st.markdown(f"- ❌ {uc}")

        conn.execute(
            "UPDATE research SET status=?,verdict=?,confidence=?,"
            "fact_check_json=?,finished_at=? WHERE id=?",
            (verdict, verdict, confidence, json.dumps(fc), ra.now(),
             research_id),
        )
        conn.commit()
        st.caption(f"Research ID: `{research_id}`")

# ─── History Tab ────────────────────────────────────────────────────────────

with tab_history:
    rows = conn.execute(
        "SELECT id, status, verdict, confidence, created_at, topic "
        "FROM research ORDER BY created_at DESC LIMIT 20"
    ).fetchall()

    if not rows:
        st.info("No research yet. Enter a topic in the **Research** tab.")
    else:
        for row in rows:
            rid, status, verdict, conf, created, t = row
            icon = (
                "✅" if verdict == "accept"
                else ("❌" if verdict == "reject" else "⏳")
            )
            conf_str = f"{conf:.0%}" if conf is not None else "—"
            with st.expander(
                f"{icon} {t[:80]} — {conf_str}", expanded=False
            ):
                st.markdown(f"**ID:** `{rid}`")
                st.markdown(
                    f"**Status:** {status} | **Verdict:** "
                    f"{verdict or '—'} | **Confidence:** {conf_str}"
                )
                st.markdown(f"**Created:** {created}")

                # Show sources
                fetches = conn.execute(
                    "SELECT url, title FROM fetches WHERE research_id=?",
                    (rid,),
                ).fetchall()
                if fetches:
                    st.markdown("**Sources:**")
                    for f in fetches:
                        st.markdown(f"- [{f[1][:60]}]({f[0]})")

                # Show report
                report_row = conn.execute(
                    "SELECT report FROM research WHERE id=?", (rid,)
                ).fetchone()
                if report_row and report_row[0]:
                    st.markdown("**Report:**")
                    st.markdown(report_row[0][:2000])
