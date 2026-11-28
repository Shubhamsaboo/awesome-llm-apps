# Live Demo Recording Guide (15–20 Min Full Walkthrough + 5-Min Pitch Cut)
**App:** Starbucks China "Luckin-Counter" Agentic CRM Studio (`app.py`)  
**Goal:** Record **one single unedited 15–20 minute screen-share walkthrough** at `1440×900` (browser zoom `100%`), giving teammates a complete archive plus a clearly marked **5-minute highlight segment** to cut directly into the live pitch video.

---

## Pre-Recording Checklist (2 Minutes Before Hitting Record)
1. Launch the app locally (`.\.venv\Scripts\python.exe -m streamlit run app.py`) or open the deployed Streamlit Community Cloud URL.
2. Confirm browser window is `1440×900` (or `1920×1080` at `100%` zoom) so the top navbar, 3 uppercase tabs, 4Ps grid, and `#1E3932` House Green footer sit cleanly with zero wrapping.
3. Have a short 10–15 second sample competitor coffee promo `.mp4` clip ready on your Desktop if you plan to upload a real clip in Segment 2 (or be ready to walk through Mode 1's upload flow clearly).
4. Confirm the sidebar shows **`Gemini API Key ready`** (never open `.streamlit/secrets.toml` on screen!).

---

## ✂️ 5-Minute Live Pitch Cut Sheet (For the Video Editor)
If teammates only need a **tight 5-minute demo** for the live class pitch, splice these exact segments from the single 18-minute recording:

| Pitch Segment | Source Timestamp | Duration | What the Audience Sees |
| :--- | :--- | :--- | :--- |
| **Hook & Branding** | `0:00 – 0:45` | 0:45 | Official Starbucks UI, 2026 Luckin strategic tension, Apache-2.0 attribution |
| **Preset 2 Live Run + Blueprint** | `7:30 – 9:45` | 2:15 | Click Preset 2 → Generate → 4Ps/KPIs/A-B Test card + WeCom opt-in push + Tab 1 Storyboard |
| **Tab 2 RedNote + GEO + 3:4 Cover** | `9:45 – 11:30` | 1:45 | Xiaohongshu KOS post, GEO card, live `gemini-nano-banana-2.1` 3:4 cover generation (stays on Tab 2!) |
| **Governance Gate + CSV Log** | `15:30 – 16:45` | 1:15 | Tab 3 4/4 `PASS ✅` (incl. PIPL), Approve & Dispatch → Audit Log + CSV download *(trim 1 min total to hit exact 5:00)* |

---

## Full 18-Minute Unedited Talking Script

### Segment 1 — Intro, 2026 Context & Open-Source Attribution (`0:00 – 2:00`)
- **On Screen:** Start at the top of the app showing the white Starbucks top navigation bar (`STARBUCKS CHINA`, top-right Siren logo) and House Green hero banner. Expand `📚 Starbucks Knowledge Base Preview` in the sidebar briefly, then scroll quickly to the `#1E3932` bottom footer and back up.
- **Talking Points:**
  - *"Welcome to our MKT 6013 CRM prototype: the **Starbucks China 'Luckin-Counter' Agentic CRM Studio**."*
  - *"In 2026, Starbucks China operates roughly 8,000+ stores under the April 2026 Boyu Capital joint venture, competing against Luckin Coffee's ~38,900 stores. Starbucks cannot—and should not—fight a ¥9.9 discount war. Instead, it needs speed and hyper-personalized CRM execution grounded in coffee craft and Starbucks Rewards loyalty."*
  - *"In the sidebar, you can see our grounded 2026 Starbucks China Knowledge Base—seasonal drinks, pastry cross-sell pairings, official anchor prices (~¥30–¥35), WeChat Mini Program channels (`啡快`, `专星送`, Online Coffee Mall), and China PIPL opt-in consent rules."*
  - *"For academic transparency, our lightweight Streamlit base is adapted from `Shubhamsaboo/awesome-llm-apps` (`starter_ai_agents/multimodal_ai_agent`, Apache-2.0 License), which we refactored onto the official `google-genai` SDK with our custom Starbucks CRM architecture, Pydantic schema, and governance controls."*

---

### Segment 2 — Mode 1: Competitor Video Counter-Strike Walkthrough (`2:00 – 6:00`)
- **On Screen:** Click **`Mode 1 — Competitor Video Counter-Strike`**. Show the `.mp4`/`.mov` uploader, optional counter-beverage dropdown (`Auto-Select Best Starbucks Counter Drink`), and strategic angle notes box. *(If you have a sample `.mp4` clip ready, upload it and run a live teardown; otherwise walk through the flow and pipeline live on screen.)*
- **Talking Points:**
  - *"Mode 1 solves competitive reaction speed. When a rival drops a viral Douyin promo, a Starbucks marketer uploads the `.mp4` or `.mov` clip here."*
  - *"Under the hood, our backend uploads the video securely to the Gemini File API, polls until `ACTIVE`, analyzes the video's opening hook, editing pacing, offer mechanic, and strategic weakness with `gemini-4-hydrogen`, and automatically deletes both the remote Gemini file and local temp file inside a `finally` block."*
  - *"Crucially, the competitive teardown is quarantined to an internal strategy brief—our brand guardrails guarantee zero mention of Luckin or ¥9.9 pricing ever leaks into consumer-facing copy."*

---

### Segment 3 — Live Run of Presets 1, 2 & 3 (`6:00 – 13:00`) ★ *Primary 5-Min Pitch Window: `7:30 – 12:30`*
- **6:00 – 7:30 | Showcase Presets 1 & 3 (RFM Switching):**
  - Click **`Preset 1: Prospect Acquisition (KOL)`** — point out how it automatically sets *Peppermint Mocha*, *Prospect / Welcome*, *KOL (Lifestyle Influencer)*, *Bilingual*, and acquisition KPIs (`CPA, ROAS, Mini Program Sign-Up Conversion`).
  - Click **`Preset 3: At-Risk Gold Win-Back (KOC)`** — point out how it switches to *Jolly Baked Apple Latte*, *At-Risk Gold Member*, *KOC*, and retention KPIs (`Win-Back Rate, CLV, NPS`) focused on Gold exclusivity instead of cheap coupons.
- **7:30 – 9:45 | Full Live Run of Preset 2 (Green Star Cross-Sell / KOS Barista):**
  - Click **`Preset 2: Green Star Cross-Sell (KOS)`** (*Toffee Nut Crunch Latte* + *Green Star Member* + *KOS Barista* + *Bilingual*).
  - Click **`✨ Generate CRM Counter-Campaign`** (while spinning ~20–25s, explain that Gemini is enforcing our 5-step prompt and strict Pydantic JSON schema).
  - Once generated, walk down the **Warm Neutral `🧭 4Ps, KPIs & A/B Test Blueprint`** card:
    - Point to **Product** (barista customization + *Holiday Chestnut Cake* / *Almond Croissant* cross-sell), **Price** (grounded ~¥30–¥35), **Promotion** (Star progress toward Gold), **Place** (`啡快` / `专星送` / Online Coffee Mall), the 3 Green Star KPIs (**AOV**, **Food/Pastry Attach Rate**, **Repeat Visits**), and the **Control vs. Variant A/B Hook Test**.
  - Expand **`💬 1-on-1 WeCom / WeChat Mini Program Push Message Preview`** — highlight the warm, non-spammy Bilingual message and PIPL opt-in privacy note.
  - Scroll through **Tab 1 (`DOUYIN/REELS SCRIPT & STORYBOARD`)**: point out `0–5s Hook`, `5–20s Craft & Proof`, `20–30s Segment-Specific CTA`, and the 5–6 shot storyboard with copy-paste AIGC prompts for Veo/Kling.
- **9:45 – 13:00 | Tab 2: Xiaohongshu Post, GEO Readiness & Live 3:4 Cover Image Generation:**
  - Click **`XIAOHONGSHU POST & COVER`** (Tab 2).
  - Highlight the styled RedNote preview card written in authentic **KOS Barista** voice, the **Barista Formula / Rewards CTA** box, and separated **Short-Tail** vs. **Long-Tail SEO Hashtags**.
  - Point to the **`🤖 GEO (Generative Engine Optimization) Readiness`** card directly below: explain how the Target AI Query and Answer-First summary prepare Starbucks China content to be cited by AI assistants (Doubao, Kimi, DeepSeek, ChatGPT/Gemini).
  - On the right side, click **`🖼️ Generate Xiaohongshu Cover Image`**. Emphasize two wins as the 3:4 portrait image renders inline:
    1. Powered by `gemini-nano-banana-2.1` (with automatic fallback to `gemini-3.1-flash-lite-image`).
    2. Isolated inside `@st.fragment`, so Tab 2 stays active with zero page reset, and the **`⬇️ Download PNG`** pill button is immediately ready.

---

### Segment 4 — Tab 3 Prompt Inspector, PIPL Guardrails & Human-in-the-Loop Governance (`13:00 – 18:00`)
- **13:00 – 15:15 | Tab 3 (`PROMPT INSPECTOR`):**
  - Click **`PROMPT INSPECTOR`** (Tab 3).
  - Point across all **4 automated compliance badges** showing `PASS ✅`:
    1. `No RMB 9.9 Discounting`
    2. `Zero Competitor Naming`
    3. `Grounded Pricing & Claims`
    4. `WeChat / PIPL Opt-In`
  - Scroll briefly through the exact 5-step assembled prompt (`1. Role` → `2. Context & Knowledge Base` → `3. Goal` → `4. Format & Style` → `5. Constraints`), note the **`⬇️ Download Prompt (.txt)`** button, and briefly expand **`🗂️ Raw Structured JSON Output`** to prove deterministic Pydantic structured output.
- **15:15 – 17:30 | Human-in-the-Loop Governance Gate & CSV Audit Log:**
  - Scroll just below the 3 tabs to **`🛡️ Human-in-the-Loop Governance Gate & CRM Dispatch`**.
  - Explain: *"In enterprise Agentic CRM, AI drafts campaigns, but human marketers own brand and legal accountability."*
  - First type `"Adjust pastry cross-sell visual angle"` and click **`🚩 Reject & Flag for Revision`** — show the amber `Revision Requested` log row appearing instantly without losing the tabs.
  - Next type `"Approved for Shanghai Tier-1 WeCom & Xiaohongshu pilot"` and click **`✅ Approve & Dispatch to Starbucks CRM`** — show the green **`Queued for Execution`** (`4/4 PASS`) row at the top of the **CRM Dispatch & Audit Log**, and point to **`⬇️ Download CRM Dispatch Log (.csv)`**.
- **17:30 – 18:00 | Wrap-Up:**
  - Scroll down to rest briefly on the official `#1E3932` Starbucks footer showing our MKT 6013 academic & Apache-2.0 attribution.
  - *"That's our end-to-end Starbucks China 'Luckin-Counter' Agentic CRM Studio—combining multimodal AI speed, RFM & 4Ps rigor, GEO readiness, PIPL compliance, and human-in-the-loop governance."*
