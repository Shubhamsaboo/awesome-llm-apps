"""
Streamlit frontend for the Research Agent with Cross-Provider Fact-Checking.

Enter a research topic → agent searches DuckDuckGo for real sources → extracts
clean text → writes a cited report (OpenAI) → adversarial fact-checker (Anthropic
Claude) verifies every claim has supporting evidence.
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
st.title("AI Research Agent with Cross-Provider Fact-Checking")
st.caption(
    "Research any topic with real DuckDuckGo search, then verify every claim "
    "using a completely different AI provider — eliminating shared model biases."
)

# ─── Sidebar ────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Configuration")

    st.subheader("Research (OpenAI)")
    openai_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=os.environ.get("OPENAI_API_KEY", ""),
        help="Required for research planning and report synthesis.",
    )
    base_url = st.text_input(
        "OpenAI Base URL (optional)",
        value=os.environ.get("OPENAI_BASE_URL", ""),
        help="For alternate OpenAI-compatible providers.",
    )
    research_model = st.selectbox(
        "Research Model",
        ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1-nano"],
        index=0,
    )

    st.subheader("Fact-Check (Anthropic)")
    anthropic_key = st.text_input(
        "Anthropic API Key",
        type="password",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        help="Required for independent fact-checking. Different provider = different biases.",
    )
    factcheck_model = st.text_input(
        "Fact-Check Model",
        value="claude-sonnet-4-20250514",
        help="Anthropic model for adversarial verification.",
    )

    st.divider()
    threshold = st.slider(
        "Fact-check confidence threshold",
        min_value=0.0, max_value=1.0, value=0.75, step=0.05,
        help="Minimum confidence to mark research as verified.",
    )

    st.divider()
    st.caption(
        "**Why two providers?** The research model (OpenAI) and fact-checker "
        "(Anthropic) have different training data and biases. This means the "
        "fact-checker can catch errors the research model is blind to."
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

    both_keys = openai_key and anthropic_key
    if not both_keys:
        st.warning("Both OpenAI and Anthropic API keys are required.")

    if st.button("Research & Fact-Check", type="primary", disabled=not both_keys):
        if not topic.strip():
            st.warning("Enter a research topic.")
            st.stop()

        # Configure
        config = ra.Config(
            research_model=research_model,
            factcheck_model=factcheck_model,
            threshold=threshold,
        )
        os.environ["OPENAI_API_KEY"] = openai_key
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key
        if base_url:
            os.environ["OPENAI_BASE_URL"] = base_url

        from openai import OpenAI
        client = OpenAI(
            api_key=openai_key,
            base_url=base_url or None,
        )

        research_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO research VALUES (?,?,?,?,?,?,?,?,?,?)",
            (research_id, topic, "planning", None, None, None, None, None,
             ra.now(), None),
        )
        conn.commit()

        # ── Stage 1: Research Plan (OpenAI) ──
        with st.status("Planning research...", expanded=True) as status:
            plan = ra.plan_research(client, topic, config)
            status.update(label="Research plan ready", state="complete")

        st.markdown(f"**Refined topic:** {plan.get('topic_refined', topic)}")
        for sq in plan.get("search_queries", []):
            st.markdown(f"- {sq['query']}")

        # ── Stage 2: Gather Sources (DuckDuckGo + newspaper4k) ──
        with st.status("Searching DuckDuckGo & extracting content...", expanded=True) as status:
            conn.execute(
                "UPDATE research SET status='gathering' WHERE id=?",
                (research_id,),
            )
            conn.commit()
            sources = ra.gather_sources(conn, research_id, plan)

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

        # ── Stage 3: Synthesize Report (OpenAI) ──
        with st.status("Writing report (OpenAI)...", expanded=True) as status:
            conn.execute(
                "UPDATE research SET status='synthesizing' WHERE id=?",
                (research_id,),
            )
            conn.commit()
            report = ra.synthesize_report(
                client, plan.get("topic_refined", topic), sources, config
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

        # ── Stage 4: Cross-Provider Fact-Check (Anthropic Claude) ──
        with st.status(
            f"Fact-checking with {factcheck_model} (Anthropic)...", expanded=True
        ) as status:
            conn.execute(
                "UPDATE research SET status='fact_checking' WHERE id=?",
                (research_id,),
            )
            conn.commit()
            fc = ra.fact_check(topic, report, sources, config)

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

        st.info(
            f"**Research:** {research_model} (OpenAI) | "
            f"**Fact-check:** {factcheck_model} (Anthropic)"
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
