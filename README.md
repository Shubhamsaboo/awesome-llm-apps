# ☕ Starbucks China "Luckin-Counter" Agentic CRM Studio

An interactive, lightweight Streamlit studio built for our **MKT 6013 CRM Project** to turn competitor short-form coffee promos—or direct seasonal beverage launches—into Starbucks China–compliant omnichannel CRM campaigns across **Douyin / Reels**, **Xiaohongshu (RedNote)**, **WeChat Mini Program**, and **WeCom**.

---

## Open-Source Attribution vs. Custom MKT 6013 CRM Modules

This project maintains transparent provenance between the open-source starter template and our custom CRM architecture:

### 1. Open-Source Base (Apache-2.0 License)
- **Source:** [`Shubhamsaboo/awesome-llm-apps`](https://github.com/Shubhamsaboo/awesome-llm-apps) — specifically [`starter_ai_agents/multimodal_ai_agent`](https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/starter_ai_agents/multimodal_ai_agent) (`LICENSE` included in root).
- **Inherited Pattern:** Lightweight single-repo Streamlit UI pattern for uploading `.mp4`/`.mov` videos, processing multimodal inputs with Google Gemini, and rendering results cleanly without an external database or OAuth layer.
- Unused root starter copies (`multimodal_agent.py`, `multimodal_reasoning_agent.py`) were removed after refactoring into `app.py` and `starbucks_crm.py` so the repository stays clean for Streamlit Community Cloud.

### 2. Custom Starbucks China CRM Studio Modules (MKT 6013)
- **`GEMINI.md`**: Project rules, November 2026 Gemini model policy, SDK standards, and brand guardrails.
- **`starbucks_crm.py`**:
  - **2026 Starbucks China Grounding Knowledge Base**: ~8,000+ Starbucks China stores (operating under the April 2026 Boyu Capital joint venture) defending premium positioning against Luckin Coffee (~38,900 stores), featured seasonal drinks, pastry/food cross-sell pairings (Almond Croissant, Cranberry Scone, Holiday Chestnut Cake, Smoked Chicken & Cheese Panini), anchor pricing (`Tall ~¥30`, `Grande ~¥33`, `Flat White ~¥35`), official WeChat Mini Program channels (`Starbucks Now 啡快`, `Starbucks Delivers 专星送`, `Online Coffee Mall`), and China PIPL / WeChat Opt-In Privacy guardrails.
  - **Starbucks Rewards RFM Lifecycle Segments & KPIs**:
    - *Prospect / Welcome (Acquisition)* → CPA, ROAS, Mini Program Sign-Up Conversion Rate
    - *Green Star Member (Semi-Active / Frequency Push)* → AOV, Food/Pastry Attach Rate, Repeat Visit Frequency
    - *At-Risk Gold Member (Switcher / Win-Back from Luckin)* → Win-Back Rate, CLV, NPS
  - **Creator Voice Matrix**: Official Brand, KOL (Lifestyle Influencer), KOS (Starbucks Barista / Store Partner), and KOC (Everyday Customer).
  - **4Ps, KPIs & A/B Test Design (`CRMBlueprint`)**: Explicit Product, Price, Promotion, Place mix, recommended campaign burst window, 3 segment-matched KPIs, and Control vs. Variant A/B creative hypothesis & success metric.
  - **GEO (Generative Engine Optimization) Readiness (`GEOSnippet`)**: Consumer AI query + fact-dense answer-first summary structured for AI search citation.
  - **1-on-1 WeCom / Mini Program Push Copy**: Non-spammy, PIPL opt-in personalized member trigger message.
  - **5-Step Prompting Framework (`build_campaign_prompt`)** & **Pydantic Structured Output Schema (`CampaignOutput`)**: Guarantees deterministic JSON rendering across all UI components.
- **`app.py` & `assets/starbucks_logo.png`**:
  - Migrated to the official **`google-genai`** SDK (`from google import genai`, `from google.genai import types`), removing deprecated libraries (`agno`, `phidata`, `duckduckgo-search`, `google-generativeai`).
  - Official Starbucks web visual language (`Plus Jakarta Sans`, `#FFFFFF` / `#1E3932` / `#00754A` / `#D4E9E2` / `#F2F0EB` palette, pill buttons, base64-embedded Siren logo, top navigation bar, and full-width `#1E3932` House Green footer banner).
  - **One-Click Demo Presets**: Instant pre-filled Bilingual setups for Prospect Acquisition (KOL), Green Star Cross-Sell (KOS), and At-Risk Gold Win-Back (KOC).
  - Safe Gemini File API video upload lifecycle (`client.files.upload` → poll `ACTIVE` → `generate_content` → guaranteed remote + local cleanup in `finally`).
  - **3 Structured Output Tabs + CRM Blueprint + Governance Gate**:
    - Above tabs: Warm Neutral **4Ps, KPIs & A/B Test Blueprint** card + expandable **WeCom 1-on-1 Push Preview**.
    - **Tab 1:** Teardown/Market Opportunity card, 30-sec Douyin/Reels script (`0–5s`, `5–20s`, `20–30s`), and shot-by-shot AIGC storyboard.
    - **Tab 2:** RedNote preview card (Short-Tail vs. Long-Tail SEO hashtags), **GEO Readiness** card, and `@st.fragment`-isolated 3:4 Cover Visual Generator (`gemini-nano-banana-2.1` + automatic `gemini-3.1-flash-lite-image` fallback) + PNG download.
    - **Tab 3:** 4 automated compliance badges (including **WeChat / PIPL Opt-In Compliance**), exact 5-step Prompt Inspector (`.txt` download), and raw Pydantic JSON viewer.
    - Below tabs: **Human-in-the-Loop Governance Gate** (`Approve & Dispatch to Starbucks CRM` / `Reject & Flag for Revision`) with an auditable **CRM Dispatch & Audit Log** and **`.csv` export**.

---

## Models Used (November 2026)

- **Default Multimodal / Text Model:** `gemini-4-hydrogen` (sidebar switchable to `gemini-3.8-flash` and `gemini-3.5-flash-lite`)
- **Xiaohongshu 3:4 Cover Visual Model:** `gemini-nano-banana-2.1` (automatic fallback to `gemini-3.1-flash-lite-image`)

---

## Quick Start (Windows PowerShell)

1. **Create and activate a local virtual environment (`.venv`):**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install --upgrade pip
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

2. **Configure your Gemini API key (choose one):**
   - **Recommended (Local / Streamlit Cloud):** Add `GOOGLE_API_KEY = "your_key_here"` inside `.streamlit/secrets.toml` (already git-ignored; never commit this file).
   - **Environment Variable:** `$env:GOOGLE_API_KEY = "your_key_here"`
   - **Sidebar Fallback:** Enter the key directly in the sidebar password field at runtime.

3. **Run the Streamlit App:**
   ```powershell
   .\.venv\Scripts\python.exe -m streamlit run app.py
   ```

---

## Streamlit Community Cloud Deployment

This application has **zero external database** and **zero OAuth** dependencies:
1. Push `app.py`, `starbucks_crm.py`, `assets/starbucks_logo.png`, `.streamlit/config.toml`, `requirements.txt`, `README.md`, `GEMINI.md`, and `LICENSE` to GitHub (confirm `.streamlit/secrets.toml` is NOT committed).
2. Deploy `app.py` on [Streamlit Community Cloud](https://share.streamlit.io/).
3. Add `GOOGLE_API_KEY` under **App Settings → Secrets**.
