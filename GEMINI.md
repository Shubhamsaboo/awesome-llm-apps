# GEMINI.md — Starbucks China "Luckin-Counter" Agentic CRM Studio

## 1. Project Overview & Attribution
- **Application Name:** Starbucks China "Luckin-Counter" Agentic CRM Studio
- **Course / Context:** MKT 6013 CRM Project
- **Open-Source Base:** Adapted from `Shubhamsaboo/awesome-llm-apps/starter_ai_agents/multimodal_ai_agent` (Apache-2.0 License).
- **Mission:** Provide an agentic multimodal CRM studio that turns competitor short-form promos (or direct seasonal launches) into Starbucks China–compliant Douyin/Reels video scripts, shot-by-shot AIGC storyboards, Xiaohongshu (RedNote) seeding posts, and 3:4 cover visuals tailored by Starbucks Rewards RFM lifecycle segment and creator voice (Official / KOL / KOS / KOC).

---

## 2. Environment, SDK & Deployment Rules
- **OS / Shell:** Windows (PowerShell). Always use a local virtual environment (`.venv`) and invoke commands via `.venv\Scripts\python.exe`.
- **Deployment Target:** **Streamlit Community Cloud** — lightweight Python + Streamlit (`app.py`), zero external database, zero OAuth.
- **Dependencies (`requirements.txt`):**
  - `streamlit`
  - `google-genai`
  - `pillow`
  - `pydantic`
  - Deprecated libraries (`agno`, `phidata`, `duckduckgo-search`, `google-generativeai`) must NOT be used.
- **Official Gemini SDK:** Always use `from google import genai` and `from google.genai import types`.
- **API Key / Secrets Loading Order:**
  1. `st.secrets.get("GOOGLE_API_KEY")` (guarded safely if no `secrets.toml` exists)
  2. `os.getenv("GOOGLE_API_KEY")`
  3. Sidebar password input (`st.text_input(..., type="password")`) if neither is present.
  - **NEVER** overwrite, print, or commit `.streamlit/secrets.toml`.
- **Models (November 2026):**
  - **Default Multimodal / Text Model:** `gemini-4-hydrogen`
  - **Switchable Text / Multimodal Models (Sidebar Dropdown):** `gemini-4-hydrogen`, `gemini-3.8-flash`, `gemini-3.5-flash-lite`
  - **Xiaohongshu Cover Image Generation Model:** `gemini-nano-banana-2.1` (3:4 portrait aspect ratio) with automatic fallback to `gemini-3.1-flash-lite-image` if unavailable.
- **Video Upload Lifecycle:**
  1. Write uploaded `.mp4` or `.mov` bytes to a local temporary file.
  2. Upload to Gemini File API via `client.files.upload(file=temp_path)`.
  3. Poll `client.files.get(name=uploaded.name)` until `state.name == "ACTIVE"` (fail gracefully if `FAILED`).
  4. Pass the remote file reference alongside the structured prompt to `client.models.generate_content(...)`.
  5. Always delete both the remote Gemini file (`client.files.delete(...)`) and the local temp file (`Path(...).unlink(missing_ok=True)`) inside a `finally` block.

---

## 3. Architecture & File Layout
- `GEMINI.md` — Persistent project rules, model policies, CRM guardrails, and architecture reference.
- `requirements.txt` — Minimal dependencies for local Windows `.venv` and Streamlit Community Cloud.
- `starbucks_crm.py` — Domain knowledge base, RFM lifecycle segment definitions, Creator Voice Matrix, Pydantic structured output schema (`CampaignOutput`), and `build_campaign_prompt(...)` implementing the 5-step prompting framework.
- `app.py` — Starbucks-branded Streamlit application with dual input modes, CRM selectors, 3 structured output tabs, Xiaohongshu cover image generation, Prompt Inspector, and Apache-2.0 attribution footer.
- `README.md` — Setup, architecture, and clear separation between the `Shubhamsaboo/awesome-llm-apps` base and custom Starbucks CRM modules.
- `.streamlit/secrets.toml` — Local-only API credentials (git-ignored; never committed or overwritten).

---

## 4. Starbucks China CRM Domain Rules & Brand Guardrails

### A. Starbucks Rewards Lifecycle Segments (RFM Logic)
1. **Prospect / Welcome (Acquisition):** 0 orders or non-member. Emphasize signature coffee craft, aroma, and "Third Place" atmosphere; CTA drives Starbucks China App / WeChat Mini Program signup with a first-cup welcome perk.
2. **Green Star Member (Semi-Active / Frequency Push):** Visits every 3–6 months. Emphasize habit-building and seasonal limited-time urgency; CTA highlights Star-earning progress toward Gold tier and Mobile Order & Pay (`啡快`) convenience.
3. **At-Risk Gold Member (Switcher / Win-Back from Luckin):** 6–12 months since last visit, tempted by competitor RMB 9.9 coupons. Never mirror cheap price-war discounting; win back via high-perceived-value Gold exclusivity (barista customization, free upgrade/extra shot, double-Star comeback offer, or Starbucks Reserve experience).

### B. Creator Voice Matrix (Official / KOL / KOS / KOC)
- **Official Brand:** Polished, authoritative seasonal launch voice highlighting official store availability and brand heritage.
- **KOL (Lifestyle Influencer):** High-reach aesthetic hook, aspirational city/café lifestyle storytelling, top-of-funnel awareness.
- **KOS (Starbucks Barista / Store Partner):** Insider craft expertise, espresso/flavor notes, and "barista secret customization" tips (e.g., oat milk swap, less syrup, blonde espresso) driving store conversion.
- **KOC (Everyday Customer):** Relatable peer-to-peer review tone, office commute or afternoon pick-me-up vibe, authentic Xiaohongshu seeding style.

### C. Grounding Knowledge Base
- **Featured / Seasonal Drinks:** Toffee Nut Crunch Latte (太妃榛果拿铁), Peppermint Mocha (薄荷摩卡), Jolly Baked Apple Latte, Blonde Oat Latte, Seasonal Holiday Cold Brew, plus user custom drink input.
- **Anchor Pricing:** Tall Latte ~¥30, Grande ~¥33, Flat White ~¥35.
- **Channels & Loyalty:** Starbucks China App, WeChat Mini Program (`啡快` Mobile Order & Pay, `专星送` Star Delivery), Starbucks Rewards (Welcome / Green / Gold tiers).

### D. Strict Brand Guardrails
- **NO RMB 9.9 flash discounts:** Never recommend or copy RMB 9.9 price-war coupons.
- **NO competitor naming in consumer copy:** Never mention or attack Luckin Coffee by name in consumer-facing scripts, captions, titles, or hashtags (internal strategic teardown in Tab 1 may reference competitive positioning neutrally without leaking competitor names into consumer copy).
- **NO fabricated facts:** Never invent fake prices, fake promo codes, or unverified health/nutritional claims.

---

## 5. Prompting & Structured Output Standard
`build_campaign_prompt(...)` in `starbucks_crm.py` MUST assemble every prompt transparently using the 5-step prompting framework:
1. **1. Role**
2. **2. Context & Knowledge Base**
3. **3. Goal**
4. **4. Format & Style**
5. **5. Constraints**

All generation calls use Pydantic `response_schema` (`response_mime_type="application/json"`) so every UI tab renders deterministically without fragile markdown parsing.

---

## 6. UI / Visual Identity Guidelines
- **Brand Palette:** Starbucks Green `#00704A`, Dark Pine `#1E3932`, Warm Cream `#F9F6F1`, clean modern typography.
- **Sidebar:** Model selector, Output Language (`English`, `Chinese (简体中文)`, `Bilingual (EN + 中文)`), API key fallback input (when not in secrets/env), and expandable **Starbucks Knowledge Base Preview**.
- **Output Tabs:**
  - **Tab 1 — 30-Sec Douyin/Reels Video Script & Storyboard**
  - **Tab 2 — Xiaohongshu (RedNote) Post & Cover Visual** (with 3:4 image generation + Download PNG)
  - **Tab 3 — Prompt Inspector (Documentation)** (full assembled prompt + Download `.txt` + raw JSON expander)
