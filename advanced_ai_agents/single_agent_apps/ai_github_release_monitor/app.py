"""
AI GitHub Release Monitor — Streamlit Web Interface
====================================================
A visual interface for monitoring GitHub releases with AI-powered analysis.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import json
import os

import streamlit as st

from release_monitor import (
    add_repo,
    check_releases,
    get_db,
    get_rate_limit,
    load_watchlist,
    remove_repo,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="AI GitHub Release Monitor", page_icon="\U0001f680", layout="wide")

# ---------------------------------------------------------------------------
# Sidebar — configuration
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("\U0001f680 Release Monitor")
    st.markdown("---")

    # API Keys
    st.subheader("Configuration")
    anthropic_key = st.text_input(
        "Anthropic API Key",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        type="password",
        help="Required for AI analysis. Get one at console.anthropic.com",
    )
    github_token = st.text_input(
        "GitHub Token (optional)",
        value=os.environ.get("GITHUB_TOKEN", ""),
        type="password",
        help="Raises API rate limit from 60 to 5000 requests/hour",
    )
    model = st.selectbox(
        "Claude Model",
        ["claude-sonnet-4-20250514", "claude-haiku-4-20250514", "claude-opus-4-20250514"],
        help="Model for release analysis",
    )

    # Set env vars for the session
    if anthropic_key:
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key
    if github_token:
        os.environ["GITHUB_TOKEN"] = github_token

    st.markdown("---")

    # Watchlist management
    st.subheader("Watchlist")
    repos = load_watchlist()

    # Add repo
    col1, col2 = st.columns([3, 1])
    with col1:
        new_repo = st.text_input("Add repository", placeholder="owner/repo", label_visibility="collapsed")
    with col2:
        if st.button("Add", use_container_width=True):
            if new_repo and "/" in new_repo:
                if add_repo(new_repo):
                    st.rerun()
            else:
                st.error("Use owner/repo format")

    # Preset suggestions
    with st.expander("Popular repos"):
        presets = [
            "anthropics/anthropic-sdk-python",
            "langchain-ai/langchain",
            "pydantic/pydantic",
            "openai/openai-python",
            "fastapi/fastapi",
            "astral-sh/ruff",
            "pallets/flask",
        ]
        for preset in presets:
            if preset not in repos:
                if st.button(f"+ {preset}", key=f"preset_{preset}"):
                    add_repo(preset)
                    st.rerun()

    # Current watchlist
    if repos:
        st.markdown(f"**Watching {len(repos)} repos:**")
        for repo in repos:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"`{repo}`")
            with col2:
                if st.button("\u2715", key=f"rm_{repo}", help=f"Remove {repo}"):
                    remove_repo(repo)
                    st.rerun()
    else:
        st.info("No repos in watchlist. Add some above!")

    # Rate limit display
    st.markdown("---")
    rate = get_rate_limit()
    if rate:
        remaining_pct = rate["remaining"] / rate["limit"] * 100
        color = "green" if remaining_pct > 50 else "orange" if remaining_pct > 10 else "red"
        st.markdown(f"GitHub API: :{color}[{rate['remaining']}/{rate['limit']}] remaining")
    elif not github_token:
        st.caption("Set GitHub token for rate limit info")

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

tab_monitor, tab_history = st.tabs(["\U0001f4e1 Monitor", "\U0001f4dc History"])

# ---------------------------------------------------------------------------
# Monitor tab
# ---------------------------------------------------------------------------

with tab_monitor:
    st.header("Check for New Releases")

    if not anthropic_key:
        st.warning("Set your Anthropic API key in the sidebar to enable AI analysis.")
    elif not repos:
        st.info("Add repositories to your watchlist in the sidebar to get started.")
    else:
        col1, col2 = st.columns([1, 4])
        with col1:
            check_button = st.button("\U0001f50d Check Now", type="primary", use_container_width=True)

        if check_button:
            try:
                import anthropic

                client = anthropic.Anthropic(api_key=anthropic_key)
            except ImportError:
                st.error("anthropic package not installed. Run: pip install anthropic")
                st.stop()

            conn = get_db()
            progress_container = st.container()
            results_container = st.container()

            with progress_container:
                status = st.status("Checking releases...", expanded=True)
                progress_messages = []

                def streamlit_callback(event: str, detail: str) -> None:
                    if event == "checking":
                        status.update(label=f"Checking {detail}...")
                        st.write(f"\U0001f50e Fetching releases from `{detail}`")
                    elif event == "analyzing":
                        st.write(f"\U0001f9e0 Analyzing `{detail}`")
                    elif event == "up_to_date":
                        st.write(f"\u2705 `{detail}` — up to date")
                    elif event == "done":
                        st.write(f"\u2728 `{detail}` — done")

                results = check_releases(client, conn, model=model, callback=streamlit_callback)
                status.update(label="Done!", state="complete")

            with results_container:
                if not results:
                    st.success("All watched repositories are up to date!")
                else:
                    st.subheader(f"Found {len(results)} new release(s)")

                    for item in results:
                        analysis = item["analysis"]
                        urgency = analysis.get("upgrade_urgency", "routine")
                        score = analysis.get("impact_score", 0.0)
                        categories = analysis.get("categories", [])

                        # Color-coded impact badge
                        if score >= 0.8:
                            badge_color = "red"
                        elif score >= 0.5:
                            badge_color = "orange"
                        else:
                            badge_color = "green"

                        # Release card
                        with st.expander(
                            f"{'🔴' if score >= 0.8 else '🟡' if score >= 0.5 else '🟢'} "
                            f"**{item['repo']}** @ `{item['tag']}` — "
                            f"Impact: {score:.1f} | {urgency.upper()}",
                            expanded=(score >= 0.5),
                        ):
                            # Summary
                            st.markdown(f"**Summary:** {analysis.get('summary', 'N/A')}")

                            # Categories as tags
                            if categories:
                                st.markdown("**Categories:** " + " ".join(f"`{c}`" for c in categories))

                            # Breaking changes
                            breaking = analysis.get("breaking_changes", [])
                            if breaking:
                                st.markdown("---")
                                st.markdown(f"\u26a0\ufe0f **Breaking Changes ({len(breaking)})**")
                                for bc in breaking:
                                    st.markdown(f"- {bc.get('description', '')}")
                                    if bc.get("migration"):
                                        st.markdown(f"  - *Migration:* {bc['migration']}")

                            # Security fixes
                            security = analysis.get("security_fixes", [])
                            if security:
                                st.markdown("---")
                                st.markdown(f"\U0001f6e1\ufe0f **Security Fixes ({len(security)})**")
                                for sf in security:
                                    sev = sf.get("severity", "unknown")
                                    st.markdown(f"- **[{sev.upper()}]** {sf.get('description', '')}")

                            # Deprecations
                            deprecations = analysis.get("deprecations", [])
                            if deprecations:
                                st.markdown("---")
                                st.markdown(f"\u23f3 **Deprecations ({len(deprecations)})**")
                                for dep in deprecations:
                                    st.markdown(f"- {dep.get('what', '')}")
                                    if dep.get("replacement"):
                                        st.markdown(f"  - *Use instead:* `{dep['replacement']}`")

                            # Highlights
                            highlights = analysis.get("highlights", [])
                            if highlights:
                                st.markdown("---")
                                st.markdown("\u2728 **Highlights**")
                                for h in highlights:
                                    st.markdown(f"- {h}")

                            # Upgrade notes
                            notes = analysis.get("upgrade_notes")
                            if notes:
                                st.markdown("---")
                                st.info(f"\U0001f4cb **Upgrade Notes:** {notes}")

                            # Raw JSON
                            with st.expander("Raw analysis JSON"):
                                st.json(analysis)

            conn.close()

# ---------------------------------------------------------------------------
# History tab
# ---------------------------------------------------------------------------

with tab_history:
    st.header("Analysis History")

    conn = get_db()
    rows = conn.execute(
        "SELECT id, repo, tag_name, impact_score, categories, created_at "
        "FROM analyses ORDER BY created_at DESC LIMIT 50"
    ).fetchall()

    if not rows:
        st.info("No analyses yet. Use the Monitor tab to check for releases.")
    else:
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            all_repos = sorted(set(r["repo"] for r in rows))
            filter_repo = st.selectbox("Filter by repository", ["All"] + all_repos)
        with col2:
            all_cats = set()
            for r in rows:
                if r["categories"]:
                    all_cats.update(r["categories"].split(","))
            filter_cat = st.selectbox("Filter by category", ["All"] + sorted(all_cats))

        # Apply filters
        filtered = rows
        if filter_repo != "All":
            filtered = [r for r in filtered if r["repo"] == filter_repo]
        if filter_cat != "All":
            filtered = [r for r in filtered if filter_cat in (r["categories"] or "")]

        # Display as table
        if filtered:
            table_data = []
            for r in filtered:
                score = r["impact_score"] or 0.0
                table_data.append(
                    {
                        "ID": r["id"],
                        "Repository": r["repo"],
                        "Tag": r["tag_name"],
                        "Impact": f"{score:.1f}",
                        "Categories": r["categories"] or "",
                        "Analyzed": r["created_at"][:16],
                    }
                )
            st.dataframe(table_data, use_container_width=True, hide_index=True)

            # Detail viewer
            selected_id = st.text_input("View details (enter ID prefix):")
            if selected_id:
                row = conn.execute(
                    "SELECT * FROM analyses WHERE id LIKE ?", (f"{selected_id}%",)
                ).fetchone()
                if row:
                    analysis = json.loads(row["analysis_json"])
                    st.subheader(f"{row['repo']} @ {row['tag_name']}")
                    st.json(analysis)
                else:
                    st.warning(f"No analysis found for ID: {selected_id}")
        else:
            st.info("No results match the selected filters.")

    conn.close()
