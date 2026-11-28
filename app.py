"""
Starbucks China "Luckin-Counter" Agentic CRM Studio (MKT 6013 CRM Project).

Refactored from Shubhamsaboo/awesome-llm-apps/starter_ai_agents/multimodal_ai_agent
(Apache-2.0 License) using the official `google-genai` SDK and Pydantic structured output.
"""

from __future__ import annotations

import base64
import csv
import html
import io
import json
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

from starbucks_crm import (
    CREATOR_VOICES,
    DEFAULT_TEXT_MODEL,
    DEMO_PRESETS,
    FALLBACK_IMAGE_MODEL,
    OUTPUT_LANGUAGES,
    PRIMARY_IMAGE_MODEL,
    REWARDS_SEGMENTS,
    STARBUCKS_KB,
    TEXT_MODELS,
    CampaignOutput,
    build_campaign_prompt,
    get_knowledge_base_preview_markdown,
)

# ---------------------------------------------------------------------------
# 1. Page Configuration, Asset Loader & Official Starbucks Web CSS
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title='Starbucks China "Luckin-Counter" Agentic CRM Studio',
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_html(markup: str) -> None:
    """Render HTML cleanly without indentation so Markdown never parses nested HTML as code blocks."""
    cleaned = "\n".join(line.strip() for line in markup.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_starbucks_logo_data_uri() -> str:
    """Load the local Starbucks Siren logo from assets/ as a base64 data URI."""
    logo_path = Path(__file__).resolve().parent / "assets" / "starbucks_logo.png"
    if logo_path.exists():
        b64 = base64.b64encode(logo_path.read_bytes()).decode("ascii")
        return f"data:image/png;base64,{b64}"
    # Fallback minimal circular green SVG if asset file is somehow missing
    fallback_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<circle cx="50" cy="50" r="48" fill="#00754A"/>'
        '<polygon points="50,18 57,38 78,38 61,50 67,70 50,58 33,70 39,50 22,38 43,38" fill="#FFFFFF"/>'
        "</svg>"
    )
    return "data:image/svg+xml;base64," + base64.b64encode(fallback_svg.encode("utf-8")).decode("ascii")


LOGO_DATA_URI = load_starbucks_logo_data_uri()

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
    --sbux-white: #FFFFFF;
    --sbux-house-green: #1E3932;
    --sbux-accent-green: #00754A;
    --sbux-accent-hover: #005C3A;
    --sbux-soft-mint: #D4E9E2;
    --sbux-warm-neutral: #F2F0EB;
    --sbux-charcoal: #212121;
    --sbux-muted: #55635E;
    --sbux-border: #E2DFD7;
    --rednote-coral: #FF2442;
}

html, body, .stApp {
    background-color: var(--sbux-white) !important;
    color: var(--sbux-charcoal) !important;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif !important;
    overflow-x: hidden;
}

.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp li, .stApp label, .stApp button, .stApp input, .stApp textarea {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}

/* Preserve Streamlit's Material Symbols icon font for sidebar toggle & expander arrows */
[data-testid="stIconMaterial"],
.material-symbols-rounded,
.material-icons {
    font-family: "Material Symbols Rounded" !important;
}

/* Hide Streamlit decoration bar, deploy toolbar & default footer while preserving sidebar toggle */
div[data-testid="stDecoration"],
div[data-testid="stAppDeployButton"],
#MainMenu {
    display: none !important;
}
footer {
    visibility: hidden !important;
    height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
}
header[data-testid="stHeader"] {
    background-color: transparent !important;
    height: 2.75rem !important;
    pointer-events: none;
}
header[data-testid="stHeader"] button,
header[data-testid="stHeader"] [data-testid="stExpandSidebarButton"],
header[data-testid="stHeader"] [data-testid="collapsedControl"] {
    pointer-events: auto !important;
}
div[data-testid="stSidebarCollapseButton"] {
    visibility: visible !important;
    opacity: 1 !important;
}

/* Main block container: wide padding + flush bottom for full-bleed footer */
section.main .block-container,
[data-testid="stMainBlockContainer"] {
    padding-top: 2.75rem !important;
    padding-bottom: 0 !important;
    padding-left: 3rem !important;
    padding-right: 3rem !important;
    max-width: 100% !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: var(--sbux-warm-neutral) !important;
    border-right: 1px solid var(--sbux-border) !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p {
    color: var(--sbux-house-green) !important;
}

/* Official Starbucks Top Navigation Bar */
.sbux-navbar {
    background-color: var(--sbux-white);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
    border-bottom: 1px solid #ECECE8;
    margin: 0 -3rem 1.75rem -3rem;
    padding: 0.95rem 3rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1.5rem;
    flex-wrap: wrap;
}
.sbux-nav-left {
    display: flex;
    align-items: center;
    gap: 2.1rem;
    flex-wrap: wrap;
}
.sbux-brand-group {
    display: flex;
    flex-direction: column;
    gap: 0.28rem;
}
.sbux-brand-title {
    font-size: 1.18rem;
    font-weight: 800;
    letter-spacing: 0.09em;
    color: var(--sbux-house-green);
    line-height: 1.1;
}
.sbux-brand-pill {
    display: inline-block;
    background-color: var(--sbux-soft-mint);
    color: var(--sbux-accent-green);
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    padding: 0.22rem 0.72rem;
    border-radius: 9999px;
    text-transform: uppercase;
    width: fit-content;
}
.sbux-nav-links {
    display: flex;
    align-items: center;
    gap: 1.65rem;
    flex-wrap: wrap;
}
.sbux-nav-links a {
    color: var(--sbux-charcoal) !important;
    text-decoration: none !important;
    font-size: 0.79rem;
    font-weight: 800;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    padding: 0.35rem 0;
    border-bottom: 2px solid transparent;
    transition: color 0.16s ease, border-color 0.16s ease;
}
.sbux-nav-links a:hover {
    color: var(--sbux-accent-green) !important;
    border-bottom-color: var(--sbux-accent-green);
}
.sbux-nav-right {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    margin-left: auto;
}
.sbux-nav-logo {
    width: 52px;
    height: 52px;
    display: block;
    border-radius: 50%;
    object-fit: cover;
}

/* Official Starbucks Editorial Hero Banner */
.sbux-hero {
    background-color: var(--sbux-house-green);
    color: var(--sbux-white);
    padding: 2rem 2.4rem;
    border-radius: 14px;
    margin-bottom: 1.75rem;
    position: relative;
    overflow: hidden;
    border-left: 6px solid var(--sbux-accent-green);
}
.sbux-hero-eyebrow {
    display: inline-block;
    background-color: rgba(212, 233, 226, 0.16);
    color: var(--sbux-soft-mint);
    font-size: 0.72rem;
    letter-spacing: 0.11em;
    text-transform: uppercase;
    font-weight: 700;
    padding: 0.26rem 0.75rem;
    border-radius: 9999px;
    margin-bottom: 0.75rem;
}
.sbux-hero h1 {
    color: var(--sbux-white) !important;
    font-size: 1.9rem;
    font-weight: 800;
    margin: 0 0 0.55rem 0;
    line-height: 1.2;
    letter-spacing: -0.015em;
}
.sbux-hero p {
    color: #E3EFEA;
    font-size: 0.96rem;
    margin: 0;
    max-width: 880px;
    line-height: 1.6;
}

/* Section Headers */
.sbux-section-heading {
    font-size: 1.08rem;
    font-weight: 800;
    color: var(--sbux-house-green);
    letter-spacing: 0.02em;
    margin: 1.25rem 0 0.6rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Starbucks Warm Neutral & Soft Mint Cards */
.sbux-card {
    background-color: var(--sbux-warm-neutral);
    border: 1px solid var(--sbux-border);
    border-left: 4px solid var(--sbux-accent-green);
    border-radius: 12px;
    padding: 1.25rem 1.4rem;
    margin-bottom: 1rem;
    color: var(--sbux-charcoal);
}
.sbux-card-pine {
    background-color: var(--sbux-warm-neutral);
    border: 1px solid var(--sbux-border);
    border-left: 4px solid var(--sbux-house-green);
    border-radius: 12px;
    padding: 1.25rem 1.4rem;
    margin-bottom: 1rem;
    color: var(--sbux-charcoal);
}
.sbux-card-mint {
    background-color: #F4FAF7;
    border: 1px solid var(--sbux-soft-mint);
    border-left: 4px solid var(--sbux-accent-green);
    border-radius: 12px;
    padding: 1.25rem 1.4rem;
    margin-bottom: 1rem;
    color: var(--sbux-charcoal);
}
.sbux-card-title {
    color: var(--sbux-house-green);
    font-weight: 800;
    font-size: 1.02rem;
    margin-bottom: 0.5rem;
}
.sbux-card code {
    background-color: #E5E1D8;
    color: var(--sbux-house-green);
    padding: 0.12rem 0.38rem;
    border-radius: 4px;
    font-size: 0.84em;
}
.sbux-badge {
    display: inline-block;
    background-color: var(--sbux-soft-mint);
    color: var(--sbux-house-green);
    font-size: 0.74rem;
    font-weight: 700;
    padding: 0.24rem 0.72rem;
    border-radius: 9999px;
    margin-right: 0.4rem;
    margin-bottom: 0.35rem;
}
.sbux-badge-neutral {
    display: inline-block;
    background-color: var(--sbux-warm-neutral);
    color: var(--sbux-house-green);
    border: 1px solid var(--sbux-border);
    font-size: 0.74rem;
    font-weight: 700;
    padding: 0.24rem 0.72rem;
    border-radius: 9999px;
    margin-right: 0.4rem;
    margin-bottom: 0.35rem;
}

/* Starbucks Pill Buttons: Primary (#00754A) & Secondary (Green-Outlined Pill) */
div.stButton > button[kind="primary"] {
    background-color: var(--sbux-accent-green) !important;
    color: var(--sbux-white) !important;
    border: 1.5px solid var(--sbux-accent-green) !important;
    border-radius: 9999px !important;
    font-weight: 700 !important;
    letter-spacing: 0.02em !important;
    padding: 0.68rem 1.6rem !important;
    box-shadow: 0 3px 10px rgba(0, 117, 74, 0.18) !important;
    transition: background-color 0.16s ease, border-color 0.16s ease, transform 0.1s ease !important;
}
div.stButton > button[kind="primary"]:hover {
    background-color: var(--sbux-accent-hover) !important;
    border-color: var(--sbux-accent-hover) !important;
}
div.stButton > button[kind="secondary"],
div.stDownloadButton > button {
    background-color: var(--sbux-white) !important;
    color: var(--sbux-accent-green) !important;
    border: 1.5px solid var(--sbux-accent-green) !important;
    border-radius: 9999px !important;
    font-weight: 700 !important;
    padding: 0.55rem 1.35rem !important;
    transition: background-color 0.16s ease, color 0.16s ease !important;
}
div.stButton > button[kind="secondary"]:hover,
div.stDownloadButton > button:hover {
    background-color: var(--sbux-soft-mint) !important;
    color: var(--sbux-house-green) !important;
    border-color: var(--sbux-accent-green) !important;
}

/* Output Tabs: Bold Uppercase + Solid #00754A Active Underline */
div[data-baseweb="tab-list"] {
    gap: 1.6rem !important;
    border-bottom: 1px solid #E5E5E0 !important;
}
button[data-baseweb="tab"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    color: #525B57 !important;
    padding: 0.7rem 0.2rem !important;
    background: transparent !important;
}
button[data-baseweb="tab"]:hover {
    color: var(--sbux-accent-green) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--sbux-house-green) !important;
    border-bottom: 3px solid var(--sbux-accent-green) !important;
}
div[data-baseweb="tab-highlight"] {
    background-color: var(--sbux-accent-green) !important;
    height: 3px !important;
}

/* RedNote Preview Card */
.rednote-card {
    background-color: var(--sbux-white);
    border: 1px solid var(--sbux-border);
    border-radius: 16px;
    padding: 1.45rem 1.6rem;
    box-shadow: 0 4px 16px rgba(30, 57, 50, 0.06);
}
.rednote-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid #EFECE6;
    padding-bottom: 0.75rem;
    margin-bottom: 0.95rem;
}
.rednote-pill {
    background-color: #FFF0F2;
    color: var(--rednote-coral);
    border: 1px solid #FFC9D0;
    font-size: 0.74rem;
    font-weight: 700;
    padding: 0.22rem 0.68rem;
    border-radius: 9999px;
}
.rednote-title {
    font-size: 1.2rem;
    font-weight: 800;
    color: var(--sbux-charcoal);
    line-height: 1.38;
    margin-bottom: 0.85rem;
}
.rednote-body {
    font-size: 0.95rem;
    color: #2B2F2D;
    line-height: 1.72;
    margin-bottom: 1rem;
}
.rednote-callout {
    background-color: var(--sbux-warm-neutral);
    border: 1px dashed var(--sbux-accent-green);
    border-radius: 10px;
    padding: 0.85rem 1rem;
    font-size: 0.9rem;
    color: var(--sbux-house-green);
    margin-bottom: 1rem;
}
.tag-chip-short {
    display: inline-block;
    background-color: var(--sbux-soft-mint);
    color: var(--sbux-house-green);
    border-radius: 9999px;
    padding: 0.24rem 0.72rem;
    font-size: 0.8rem;
    font-weight: 700;
    margin: 0.2rem 0.3rem 0.2rem 0;
}
.tag-chip-long {
    display: inline-block;
    background-color: var(--sbux-warm-neutral);
    color: var(--sbux-charcoal);
    border: 1px solid var(--sbux-border);
    border-radius: 9999px;
    padding: 0.24rem 0.72rem;
    font-size: 0.8rem;
    font-weight: 600;
    margin: 0.2rem 0.3rem 0.2rem 0;
}

/* Storyboard Table */
.sbux-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.88rem;
    background-color: var(--sbux-white);
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--sbux-border);
}
.sbux-table th {
    background-color: var(--sbux-house-green);
    color: var(--sbux-white);
    text-align: left;
    padding: 0.78rem 0.9rem;
    font-weight: 700;
    font-size: 0.8rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.sbux-table td {
    padding: 0.78rem 0.9rem;
    border-bottom: 1px solid #EFECE6;
    vertical-align: top;
    line-height: 1.55;
    color: var(--sbux-charcoal);
}
.sbux-table tr:nth-child(even) td {
    background-color: #FAF9F6;
}

/* MKT 6013 CRM Blueprint, Presets, GEO & Governance Gate */
.sbux-preset-bar-label {
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: var(--sbux-accent-green);
    margin: 0.1rem 0 0.5rem 0;
}
.sbux-blueprint-card {
    background-color: var(--sbux-warm-neutral);
    border: 1px solid var(--sbux-border);
    border-top: 4px solid var(--sbux-house-green);
    border-radius: 14px;
    padding: 1.3rem 1.45rem;
    margin: 0.85rem 0 1rem 0;
}
.sbux-blueprint-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin-bottom: 1rem;
}
.sbux-4p-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 0.8rem;
    margin-bottom: 1rem;
}
.sbux-4p-cell {
    background-color: var(--sbux-white);
    border: 1px solid var(--sbux-border);
    border-radius: 10px;
    padding: 0.85rem 0.95rem;
    font-size: 0.85rem;
    line-height: 1.5;
    color: var(--sbux-charcoal);
}
.sbux-4p-label {
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--sbux-accent-green);
    margin-bottom: 0.35rem;
}
.sbux-kpi-ab-grid {
    display: grid;
    grid-template-columns: 0.95fr 1.35fr;
    gap: 0.9rem;
}
.sbux-subpanel {
    background-color: var(--sbux-white);
    border: 1px solid var(--sbux-border);
    border-radius: 10px;
    padding: 0.9rem 1rem;
    font-size: 0.85rem;
    line-height: 1.55;
    color: var(--sbux-charcoal);
}
.sbux-wecom-box {
    background-color: #F4FAF7;
    border: 1px solid #C6E2D7;
    border-left: 4px solid var(--sbux-accent-green);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    font-size: 0.9rem;
    line-height: 1.65;
    color: var(--sbux-charcoal);
}
.sbux-geo-card {
    background-color: #F4FAF7;
    border: 1px solid #C6E2D7;
    border-left: 4px solid var(--sbux-house-green);
    border-radius: 12px;
    padding: 1.05rem 1.2rem;
    margin-top: 1rem;
    font-size: 0.87rem;
    line-height: 1.58;
    color: var(--sbux-charcoal);
}
.sbux-gov-header {
    background-color: var(--sbux-warm-neutral);
    border: 1px solid var(--sbux-border);
    border-left: 4px solid var(--sbux-house-green);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin: 1.5rem 0 0.85rem 0;
}
.sbux-status-queued {
    display: inline-block;
    background-color: var(--sbux-soft-mint);
    color: var(--sbux-house-green);
    font-size: 0.74rem;
    font-weight: 800;
    padding: 0.2rem 0.65rem;
    border-radius: 9999px;
    white-space: nowrap;
}
.sbux-status-revision {
    display: inline-block;
    background-color: #FDF1DF;
    color: #8A4F08;
    border: 1px solid #EBCBA0;
    font-size: 0.74rem;
    font-weight: 800;
    padding: 0.2rem 0.65rem;
    border-radius: 9999px;
    white-space: nowrap;
}

/* Official Starbucks Full-Width House Green Footer */
.sbux-official-footer {
    background-color: #1E3932;
    color: #FFFFFF;
    margin: 3.5rem -3rem 0 -3rem;
    padding: 3rem 2.75rem 2.6rem 2.75rem;
}
.sbux-footer-inner {
    max-width: 1280px;
    margin: 0 auto;
    display: flex;
    align-items: flex-start;
    gap: 3rem;
}
.sbux-footer-brand-col {
    flex: 0 0 auto;
    position: relative;
    padding-top: 0.15rem;
}
.sbux-footer-logo {
    width: 56px;
    height: 56px;
    display: block;
    border-radius: 50%;
    object-fit: cover;
}
.sbux-footer-tm {
    position: absolute;
    right: -6px;
    bottom: -2px;
    font-size: 8px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.75);
}
.sbux-footer-main {
    flex: 1 1 auto;
    min-width: 0;
}
.sbux-footer-cols {
    display: grid;
    grid-template-columns: minmax(225px, 245px) minmax(160px, 195px) minmax(160px, 195px);
    gap: 2rem;
}
.sbux-footer-col-title {
    color: #FFFFFF;
    font-size: 0.96rem;
    font-weight: 700;
    margin: 0 0 1.1rem 0;
}
.sbux-footer-links {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
}
.sbux-footer-links a {
    color: rgba(255, 255, 255, 0.82) !important;
    text-decoration: none !important;
    font-size: 0.84rem;
    font-weight: 400;
    display: inline-flex;
    align-items: center;
    gap: 0.36rem;
    white-space: nowrap;
    transition: color 0.15s ease;
}
.sbux-footer-links a:hover {
    color: #FFFFFF !important;
}
.sbux-footer-divider {
    border: 0;
    border-top: 1px solid rgba(255, 255, 255, 0.22);
    margin: 2rem 0 2.15rem 0;
}
.sbux-footer-bottom {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1.5rem;
    flex-wrap: wrap;
}
.sbux-footer-legal-side {
    flex: 1 1 440px;
}
.sbux-legal-links {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 1.05rem;
    margin-bottom: 1.55rem;
}
.sbux-legal-links a {
    color: rgba(255, 255, 255, 0.82) !important;
    text-decoration: none !important;
    font-size: 0.82rem;
    font-weight: 400;
    white-space: nowrap;
}
.sbux-legal-links a:hover {
    color: #FFFFFF !important;
}
.sbux-legal-links a.sbux-cookie-policy {
    color: #FFFFFF !important;
    font-weight: 700;
    text-decoration: underline !important;
    text-underline-offset: 3px;
}
.sbux-social-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.55rem;
}
.sbux-social-btn {
    width: 30px;
    height: 30px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    text-decoration: none !important;
    transition: opacity 0.15s ease, transform 0.15s ease;
}
.sbux-social-btn:hover {
    opacity: 0.85;
    transform: translateY(-1px);
}
.sbux-copyright {
    font-size: 0.82rem;
    color: rgba(255, 255, 255, 0.74);
    margin: 0;
}
.sbux-academic-note {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.55);
    margin: 0.45rem 0 0 0;
    line-height: 1.5;
}
.sbux-academic-note a {
    color: #D4E9E2 !important;
    text-decoration: underline !important;
    text-underline-offset: 2px;
}

/* App Promo Card (Right Side of Footer) */
.sbux-app-card {
    flex: 0 0 auto;
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 10px;
    padding: 20px 22px;
    background-color: rgba(255, 255, 255, 0.02);
    width: 382px;
    max-width: 100%;
}
.sbux-app-card-title {
    color: #FFFFFF;
    font-size: 0.91rem;
    font-weight: 700;
    margin: 0 0 0.45rem 0;
    line-height: 1.35;
    white-space: nowrap;
}
.sbux-app-card-sub {
    color: rgba(255, 255, 255, 0.78);
    font-size: 0.82rem;
    line-height: 1.5;
    margin: 0 0 1.2rem 0;
}
.sbux-store-badges {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: nowrap;
}
.sbux-store-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background-color: #000000;
    color: #FFFFFF !important;
    text-decoration: none !important;
    border: 1px solid rgba(255, 255, 255, 0.65);
    border-radius: 7px;
    padding: 7px 12px;
    min-width: 146px;
    transition: border-color 0.15s ease, transform 0.15s ease;
}
.sbux-store-badge:hover {
    border-color: #FFFFFF;
    transform: translateY(-1px);
}
.sbux-badge-text {
    display: flex;
    flex-direction: column;
    line-height: 1.12;
}
.sbux-badge-small {
    font-size: 9px;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.88);
    letter-spacing: 0.02em;
}
.sbux-badge-big {
    font-size: 14px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: -0.01em;
}

/* Remove extra spacing beneath the final footer markdown container */
div[data-testid="stElementContainer"]:has(.sbux-official-footer) {
    margin-bottom: 0 !important;
    padding-bottom: 0 !important;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 2. Helper Functions (Secrets, Gemini Text/Video & Image Generation)
# ---------------------------------------------------------------------------


def escape_br(text: str) -> str:
    """Safely HTML-escape text and preserve newlines."""
    return html.escape(text or "").replace("\n", "<br>")


def resolve_api_key() -> Tuple[Optional[str], str]:
    """
    Resolve GOOGLE_API_KEY in strict order:
      1. st.secrets.get("GOOGLE_API_KEY")
      2. os.getenv("GOOGLE_API_KEY")
      3. None (triggers sidebar password input)
    """
    try:
        secret_key = st.secrets.get("GOOGLE_API_KEY")
        if secret_key and str(secret_key).strip():
            return str(secret_key).strip(), "Streamlit secrets"
    except Exception:
        pass

    env_key = os.getenv("GOOGLE_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip(), "Environment variable"

    return None, "Not configured"


def get_genai_client(api_key: str) -> genai.Client:
    """Create a fresh official google-genai client."""
    return genai.Client(api_key=api_key)


def generate_crm_campaign(
    api_key: str,
    model_name: str,
    assembled_prompt: str,
    video_bytes: Optional[bytes] = None,
    video_filename: Optional[str] = None,
) -> Tuple[CampaignOutput, str]:
    """
    Run Gemini multimodal/text generation returning a validated CampaignOutput
    and raw JSON string. Handles video file upload, ACTIVE polling, and guaranteed cleanup.
    """
    client = get_genai_client(api_key)
    temp_video_path: Optional[Path] = None
    remote_gemini_file = None

    try:
        contents: list = []

        if video_bytes is not None:
            suffix = Path(video_filename or "competitor.mp4").suffix.lower()
            if suffix not in {".mp4", ".mov"}:
                suffix = ".mp4"

            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(video_bytes)
                temp_video_path = Path(tmp.name)

            remote_gemini_file = client.files.upload(file=str(temp_video_path))

            # Poll until Gemini finishes processing the uploaded video
            poll_deadline = time.time() + 180
            while True:
                file_info = client.files.get(name=remote_gemini_file.name)
                state_name = getattr(file_info.state, "name", str(file_info.state))
                if state_name == "ACTIVE":
                    remote_gemini_file = file_info
                    break
                if state_name == "FAILED":
                    raise RuntimeError("Gemini File API reported FAILED while processing the uploaded video.")
                if time.time() > poll_deadline:
                    raise TimeoutError("Timed out waiting for uploaded video to become ACTIVE on Gemini File API.")
                time.sleep(2)

            contents.append(remote_gemini_file)

        contents.append(assembled_prompt)

        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CampaignOutput,
                temperature=0.7,
            ),
        )

        # Prefer parsed Pydantic object if returned by SDK; fallback to text validation
        parsed_obj = getattr(response, "parsed", None)
        if isinstance(parsed_obj, CampaignOutput):
            campaign = parsed_obj
            raw_json = campaign.model_dump_json(indent=2)
        else:
            raw_text = (response.text or "").strip()
            if not raw_text:
                raise ValueError("Gemini returned an empty response.")
            campaign = CampaignOutput.model_validate_json(raw_text)
            raw_json = json.dumps(json.loads(raw_text), indent=2, ensure_ascii=False)

        return campaign, raw_json

    finally:
        if remote_gemini_file is not None:
            try:
                client.files.delete(name=remote_gemini_file.name)
            except Exception:
                pass
        if temp_video_path is not None:
            temp_video_path.unlink(missing_ok=True)


def _extract_image_bytes_from_response(response) -> Optional[bytes]:
    """Extract raw image bytes from a Gemini generate_content response."""
    parts = []
    if getattr(response, "candidates", None):
        for cand in response.candidates:
            content = getattr(cand, "content", None)
            if content and getattr(content, "parts", None):
                parts.extend(content.parts)
    elif getattr(response, "parts", None):
        parts.extend(response.parts)

    for part in parts:
        inline_data = getattr(part, "inline_data", None)
        if inline_data is not None:
            data = getattr(inline_data, "data", None)
            if isinstance(data, bytes) and len(data) > 0:
                return data
            if isinstance(data, str) and data:
                return base64.b64decode(data)
    return None


def generate_xiaohongshu_cover(api_key: str, image_prompt: str) -> Tuple[bytes, str, Optional[str]]:
    """
    Generate a 3:4 portrait Xiaohongshu cover visual using `gemini-nano-banana-2.1`,
    automatically falling back to `gemini-3.1-flash-lite-image` if unavailable.

    Returns: (png_bytes, model_used, fallback_warning_or_none)
    """
    client = get_genai_client(api_key)
    models_to_try = [PRIMARY_IMAGE_MODEL, FALLBACK_IMAGE_MODEL]
    errors: list[str] = []

    config_kwargs: dict = {"response_modalities": ["IMAGE"]}
    if hasattr(types, "ImageConfig"):
        config_kwargs["image_config"] = types.ImageConfig(aspect_ratio="3:4")

    full_prompt = (
        f"{image_prompt.strip()}\n\n"
        "Composition requirement: 3:4 vertical portrait framing ideal for a Xiaohongshu (RedNote) cover card, "
        "editorial café photography, warm natural light, authentic handcrafted coffee aesthetic, zero garbled text."
    )

    for idx, model_name in enumerate(models_to_try):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(**config_kwargs),
            )
            raw_bytes = _extract_image_bytes_from_response(response)
            if not raw_bytes:
                raise RuntimeError(f"Model `{model_name}` returned no image payload.")

            with Image.open(io.BytesIO(raw_bytes)) as img:
                png_buffer = io.BytesIO()
                img.convert("RGB").save(png_buffer, format="PNG")
                png_bytes = png_buffer.getvalue()

            fallback_note = None
            if idx > 0:
                fallback_note = (
                    f"Primary model `{PRIMARY_IMAGE_MODEL}` was unavailable; "
                    f"automatically fell back to `{model_name}`."
                )
            return png_bytes, model_name, fallback_note

        except Exception as exc:
            errors.append(f"{model_name}: {exc}")

    raise RuntimeError(
        "Image generation failed for both primary and fallback models.\n" + "\n".join(errors)
    )


@st.fragment
def render_cover_visual_studio(
    default_prompt: str, run_id: int, drink_label: str, active_api_key: Optional[str]
) -> None:
    """Isolated fragment for Xiaohongshu 3:4 cover generation so Tab 2 stays active on rerun."""
    st.markdown("#### 🎨 Xiaohongshu 3:4 Cover Visual Generator")
    st.caption(
        f"Powered by `{PRIMARY_IMAGE_MODEL}` (automatic fallback to `{FALLBACK_IMAGE_MODEL}`) in 3:4 portrait ratio."
    )

    edited_cover_prompt = st.text_area(
        "Editable Cover Image Prompt",
        value=default_prompt,
        height=165,
        key=f"cover_prompt_input_{run_id}",
    )

    if st.button(
        "🖼️ Generate Xiaohongshu Cover Image",
        type="primary",
        width="stretch",
        key=f"btn_generate_cover_{run_id}",
    ):
        if not active_api_key:
            st.error("Gemini API key is required to generate cover visuals.")
        elif not edited_cover_prompt.strip():
            st.warning("Please enter an image prompt first.")
        else:
            with st.spinner(f"Rendering 3:4 RedNote cover with `{PRIMARY_IMAGE_MODEL}`..."):
                try:
                    png_bytes, used_model, fallback_note = generate_xiaohongshu_cover(
                        api_key=active_api_key,
                        image_prompt=edited_cover_prompt,
                    )
                    st.session_state.cover_image_bytes = png_bytes
                    st.session_state.cover_image_model = used_model
                    st.session_state.cover_image_note = fallback_note
                except Exception as img_exc:
                    st.error(f"Cover image generation error: {img_exc}")

    if st.session_state.cover_image_note:
        st.info(st.session_state.cover_image_note)

    if st.session_state.cover_image_bytes:
        st.image(
            st.session_state.cover_image_bytes,
            caption=f"Generated 3:4 Xiaohongshu Cover • Model: {st.session_state.cover_image_model}",
            width="stretch",
        )
        safe_slug = (
            "".join(c if c.isalnum() else "_" for c in drink_label)
            .strip("_")
            .lower()[:40]
            or "starbucks_cover"
        )
        st.download_button(
            label="⬇️ Download PNG",
            data=st.session_state.cover_image_bytes,
            file_name=f"rednote_cover_{safe_slug}.png",
            mime="image/png",
            width="stretch",
        )
    else:
        render_html(
            """
            <div class="sbux-card" style="text-align:center; padding: 2rem 1.2rem; border: 1.5px dashed #00754A;">
                <div style="font-size: 2rem; margin-bottom: 0.4rem;">📸</div>
                <div style="font-weight: 800; color: #1E3932;">3:4 Portrait Cover Preview</div>
                <div style="font-size: 0.86rem; color: #55635E; margin-top: 0.25rem;">
                    Review or tweak the prompt above, then click <strong>Generate Xiaohongshu Cover Image</strong>.
                </div>
            </div>
            """
        )


def build_dispatch_csv_bytes(rows: list[dict[str, str]]) -> bytes:
    """Serialize CRM dispatch audit log rows to UTF-8 BOM CSV bytes."""
    fieldnames = [
        "Timestamp",
        "Drink",
        "RFM Segment",
        "Creator Voice",
        "Target Channels",
        "Guardrails",
        "Status",
        "Reviewer Note",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in fieldnames})
    return buf.getvalue().encode("utf-8-sig")


@st.fragment
def render_governance_gate(campaign: CampaignOutput, meta: dict, run_id: int) -> None:
    """Human-in-the-Loop Governance Gate & CRM Dispatch Audit Log isolated in a fragment."""
    render_html(
        """
        <div class="sbux-gov-header">
            <div class="sbux-card-title" style="margin-bottom: 0.25rem;">🛡️ Human-in-the-Loop Governance Gate &amp; CRM Dispatch</div>
            <div style="font-size: 0.86rem; color: #55635E;">
                Agentic safety checkpoint: review brand guardrails, 4Ps blueprint, and PIPL opt-in copy before queuing for Starbucks China CRM execution.
            </div>
        </div>
        """
    )

    reviewer_note = st.text_input(
        "Reviewer Comment / Revision Note (Optional)",
        placeholder="e.g., Approved for Shanghai Tier-1 WeCom opt-in pilot — or specify creative edits needed",
        key=f"gov_reviewer_note_{run_id}",
    )

    gc = campaign.guardrail_self_check
    passed_count = sum(
        [
            bool(gc.no_9_9_discount),
            bool(gc.no_competitor_named_in_consumer_copy),
            bool(gc.pricing_and_claims_grounded),
            bool(gc.wechat_pipl_opt_in_compliant),
        ]
    )
    guardrail_summary = f"{passed_count}/4 PASS"
    segment_key = meta.get("segment", "")
    target_channels = REWARDS_SEGMENTS.get(segment_key, {}).get(
        "primary_channels", "Starbucks China App, WeChat Mini Program (啡快)"
    )

    g_btn1, g_btn2 = st.columns(2, gap="medium")
    with g_btn1:
        approve_clicked = st.button(
            "✅ Approve & Dispatch to Starbucks CRM",
            type="primary",
            width="stretch",
            key=f"btn_gov_approve_{run_id}",
        )
    with g_btn2:
        reject_clicked = st.button(
            "🚩 Reject & Flag for Revision",
            type="secondary",
            width="stretch",
            key=f"btn_gov_reject_{run_id}",
        )

    if approve_clicked:
        st.session_state.crm_dispatch_log.insert(
            0,
            {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Drink": meta.get("drink", ""),
                "RFM Segment": segment_key,
                "Creator Voice": meta.get("voice", ""),
                "Target Channels": target_channels,
                "Guardrails": guardrail_summary,
                "Status": "Queued for Execution",
                "Reviewer Note": reviewer_note.strip() or "Approved for omnichannel CRM dispatch",
            },
        )
        st.success("Campaign approved and logged as **Queued for Execution** in the CRM Dispatch & Audit Log.")

    if reject_clicked:
        st.session_state.crm_dispatch_log.insert(
            0,
            {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Drink": meta.get("drink", ""),
                "RFM Segment": segment_key,
                "Creator Voice": meta.get("voice", ""),
                "Target Channels": target_channels,
                "Guardrails": guardrail_summary,
                "Status": "Revision Requested",
                "Reviewer Note": reviewer_note.strip() or "Flagged by reviewer for creative/compliance iteration",
            },
        )
        st.warning("Campaign flagged as **Revision Requested** in the CRM Dispatch & Audit Log.")

    if st.session_state.crm_dispatch_log:
        st.markdown("##### 📋 CRM Dispatch & Audit Log")
        log_rows_html = []
        for entry in st.session_state.crm_dispatch_log:
            status_cls = (
                "sbux-status-queued"
                if entry["Status"] == "Queued for Execution"
                else "sbux-status-revision"
            )
            log_rows_html.append(
                f"<tr>"
                f"<td style='white-space:nowrap; font-size:0.82rem;'>{html.escape(entry['Timestamp'])}</td>"
                f"<td><strong>{html.escape(entry['Drink'])}</strong></td>"
                f"<td>{html.escape(entry['RFM Segment'])}</td>"
                f"<td>{html.escape(entry['Creator Voice'])}</td>"
                f"<td style='font-size:0.82rem;'>{html.escape(entry['Target Channels'])}</td>"
                f"<td style='white-space:nowrap; font-weight:700; color:#00754A;'>{html.escape(entry['Guardrails'])}</td>"
                f"<td><span class='{status_cls}'>{html.escape(entry['Status'])}</span></td>"
                f"<td style='font-size:0.82rem;'>{html.escape(entry['Reviewer Note'])}</td>"
                f"</tr>"
            )
        render_html(
            f"""
            <table class="sbux-table">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Drink</th>
                        <th>RFM Segment</th>
                        <th>Creator Voice</th>
                        <th>Target Channels</th>
                        <th>Guardrails</th>
                        <th>Status</th>
                        <th>Reviewer Note</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(log_rows_html)}
                </tbody>
            </table>
            """
        )
        st.markdown("")
        st.download_button(
            label="⬇️ Download CRM Dispatch Log (.csv)",
            data=build_dispatch_csv_bytes(st.session_state.crm_dispatch_log),
            file_name="starbucks_crm_dispatch_log.csv",
            mime="text/csv",
            key=f"btn_download_dispatch_csv_{run_id}_{len(st.session_state.crm_dispatch_log)}",
        )


def apply_demo_preset(preset_id: str) -> None:
    """Pre-fill form controls via on_click callback before widget instantiation."""
    preset = DEMO_PRESETS[preset_id]
    st.session_state.ui_input_mode = preset["mode"]
    st.session_state.ui_direct_drink = preset["drink"]
    st.session_state.ui_direct_notes = preset["notes"]
    st.session_state.ui_segment = preset["segment"]
    st.session_state.ui_voice = preset["voice"]
    st.session_state.ui_language = preset["language"]
    st.session_state.active_preset_notice = preset["button_label"]


# ---------------------------------------------------------------------------
# 3. Session State Initialization
# ---------------------------------------------------------------------------

st.session_state.setdefault("campaign_result", None)
st.session_state.setdefault("campaign_raw_json", "")
st.session_state.setdefault("assembled_prompt", "")
st.session_state.setdefault("campaign_meta", {})
st.session_state.setdefault("campaign_run_id", 0)
st.session_state.setdefault("cover_image_bytes", None)
st.session_state.setdefault("cover_image_model", "")
st.session_state.setdefault("cover_image_note", None)
st.session_state.setdefault("crm_dispatch_log", [])
st.session_state.setdefault("active_preset_notice", None)

# Form control session defaults (enables instant one-click demo presets)
st.session_state.setdefault("ui_language", OUTPUT_LANGUAGES[0])
st.session_state.setdefault("ui_input_mode", "Mode 2 — Direct Seasonal Launch")
st.session_state.setdefault("ui_direct_drink", list(STARBUCKS_KB["featured_drinks"].keys())[0])
st.session_state.setdefault("ui_direct_notes", "")
st.session_state.setdefault("ui_segment", list(REWARDS_SEGMENTS.keys())[2])
st.session_state.setdefault("ui_voice", list(CREATOR_VOICES.keys())[2])


# ---------------------------------------------------------------------------
# 4. Sidebar Controls
# ---------------------------------------------------------------------------

resolved_key, key_source = resolve_api_key()

with st.sidebar:
    render_html(
        f"""
        <div style="display: flex; align-items: center; gap: 0.75rem; padding: 0.25rem 0 0.85rem 0; border-bottom: 2px solid #00754A; margin-bottom: 1rem;">
            <img src="{LOGO_DATA_URI}" alt="Starbucks Logo" style="width: 38px; height: 38px; border-radius: 50%; flex-shrink: 0;" />
            <div>
                <div style="font-size: 0.68rem; font-weight: 800; letter-spacing: 0.1em; color: #00754A; text-transform: uppercase;">
                    MKT 6013 CRM Studio
                </div>
                <div style="font-size: 1.08rem; font-weight: 800; color: #1E3932; line-height: 1.2;">
                    Studio Controls
                </div>
            </div>
        </div>
        """
    )

    if resolved_key:
        api_key = resolved_key
        st.success(f"Gemini API Key ready ({key_source})")
    else:
        api_key = st.text_input(
            "Enter GOOGLE_API_KEY",
            type="password",
            placeholder="AIza...",
            help="Loaded automatically from st.secrets or environment variable when available.",
        )
        st.caption("Obtain a key from [Google AI Studio](https://aistudio.google.com/apikey).")

    selected_model = st.selectbox(
        "Multimodal / Text Model",
        options=TEXT_MODELS,
        index=TEXT_MODELS.index(DEFAULT_TEXT_MODEL),
        help="Default: gemini-4-hydrogen (November 2026). Switch to lighter Flash tiers for rapid iteration.",
    )

    selected_language = st.selectbox(
        "Output Language",
        options=OUTPUT_LANGUAGES,
        key="ui_language",
        help="Controls language of strategic teardown, 4Ps blueprint, Douyin script, Xiaohongshu copy, GEO snippet, and WeCom push.",
    )

    st.caption(
        f"Cover Visual Engine: `{PRIMARY_IMAGE_MODEL}` "
        f"(auto-fallback: `{FALLBACK_IMAGE_MODEL}`)"
    )

    st.markdown("---")
    with st.expander("📚 Starbucks Knowledge Base Preview", expanded=False):
        st.markdown(get_knowledge_base_preview_markdown())


# ---------------------------------------------------------------------------
# 5. Official Starbucks Top Navigation Bar (Logo at Top Right) & Hero Banner
# ---------------------------------------------------------------------------

render_html(
    f"""
    <nav class="sbux-navbar" aria-label="Starbucks China CRM Studio Navigation">
        <div class="sbux-nav-left">
            <div class="sbux-brand-group">
                <div class="sbux-brand-title">STARBUCKS CHINA</div>
                <span class="sbux-brand-pill">AGENTIC CRM STUDIO • LUCKIN-COUNTER ENGINE</span>
            </div>
            <div class="sbux-nav-links">
                <a href="#campaign-generator">CAMPAIGN GENERATOR</a>
                <a href="#rewards-crm">REWARDS CRM</a>
                <a href="#prompt-inspector">PROMPT INSPECTOR</a>
            </div>
        </div>
        <div class="sbux-nav-right">
            <img src="{LOGO_DATA_URI}" alt="Starbucks Siren Logo" class="sbux-nav-logo" />
        </div>
    </nav>
    """
)

render_html(
    """
    <section class="sbux-hero" id="campaign-generator">
        <span class="sbux-hero-eyebrow">MKT 6013 CRM Project • Omnichannel Retention &amp; Seeding</span>
        <h1>Starbucks China "Luckin-Counter" Agentic CRM Studio</h1>
        <p>
            Transform competitor short-form promos or seasonal menu launches into RFM-segmented Douyin/Reels scripts,
            AIGC storyboards, Xiaohongshu (RedNote) seeding posts, and 3:4 portrait cover visuals — grounded strictly
            in Starbucks China coffee craft, Third Place warmth, and Rewards loyalty exclusivity.
        </p>
    </section>
    """
)

# ---------------------------------------------------------------------------
# 6. One-Click Demo Presets, Dual-Mode Controls & Rewards CRM Selectors
# ---------------------------------------------------------------------------

render_html('<div class="sbux-preset-bar-label">⚡ One-Click MKT 6013 Live Demo Presets</div>')
p_cols = st.columns(3, gap="small")
for p_col, (preset_id, preset_cfg) in zip(p_cols, DEMO_PRESETS.items()):
    with p_col:
        st.button(
            preset_cfg["button_label"],
            type="secondary",
            width="stretch",
            key=f"btn_{preset_id}",
            on_click=apply_demo_preset,
            args=(preset_id,),
        )

if st.session_state.active_preset_notice:
    st.info(
        f"Loaded **{st.session_state.active_preset_notice}** — controls & Bilingual output pre-filled. "
        "Click **Generate CRM Counter-Campaign** below."
    )

input_mode_label = st.radio(
    "Select Campaign Input Mode",
    options=[
        "Mode 1 — Competitor Video Counter-Strike",
        "Mode 2 — Direct Seasonal Launch",
    ],
    key="ui_input_mode",
    horizontal=True,
)
is_video_mode = input_mode_label.startswith("Mode 1")

uploaded_video = None
selected_drink: Optional[str] = None
campaign_notes: str = ""

with st.container():
    if is_video_mode:
        v_col1, v_col2 = st.columns([1.2, 1.0], gap="large")
        with v_col1:
            uploaded_video = st.file_uploader(
                "Upload Competitor Promo Clip (.mp4 / .mov)",
                type=["mp4", "mov"],
                help="Uploaded securely via Gemini File API, analyzed, and deleted immediately after generation.",
            )
            if uploaded_video is not None:
                st.video(uploaded_video)
        with v_col2:
            drink_choices = (
                ["Auto-Select Best Starbucks Counter Drink"]
                + list(STARBUCKS_KB["featured_drinks"].keys())
                + ["Custom Drink..."]
            )
            counter_drink_choice = st.selectbox(
                "Starbucks Counter Beverage (Optional)",
                options=drink_choices,
                index=0,
            )
            if counter_drink_choice == "Custom Drink...":
                selected_drink = st.text_input(
                    "Enter Custom Starbucks Drink Name",
                    placeholder="e.g., Brown Sugar Oat Shaken Espresso (红糖燕麦冰震浓缩)",
                )
            elif counter_drink_choice != "Auto-Select Best Starbucks Counter Drink":
                selected_drink = counter_drink_choice

            campaign_notes = st.text_area(
                "Optional Campaign Angle / Strategic Notes",
                placeholder="e.g., Counter a fast-paced ¥9.9 coupon video by spotlighting freshly pulled espresso aroma and Gold member bespoke customization.",
                height=115,
            )
    else:
        d_col1, d_col2 = st.columns([1.0, 1.2], gap="large")
        with d_col1:
            drink_options = list(STARBUCKS_KB["featured_drinks"].keys()) + ["Custom Drink..."]
            drink_choice = st.selectbox(
                "Featured / Seasonal Starbucks Drink",
                options=drink_options,
                key="ui_direct_drink",
            )
            if drink_choice == "Custom Drink...":
                selected_drink = st.text_input(
                    "Enter Custom Starbucks Drink Name",
                    placeholder="e.g., Pistachio Velvet Oat Latte (开心果丝绒燕麦拿铁)",
                )
            else:
                selected_drink = drink_choice
                drink_meta = STARBUCKS_KB["featured_drinks"][drink_choice]
                st.caption(f"**Flavor Profile:** {drink_meta['flavor_profile']}")
        with d_col2:
            campaign_notes = st.text_area(
                "Target Occasion / Campaign Notes (Optional)",
                placeholder="e.g., First chilly Monday morning of winter; highlight warm barista craft and effortless 啡快 pickup before the 9 AM standup.",
                height=115,
                key="ui_direct_notes",
            )

render_html('<div id="rewards-crm" class="sbux-section-heading">🎯 Rewards CRM Targeting &amp; Creator Voice</div>')
crm_col1, crm_col2 = st.columns(2, gap="large")

with crm_col1:
    selected_segment = st.selectbox(
        "Starbucks Rewards Lifecycle Segment (RFM)",
        options=list(REWARDS_SEGMENTS.keys()),
        key="ui_segment",
    )
    seg_info = REWARDS_SEGMENTS[selected_segment]
    st.caption(
        f"**RFM Logic:** {seg_info['rfm_logic']}  \n"
        f"**Focus:** {seg_info['strategic_focus']}  \n"
        f"**Target KPIs:** {seg_info['kpi_targets']}"
    )

with crm_col2:
    selected_voice = st.selectbox(
        "Creator Voice Matrix (Official / KOL / KOS / KOC)",
        options=list(CREATOR_VOICES.keys()),
        key="ui_voice",
    )
    voice_info = CREATOR_VOICES[selected_voice]
    st.caption(f"**Funnel Role:** {voice_info['funnel_role']}  \n**Voice:** {voice_info['tone_and_style']}")

generate_clicked = st.button(
    "✨ Generate CRM Counter-Campaign",
    type="primary",
    width="stretch",
)

# ---------------------------------------------------------------------------
# 7. Execute Campaign Generation
# ---------------------------------------------------------------------------

if generate_clicked:
    if not api_key:
        st.error("Please configure `GOOGLE_API_KEY` in `.streamlit/secrets.toml`, environment variables, or the sidebar input.")
    elif is_video_mode and uploaded_video is None:
        st.warning("Please upload a competitor `.mp4` or `.mov` clip in Mode 1, or switch to Mode 2 — Direct Seasonal Launch.")
    elif not is_video_mode and not (selected_drink and selected_drink.strip()):
        st.warning("Please select a featured drink or enter a custom Starbucks drink name.")
    else:
        assembled_prompt = build_campaign_prompt(
            mode="video" if is_video_mode else "direct",
            segment_key=selected_segment,
            voice_key=selected_voice,
            output_language=selected_language,
            drink_name=selected_drink.strip() if selected_drink else None,
            notes=campaign_notes,
            has_video=bool(is_video_mode and uploaded_video is not None),
        )

        spinner_msg = (
            f"Uploading competitor video to Gemini (`{selected_model}`) and crafting your counter-campaign..."
            if is_video_mode
            else f"Generating Starbucks China CRM campaign with `{selected_model}`..."
        )
        with st.spinner(spinner_msg):
            try:
                video_bytes = uploaded_video.getvalue() if (is_video_mode and uploaded_video) else None
                video_name = uploaded_video.name if (is_video_mode and uploaded_video) else None

                campaign_obj, raw_json = generate_crm_campaign(
                    api_key=api_key,
                    model_name=selected_model,
                    assembled_prompt=assembled_prompt,
                    video_bytes=video_bytes,
                    video_filename=video_name,
                )

                st.session_state.campaign_result = campaign_obj
                st.session_state.campaign_raw_json = raw_json
                st.session_state.assembled_prompt = assembled_prompt
                st.session_state.campaign_run_id += 1
                st.session_state.campaign_meta = {
                    "mode": input_mode_label,
                    "drink": selected_drink or "AI-Selected Counter Beverage",
                    "segment": selected_segment,
                    "voice": selected_voice,
                    "language": selected_language,
                    "model": selected_model,
                }
                st.session_state.cover_image_bytes = None
                st.session_state.cover_image_model = ""
                st.session_state.cover_image_note = None

                st.success(f"Campaign generated successfully: **{campaign_obj.campaign_title}**")
            except Exception as exc:
                st.error(f"Generation failed: {exc}")


# ---------------------------------------------------------------------------
# 8. Structured 3-Tab Output Rendering
# ---------------------------------------------------------------------------

render_html('<div id="prompt-inspector"></div>')

if st.session_state.campaign_result is not None:
    campaign: CampaignOutput = st.session_state.campaign_result
    meta = st.session_state.campaign_meta

    st.markdown("---")
    render_html(
        f"""
        <div style="margin-bottom: 0.7rem;">
            <span class="sbux-badge">☕ {html.escape(meta.get('drink', ''))}</span>
            <span class="sbux-badge">🎯 {html.escape(meta.get('segment', ''))}</span>
            <span class="sbux-badge-neutral">🎙️ {html.escape(meta.get('voice', ''))}</span>
            <span class="sbux-badge-neutral">🌐 {html.escape(meta.get('language', ''))}</span>
            <span class="sbux-badge">🤖 {html.escape(meta.get('model', ''))}</span>
        </div>
        <h3 style="color: #1E3932; margin: 0.25rem 0 0.75rem 0; font-weight: 800;">{html.escape(campaign.campaign_title)}</h3>
        """
    )

    # ---- CRM Blueprint (4Ps, KPIs & A/B Test) + WeCom 1-on-1 Push Preview ----
    bp = campaign.crm_blueprint
    kpis_html = "".join(
        f"<div style='margin-bottom:0.4rem;'><span class='sbux-badge'>📈 {html.escape(kpi)}</span></div>"
        for kpi in bp.primary_kpis
    )
    render_html(
        f"""
        <div class="sbux-blueprint-card">
            <div class="sbux-blueprint-head">
                <div class="sbux-card-title" style="margin: 0;">🧭 4Ps, KPIs &amp; A/B Test Blueprint</div>
                <span class="sbux-badge">📅 {html.escape(bp.campaign_period)}</span>
            </div>
            <div class="sbux-4p-grid">
                <div class="sbux-4p-cell">
                    <div class="sbux-4p-label">Product</div>
                    {escape_br(bp.four_ps.product)}
                </div>
                <div class="sbux-4p-cell">
                    <div class="sbux-4p-label">Price</div>
                    {escape_br(bp.four_ps.price)}
                </div>
                <div class="sbux-4p-cell">
                    <div class="sbux-4p-label">Promotion</div>
                    {escape_br(bp.four_ps.promotion)}
                </div>
                <div class="sbux-4p-cell">
                    <div class="sbux-4p-label">Place</div>
                    {escape_br(bp.four_ps.place)}
                </div>
            </div>
            <div class="sbux-kpi-ab-grid">
                <div class="sbux-subpanel">
                    <div class="sbux-4p-label">Primary Segment KPIs</div>
                    {kpis_html}
                </div>
                <div class="sbux-subpanel">
                    <div class="sbux-4p-label">A/B Creative Experiment</div>
                    <div><strong>Control Hook (A):</strong> {escape_br(bp.ab_test.control_hook)}</div>
                    <div style="margin-top:0.35rem;"><strong>Variant Hook (B):</strong> {escape_br(bp.ab_test.variant_hook)}</div>
                    <div style="margin-top:0.35rem;"><strong>Hypothesis:</strong> {escape_br(bp.ab_test.hypothesis)}</div>
                    <div style="margin-top:0.35rem; color:#00754A;"><strong>Success Metric:</strong> {escape_br(bp.ab_test.success_metric)}</div>
                </div>
            </div>
        </div>
        """
    )

    with st.expander("💬 1-on-1 WeCom / WeChat Mini Program Push Message Preview", expanded=False):
        render_html(
            f"""
            <div class="sbux-wecom-box">
                <div style="font-size:0.74rem; font-weight:800; letter-spacing:0.06em; text-transform:uppercase; color:#00754A; margin-bottom:0.45rem;">
                    Starbucks China WeCom • Opt-In Member Trigger ({html.escape(meta.get('segment', ''))})
                </div>
                <div>{escape_br(campaign.wecom_push_copy)}</div>
                <div style="margin-top:0.65rem; padding-top:0.5rem; border-top:1px dashed #B9DBCD; font-size:0.76rem; color:#55635E;">
                    🔒 PIPL Privacy Guardrail: Sent only to opted-in Starbucks Rewards members with separate location/personalization consent and 1-tap preference control.
                </div>
            </div>
            """
        )

    tab1, tab2, tab3 = st.tabs(
        [
            "DOUYIN/REELS SCRIPT & STORYBOARD",
            "XIAOHONGSHU POST & COVER",
            "PROMPT INSPECTOR",
        ]
    )

    # ---- TAB 1: Douyin/Reels Video Script & Storyboard ----
    with tab1:
        st.markdown("#### Tab 1 — 30-Sec Douyin/Reels Video Script & Storyboard")
        td = campaign.teardown
        render_html(
            f"""
            <div class="sbux-card-mint">
                <div class="sbux-card-title">📊 {html.escape(td.mode_label)} (Internal Strategy Brief)</div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 0.9rem; margin-top: 0.65rem;">
                    <div><strong>Hook Analysis:</strong><br>{escape_br(td.hook_analysis)}</div>
                    <div><strong>Pacing &amp; Visual Style:</strong><br>{escape_br(td.pacing_and_visual_style)}</div>
                    <div><strong>Offer &amp; Mechanic:</strong><br>{escape_br(td.offer_and_mechanic)}</div>
                    <div><strong>Strategic Weakness / Gap:</strong><br>{escape_br(td.strategic_weakness_or_gap)}</div>
                </div>
                <div style="margin-top: 0.9rem; padding-top: 0.75rem; border-top: 1px solid #C6E2D7;">
                    <strong>🌿 Starbucks China Counter-Angle:</strong> {escape_br(td.starbucks_counter_angle)}
                </div>
            </div>
            """
        )

        st.markdown("#### 🎞️ 30-Second Script Architecture")
        beats = [
            ("0–5s Hook", campaign.video_script.hook_0_5s, "sbux-card"),
            ("5–20s Craft & Proof", campaign.video_script.craft_proof_5_20s, "sbux-card-pine"),
            ("20–30s Segment-Specific CTA", campaign.video_script.cta_20_30s, "sbux-card"),
        ]
        b_cols = st.columns(3, gap="medium")
        for col, (label, beat, css_cls) in zip(b_cols, beats):
            with col:
                render_html(
                    f"""
                    <div class="{css_cls}" style="height: 100%;">
                        <div class="sbux-badge">{html.escape(beat.time_range or label)}</div>
                        <div class="sbux-card-title">{html.escape(label)} — {html.escape(beat.beat_title)}</div>
                        <p style="font-size: 0.88rem; margin-bottom: 0.55rem;">
                            <strong>Visual:</strong> {escape_br(beat.visual_direction)}
                        </p>
                        <p style="font-size: 0.88rem; margin-bottom: 0.55rem;">
                            <strong>Voiceover:</strong> {escape_br(beat.voiceover_or_dialogue)}
                        </p>
                        <p style="font-size: 0.86rem; margin-bottom: 0; color: #00754A;">
                            <strong>On-Screen Text:</strong> {escape_br(beat.on_screen_text)}
                        </p>
                    </div>
                    """
                )

        st.markdown("#### 🎥 Shot-by-Shot Storyboard & AIGC Video Prompts")
        rows_html = []
        for shot in campaign.video_script.storyboard:
            rows_html.append(
                f"<tr>"
                f"<td style='white-space:nowrap; font-weight:700; color:#00754A;'>{html.escape(shot.timestamp)}</td>"
                f"<td>{escape_br(shot.visual_camera_angle)}</td>"
                f"<td>{escape_br(shot.voiceover_text_overlay)}</td>"
                f"<td style='font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size:0.81rem;'>{escape_br(shot.aigc_video_prompt)}</td>"
                f"</tr>"
            )
        render_html(
            f"""
            <table class="sbux-table">
                <thead>
                    <tr>
                        <th style="width: 10%;">Timestamp</th>
                        <th style="width: 26%;">Visual / Camera Angle</th>
                        <th style="width: 28%;">Voiceover / Text Overlay</th>
                        <th style="width: 36%;">Copy-Paste AIGC Video Prompt</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows_html)}
                </tbody>
            </table>
            """
        )

        with st.expander("📋 One-Click Copy AIGC Video Prompts", expanded=False):
            for idx, shot in enumerate(campaign.video_script.storyboard, start=1):
                st.caption(f"Shot {idx} ({shot.timestamp})")
                st.code(shot.aigc_video_prompt, language="text")

    # ---- TAB 2: Xiaohongshu (RedNote) Post & Cover Visual ----
    with tab2:
        st.markdown("#### Tab 2 — Xiaohongshu (RedNote) Post & Cover Visual")
        xhs = campaign.xiaohongshu
        x_left, x_right = st.columns([1.15, 0.95], gap="large")

        with x_left:
            short_tags_html = "".join(
                f"<span class='tag-chip-short'>{html.escape('#' + tag.strip().lstrip('#'))}</span>"
                for tag in xhs.short_tail_hashtags
                if tag and tag.strip()
            )
            long_tags_html = "".join(
                f"<span class='tag-chip-long'>{html.escape('#' + tag.strip().lstrip('#'))}</span>"
                for tag in xhs.long_tail_hashtags
                if tag and tag.strip()
            )

            render_html(
                f"""
                <div class="rednote-card">
                    <div class="rednote-header">
                        <div>
                            <strong style="color:#1E3932;">{html.escape(meta.get('voice', 'Creator'))}</strong>
                            <div style="font-size:0.78rem; color:#55635E;">Starbucks China • Xiaohongshu Seeding Preview</div>
                        </div>
                        <span class="rednote-pill">小红书 RedNote</span>
                    </div>
                    <div class="rednote-title">{html.escape(xhs.title)}</div>
                    <div class="rednote-body">{escape_br(xhs.body_copy)}</div>
                    <div class="rednote-callout">
                        <strong>☕ Barista Formula / Rewards CTA:</strong><br>
                        {escape_br(xhs.ordering_or_rewards_callout)}
                    </div>
                    <div style="margin-bottom: 0.7rem;">
                        <div style="font-size: 0.78rem; font-weight: 800; color: #00754A; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.3rem;">
                            Short-Tail SEO Hashtags (High Volume)
                        </div>
                        {short_tags_html}
                    </div>
                    <div>
                        <div style="font-size: 0.78rem; font-weight: 800; color: #1E3932; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.3rem;">
                            Long-Tail SEO Hashtags (High Conversion Intent)
                        </div>
                        {long_tags_html}
                    </div>
                </div>
                """
            )

            geo = campaign.geo_snippet
            render_html(
                f"""
                <div class="sbux-geo-card">
                    <div style="font-size: 0.76rem; font-weight: 800; letter-spacing: 0.07em; text-transform: uppercase; color: #00754A; margin-bottom: 0.45rem;">
                        🤖 GEO (Generative Engine Optimization) Readiness
                    </div>
                    <div style="margin-bottom: 0.5rem;">
                        <strong>Target AI Query:</strong> “{html.escape(geo.target_ai_query)}”
                    </div>
                    <div>
                        <strong>Answer-First Citation Summary:</strong><br>
                        {escape_br(geo.answer_first_summary)}
                    </div>
                </div>
                """
            )

        with x_right:
            render_cover_visual_studio(
                default_prompt=xhs.cover_image_prompt,
                run_id=st.session_state.campaign_run_id,
                drink_label=meta.get("drink", "starbucks_cover"),
                active_api_key=api_key,
            )

    # ---- TAB 3: Prompt Inspector (Documentation) ----
    with tab3:
        st.markdown("#### Tab 3 — Prompt Inspector (Documentation)")
        gc = campaign.guardrail_self_check
        g_col1, g_col2, g_col3, g_col4 = st.columns(4)
        g_col1.metric("No RMB 9.9 Discounting", "PASS ✅" if gc.no_9_9_discount else "CHECK ⚠️")
        g_col2.metric(
            "Zero Competitor Naming",
            "PASS ✅" if gc.no_competitor_named_in_consumer_copy else "CHECK ⚠️",
        )
        g_col3.metric(
            "Grounded Pricing & Claims",
            "PASS ✅" if gc.pricing_and_claims_grounded else "CHECK ⚠️",
        )
        g_col4.metric(
            "WeChat / PIPL Opt-In",
            "PASS ✅" if gc.wechat_pipl_opt_in_compliant else "CHECK ⚠️",
        )
        st.caption(f"**Brand & Privacy Compliance Note:** {gc.compliance_note}")

        st.markdown("#### 🧾 Exact 5-Step Assembled Prompt Sent to Gemini")
        st.download_button(
            label="⬇️ Download Prompt (.txt)",
            data=st.session_state.assembled_prompt.encode("utf-8"),
            file_name="starbucks_crm_prompt.txt",
            mime="text/plain",
        )
        st.code(st.session_state.assembled_prompt, language="markdown")

        with st.expander("🗂️ Raw Structured JSON Output (Pydantic CampaignOutput)", expanded=False):
            try:
                st.json(json.loads(st.session_state.campaign_raw_json))
            except Exception:
                st.code(st.session_state.campaign_raw_json, language="json")

    # ---- Human-in-the-Loop Governance Gate & CRM Dispatch Log ----
    render_governance_gate(
        campaign=campaign,
        meta=meta,
        run_id=st.session_state.campaign_run_id,
    )
else:
    render_html(
        """
        <div class="sbux-card" style="margin-top: 0.9rem;">
            <div class="sbux-card-title">🚀 Ready to Build Your Starbucks China Counter-Campaign</div>
            <p style="margin: 0; font-size: 0.92rem; color: #364540; line-height: 1.6;">
                Choose <strong>Mode 1</strong> to upload a competitor promotional clip (<code>.mp4</code> / <code>.mov</code>)
                for multimodal viral teardown, or use <strong>Mode 2 — Direct Seasonal Launch</strong> to craft an RFM-segmented
                Douyin storyboard, Xiaohongshu seeding post, and 3:4 cover visual right away.
            </p>
        </div>
        """
    )


# ---------------------------------------------------------------------------
# 9. Official Full-Width Dark House Green (#1E3932) Starbucks Footer Banner
# ---------------------------------------------------------------------------

EXT_LINK_ICON = (
    '<svg width="12" height="12" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" '
    'style="opacity:0.78; flex-shrink:0;" aria-hidden="true">'
    '<path d="M9.5 2.5H13.5V6.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M13.5 2.5L7.5 8.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>'
    '<path d="M12.5 9.2V12.5C12.5 13.05 12.05 13.5 11.5 13.5H3.5C2.95 13.5 2.5 13.05 2.5 12.5V4.5C2.5 3.95 2.95 3.5 3.5 3.5H6.8" '
    'stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>'
    "</svg>"
)

FB_ICON = (
    '<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="Facebook">'
    '<circle cx="14" cy="14" r="14" fill="#FFFFFF"/>'
    '<path d="M15.65 22V14.7H18.1L18.47 11.85H15.65V10.03C15.65 9.21 15.88 8.65 17.06 8.65H18.57V6.11C18.31 6.07 17.41 6 16.37 6C14.19 6 12.7 7.33 12.7 9.77V11.85H10.25V14.7H12.7V22H15.65Z" fill="#1E3932"/>'
    "</svg>"
)

IG_ICON = (
    '<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="Instagram">'
    '<circle cx="14" cy="14" r="14" fill="#FFFFFF"/>'
    '<rect x="7.5" y="7.5" width="13" height="13" rx="3.8" stroke="#1E3932" stroke-width="1.8"/>'
    '<circle cx="14" cy="14" r="3.1" stroke="#1E3932" stroke-width="1.7"/>'
    '<circle cx="17.8" cy="10.2" r="1" fill="#1E3932"/>'
    "</svg>"
)

TIKTOK_ICON = (
    '<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="TikTok">'
    '<circle cx="14" cy="14" r="14" fill="#FFFFFF"/>'
    '<path d="M18.95 10.65C17.85 10.65 16.85 10.2 16.12 9.48C15.63 9 15.3 8.37 15.17 7.67H13.18V16.65C13.18 17.73 12.3 18.61 11.22 18.61C10.14 18.61 9.26 17.73 9.26 16.65C9.26 15.57 10.14 14.69 11.22 14.69C11.43 14.69 11.63 14.72 11.82 14.78V12.75C11.62 12.72 11.42 12.71 11.22 12.71C9.04 12.71 7.28 14.47 7.28 16.65C7.28 18.83 9.04 20.59 11.22 20.59C13.4 20.59 15.16 18.83 15.16 16.65V11.84C16.05 12.48 17.14 12.86 18.32 12.86H18.95V10.65Z" fill="#1E3932"/>'
    "</svg>"
)

APPLE_ICON = (
    '<svg width="20" height="24" viewBox="0 0 20 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    '<path d="M16.52 12.66C16.49 9.95 18.74 8.63 18.84 8.57C17.57 6.72 15.6 6.47 14.91 6.39C13.25 6.22 11.64 7.38 10.79 7.38C9.93 7.38 8.63 6.41 7.23 6.44C5.42 6.47 3.74 7.5 2.81 9.13C0.9 12.44 2.33 17.32 4.16 19.98C5.06 21.28 6.13 22.74 7.53 22.69C8.89 22.63 9.41 21.82 11.05 21.82C12.68 21.82 13.16 22.69 14.59 22.66C16.05 22.63 16.98 21.34 17.86 20.03C18.91 18.51 19.33 17.03 19.35 16.95C19.32 16.93 16.55 15.87 16.52 12.66ZM13.84 4.54C14.58 3.63 15.09 2.39 14.95 1.12C13.87 1.17 12.53 1.85 11.77 2.74C11.1 3.52 10.5 4.8 10.66 6.03C11.87 6.12 13.09 5.42 13.84 4.54Z" fill="#FFFFFF"/>'
    "</svg>"
)

GPLAY_ICON = (
    '<svg width="21" height="23" viewBox="0 0 24 26" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    '<path d="M1.4 0.8C1.15 1.07 1 1.5 1 2.05V23.95C1 24.5 1.15 24.93 1.4 25.2L1.5 25.28L13.75 13.03V12.97L1.5 0.72L1.4 0.8Z" fill="#4285F4"/>'
    '<path d="M17.83 17.12L13.75 13.03V12.97L17.83 8.88L17.93 8.94L22.76 11.69C24.14 12.47 24.14 13.75 22.76 14.53L17.93 17.28L17.83 17.12Z" fill="#FBBC05"/>'
    '<path d="M17.93 17.28L13.75 13L1.4 25.2C1.86 25.68 2.61 25.74 3.47 25.25L17.93 17.28Z" fill="#EA4335"/>'
    '<path d="M17.93 8.94L3.47 0.97C2.61 0.48 1.86 0.54 1.4 1.02L13.75 13L17.93 8.94Z" fill="#34A853"/>'
    "</svg>"
)

render_html(
    f"""
    <div class="sbux-official-footer" role="contentinfo">
        <div class="sbux-footer-inner">
            <div class="sbux-footer-brand-col">
                <img src="{LOGO_DATA_URI}" alt="Starbucks Siren Logo" class="sbux-footer-logo" />
                <span class="sbux-footer-tm">TM</span>
            </div>
            <div class="sbux-footer-main">
                <div class="sbux-footer-cols">
                    <div>
                        <div class="sbux-footer-col-title">About us</div>
                        <ul class="sbux-footer-links">
                            <li><a href="https://www.starbucks.com.cn/about/" target="_blank" rel="noopener">About us</a></li>
                            <li><a href="https://about.starbucks.com/" target="_blank" rel="noopener">Starbucks® for the Record {EXT_LINK_ICON}</a></li>
                            <li><a href="https://stories.starbucks.com/" target="_blank" rel="noopener">Starbucks® Stories &amp; News {EXT_LINK_ICON}</a></li>
                        </ul>
                    </div>
                    <div>
                        <div class="sbux-footer-col-title">Contact &amp; FAQ</div>
                        <ul class="sbux-footer-links">
                            <li><a href="https://www.starbucks.com.cn/help/" target="_blank" rel="noopener">FAQ</a></li>
                            <li><a href="https://www.starbucks.com.cn/about/contact/" target="_blank" rel="noopener">Contact Us</a></li>
                            <li><a href="https://www.starbucks.com/about-us/accessibility/" target="_blank" rel="noopener">Accessibility</a></li>
                        </ul>
                    </div>
                    <div>
                        <div class="sbux-footer-col-title">Careers</div>
                        <ul class="sbux-footer-links">
                            <li><a href="https://careers.starbucks.com/" target="_blank" rel="noopener">Search Careers {EXT_LINK_ICON}</a></li>
                        </ul>
                    </div>
                </div>
                <hr class="sbux-footer-divider" />
                <div class="sbux-footer-bottom">
                    <div class="sbux-footer-legal-side">
                        <div class="sbux-legal-links">
                            <a href="https://www.starbucks.com/terms/starbucks-terms-of-use/" target="_blank" rel="noopener">Legal information</a>
                            <a href="https://www.starbucks.com/terms/privacy-policy/" target="_blank" rel="noopener">Privacy Policy</a>
                            <a href="https://www.starbucks.com/terms/starbucks-terms-of-use/" target="_blank" rel="noopener">Terms of Use</a>
                            <a href="https://www.starbucks.com/terms/privacy-policy/#cookies" target="_blank" rel="noopener">Cookie Notice</a>
                            <a href="https://www.starbucks.com/terms/privacy-policy/#cookies" target="_blank" rel="noopener" class="sbux-cookie-policy">Cookie Policy</a>
                        </div>
                        <div class="sbux-social-row">
                            <a href="https://www.facebook.com/Starbucks" target="_blank" rel="noopener" class="sbux-social-btn" aria-label="Facebook">{FB_ICON}</a>
                            <a href="https://www.instagram.com/starbucks" target="_blank" rel="noopener" class="sbux-social-btn" aria-label="Instagram">{IG_ICON}</a>
                            <a href="https://www.tiktok.com/@starbucks" target="_blank" rel="noopener" class="sbux-social-btn" aria-label="TikTok">{TIKTOK_ICON}</a>
                        </div>
                        <p class="sbux-copyright">© 2026 Starbucks Corporation.</p>
                        <p class="sbux-academic-note">MKT 6013 Academic CRM Prototype • Adapted from <a href="https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/starter_ai_agents/multimodal_ai_agent" target="_blank" rel="noopener">Shubhamsaboo/awesome-llm-apps</a> (Apache-2.0 License).</p>
                    </div>
                    <div class="sbux-app-card">
                        <div class="sbux-app-card-title">Start ordering ahead with the Starbucks® app</div>
                        <div class="sbux-app-card-sub">Order and pay — then breeze in to pick up your drink at your selected store.</div>
                        <div class="sbux-store-badges">
                            <a href="https://apps.apple.com/app/starbucks/id331177714" target="_blank" rel="noopener" class="sbux-store-badge">
                                {APPLE_ICON}
                                <span class="sbux-badge-text">
                                    <span class="sbux-badge-small">Download on the</span>
                                    <span class="sbux-badge-big">App Store</span>
                                </span>
                            </a>
                            <a href="https://play.google.com/store/apps/details?id=com.starbucks.mobilecard" target="_blank" rel="noopener" class="sbux-store-badge">
                                {GPLAY_ICON}
                                <span class="sbux-badge-text">
                                    <span class="sbux-badge-small">GET IT ON</span>
                                    <span class="sbux-badge-big">Google Play</span>
                                </span>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
)
