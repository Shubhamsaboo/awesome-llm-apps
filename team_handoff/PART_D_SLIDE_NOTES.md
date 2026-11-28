# Part D (Prototype Design) — 10-Slide Content Blueprint
**Project:** Starbucks China "Luckin-Counter" Agentic CRM Studio (MKT 6013 CRM Project)  
**Target Deck Section:** Part D — Prototype Design (10 Slides)  
**Companion Files:** `team_handoff/DEMO_RECORDING_GUIDE.md` • `team_handoff/sample_assembled_prompt.txt`

---

## Slide 1 — Strategic Imperative: Why This Prototype Matters to Starbucks China
- **2026 China Coffee Battlefield:** Operating ~8,000+ stores under the April 2026 Boyu Capital joint venture, Starbucks China faces unprecedented velocity from Luckin Coffee (~38,900 stores) driven by aggressive RMB 9.9 couponing and rapid viral product drops.
- **The Strategic Trap:** Copying ¥9.9 flash discounts destroys Starbucks' premium margin, erodes brand equity, and alienates loyal Gold Star members.
- **The Real Gap — Speed & Personalization:** Starbucks China does not lack coffee craft or "Third Place" love; it needs **agile, RFM-personalized omnichannel content** that responds to competitor viral campaigns in minutes instead of weeks.
- **Our Prototype's Role:** An **Agentic CRM Studio** that empowers Starbucks China marketers to counter competitor promotions (or launch seasonal drinks) across Douyin, Xiaohongshu, and WeCom—anchored strictly in craft quality, food-attach value, and Starbucks Rewards exclusivity.

---

## Slide 2 — Prototype Overview: Starbucks China "Luckin-Counter" Agentic CRM Studio
- **One-Sentence Pitch:** A lightweight, browser-based multimodal Gemini CRM studio styled in Starbucks' official web identity that transforms a competitor video or seasonal drink brief into an approved, multi-channel campaign in under 30 seconds.
- **Zero-Friction Deployment:** Built in pure Python + Streamlit (`app.py`, `starbucks_crm.py`), zero external database, zero OAuth, 4 minimal dependencies (`streamlit`, `google-genai`, `pillow`, `pydantic`), ready for instant Streamlit Community Cloud hosting.
- **Multimodal Intelligence (Nov 2026 Gemini Stack):**
  - **Reasoning & Video Analysis:** `gemini-4-hydrogen` (switchable to `gemini-3.8-flash` / `gemini-3.5-flash-lite`) with Pydantic `response_schema` for deterministic JSON outputs.
  - **Xiaohongshu Visual Engine:** `gemini-nano-banana-2.1` (3:4 portrait aspect ratio) with automatic fallback to `gemini-3.1-flash-lite-image`.
- **Output Languages:** Full support for **English**, **Chinese (简体中文)**, and **Bilingual (EN + 中文)** for seamless global-local team workflows.

---

## Slide 3 — Prototype Architecture & Agentic CRM Mapping
Map our studio directly to the **3 Pillars of Modern CRM + Governance** taught in MKT 6013:

| CRM Pillar | Studio Capability | Starbucks China Business Impact |
| :--- | :--- | :--- |
| **Operational CRM** *(Execution & Campaign Delivery)* | 30-sec Douyin/Reels scripts, shot-by-shot AIGC video prompts, Xiaohongshu (RedNote) posts + 3:4 cover visuals, and **1-on-1 WeCom / Mini Program opt-in push copy**. | Cuts campaign creative turnaround from days to minutes across China's top social & private-traffic channels (`啡快`, `专星送`, Online Coffee Mall). |
| **Analytical CRM** *(RFM Intelligence & Experimentation)* | **Starbucks Rewards RFM Lifecycle Segmentation** (Prospect, Green Star, At-Risk Gold), **4Ps Mix**, segment-matched **Primary KPIs**, and **A/B Creative Hook Experimentation** (`Control` vs. `Variant`, hypothesis, success metric). | Aligns every message to measurable lifecycle metrics: Prospect → CPA/ROAS/Sign-Ups; Green Star → AOV/Pastry Attach/Repeat Visits; At-Risk Gold → Win-Back Rate/CLV/NPS. |
| **Collaborative & Governed CRM** *(Ecosystem Alignment, Privacy & Safety)* | **Creator Voice Matrix** (Official / KOL / KOS Barista / KOC), **GEO (Generative Engine Optimization)** AI-search citation card, **China PIPL & WeChat Opt-In Compliance**, and **Human-in-the-Loop Governance Gate + CSV Audit Log**. | Aligns store partners (KOS) with influencers/customers, future-proofs discovery in AI search engines, prevents ¥9.9 / competitor-naming violations, and enforces human approval before CRM dispatch. |

---

## Slide 4 — End-to-End System Flow & Guardrailed Data Pipeline
- **Step 1 — Input Ingestion:** Marketer uploads a competitor `.mp4`/`.mov` promo (Mode 1) OR picks a featured/custom Starbucks drink + occasion notes (Mode 2) OR clicks one of **3 One-Click Demo Presets**.
- **Step 2 — Grounded 5-Step Prompt Assembly (`starbucks_crm.py`):** Injects 2026 Starbucks China store/JV context, approved pastry cross-sell pairings, anchor pricing (`Tall ~¥30`, `Grande ~¥33`, `Flat White ~¥35`), RFM rules, Creator Voice tone, and PIPL privacy constraints.
- **Step 3 — Secure Multimodal Inference (`google-genai`):**
  - Video clips upload via `client.files.upload()`, poll until `ACTIVE`, run structured generation, and auto-delete both remote Gemini files and local temp files in a `finally` block.
- **Step 4 — Structured Rendering & Isolated Fragments:** Pydantic `CampaignOutput` populates the Blueprint strip and all 3 tabs deterministically; `@st.fragment` isolates Tab 2 cover image generation and the Governance Gate so actions never wipe generated tabs.
- **Step 5 — Human Governance & Audit Export:** Marketer reviews 4 automated compliance badges, approves or flags for revision, and exports the **CRM Dispatch & Audit Log (`.csv`)**.

---

## Slide 5 — Feature Walkthrough (1/3): Dual Input Modes, RFM Segments & Demo Presets
- **Dual Input Modes:**
  - **Mode 1 — Competitor Video Counter-Strike:** Upload a competitor `.mp4`/`.mov` promo to generate an internal *Competitor Viral Teardown* (hook, pacing, offer mechanic, strategic weakness) and a craft-led Starbucks counter-campaign.
  - **Mode 2 — Direct Seasonal Launch:** Zero video needed—pick from 5 core seasonal beverages (*Toffee Nut Crunch Latte*, *Peppermint Mocha*, *Jolly Baked Apple Latte*, *Blonde Oat Latte*, *Seasonal Holiday Cold Brew*) or enter a custom drink.
- **3 One-Click Demo Presets (Bilingual Ready):**
  1. **Preset 1 — Prospect Acquisition (KOL):** *Peppermint Mocha* + Prospect/Welcome + Lifestyle KOL.
  2. **Preset 2 — Green Star Cross-Sell (KOS):** *Toffee Nut Crunch Latte* + Green Star Member + Barista KOS (oat milk/half-syrup + pastry cross-sell).
  3. **Preset 3 — At-Risk Gold Win-Back (KOC):** *Jolly Baked Apple Latte* + At-Risk Gold Member + Everyday Customer KOC (double-Star / complimentary upgrade win-back).
- **Sidebar Transparency:** Model selector, language switch, secure API key resolution (`st.secrets` → env → password input), and expandable **Starbucks Knowledge Base Preview**.

---

## Slide 6 — Feature Walkthrough (2/3): 4Ps/KPIs/A-B Blueprint, WeCom Push & Tab 1 Storyboard
- **4Ps, KPIs & A/B Test Blueprint Card (Above Tabs):**
  - Displays tailored **Product** (including pastry cross-sell pairings like *Holiday Chestnut Cake* or *Almond Croissant*), **Price** (grounded anchor framing), **Promotion** (Rewards perk), **Place** (`啡快`, `专星送`, Online Coffee Mall, ~8,000+ stores), **Campaign Period**, **3 Segment KPIs**, and **Control vs. Variant A/B Hook Test**.
- **1-on-1 WeCom / Mini Program Push Preview:** Expandable private-traffic trigger message crafted to feel like warm barista service—never intrusive spam—with an explicit PIPL opt-in privacy note.
- **Tab 1 — 30-Sec Douyin/Reels Video Script & Storyboard:**
  - Internal **Teardown / Market Opportunity Card** (competitive analysis strictly quarantined from consumer copy).
  - 3-act script cards: **`0–5s Hook`**, **`5–20s Craft & Proof`**, and **`20–30s Segment-Specific CTA`**.
  - **Shot-by-Shot Storyboard Table** with timestamps, camera angles, voiceover/overlays, and **1-click copyable English AIGC video prompts** (Veo / Kling / Runway ready).

---

## Slide 7 — Feature Walkthrough (3/3): Tab 2 Xiaohongshu Post, GEO Readiness & Live 3:4 Cover Visuals
- **RedNote Seeding Preview Card:** Renders clickable emoji title, authentic KOL/KOS/KOC body copy, pinned **Barista Formula / Rewards CTA** box, and separated **Short-Tail SEO Hashtags** (broad reach) vs. **Long-Tail SEO Hashtags** (high conversion intent).
- **GEO (Generative Engine Optimization) Readiness Card:**
  - Displays a realistic **Target AI Query** (e.g., *"What is the best winter holiday coffee to order at Starbucks China?"*) paired with a fact-dense **Answer-First Citation Summary** containing unambiguous Starbucks China brand, drink, anchor price (~¥30–¥35), and WeChat Mini Program entities built for AI search engines.
- **Live 3:4 Portrait Cover Visual Studio:**
  - Pre-filled, editable cover prompt + **`Generate Xiaohongshu Cover Image`** button powered by `gemini-nano-banana-2.1` (auto-fallback: `gemini-3.1-flash-lite-image`).
  - Wrapped in `@st.fragment` so generating and downloading the PNG never resets Tab 2.
  - **Starbucks Siren Watermark:** Toggle (on by default) overlays the official Siren logo in a chosen corner (bottom-right default) with a soft shadow, so the downloaded PNG looks like a real Starbucks China brand post.

---

## Slide 8 — Prompt Engineering Architecture: 5-Step Grounded Framework
Every Gemini request is assembled transparently in `starbucks_crm.py` (`build_campaign_prompt`) using the **5-Step Prompting Framework** and inspectable live in **Tab 3 — Prompt Inspector** (full rendered Preset 2 sample saved in `team_handoff/sample_assembled_prompt.txt`):

```markdown
### 1. Role
Senior Agentic CRM Strategist & Omnichannel Creative Director for Starbucks China
specializing in high-LTV retention, RFM lifecycle marketing, 4Ps, A/B testing,
Douyin/Reels storytelling, Xiaohongshu KOL/KOS/KOC seeding, and GEO.

### 2. Context & Knowledge Base
- 2026 Market Context: ~8,000+ Starbucks China stores (April 2026 Boyu Capital JV)
  defending premium craft vs. Luckin Coffee (~38,900 stores).
- Input Mode: Mode 1 (Uploaded Competitor Video) or Mode 2 (Direct Seasonal Launch).
- Selected RFM Segment: Profile, mindset, strategic focus, mandatory CTA, & 3 KPIs.
- Assigned Creator Voice: Role, funnel role, tone/style, hook pattern, RedNote style.
- Grounded KB: Hero drink flavor/customizations, approved pastry pairings,
  anchor pricing (~¥30 Tall / ~¥33 Grande / ~¥35 Flat White), official WeChat Mini
  Program channels (啡快, 专星送, Online Coffee Mall), and China PIPL consent rule.

### 3. Goal
Generate 7 cohesive artifacts: (1) 4Ps/KPIs/A-B Blueprint, (2) Strategic Teardown,
(3) 30-sec Douyin Script + 5–6 Shot Storyboard, (4) Xiaohongshu Seeding Post + 3:4
Cover Prompt, (5) GEO Readiness Snippet, (6) 1-on-1 WeCom Opt-In Push, and
(7) Brand & PIPL Guardrail Self-Check.

### 4. Format & Style
- Strict Output Language Rule (English / 简体中文 / Bilingual EN + 中文).
- Strict Pydantic `CampaignOutput` JSON schema (`response_schema`) for zero-error UI.
- Native Douyin pacing, authentic RedNote tone, English AIGC/cover prompts.

### 5. Constraints
- NEVER recommend RMB 9.9 flash discounts or price-war tactics.
- NEVER mention or attack Luckin Coffee (or any rival) in consumer-facing copy.
- NEVER invent fake prices, promo codes, or unverified health claims.
- ALWAYS enforce China PIPL & WeChat Opt-In Privacy (separate location/offer consent,
  zero spam) and align every CTA to official Starbucks China channels.
```

---

## Slide 9 — Brand Guardrails, China PIPL Privacy & Human-in-the-Loop Governance
- **4 Automated Compliance Checks (Tab 3 — Prompt Inspector):**
  1. **No RMB 9.9 Discounting (`PASS ✅`)** — Protects premium pricing architecture.
  2. **Zero Competitor Naming (`PASS ✅`)** — Quarantines competitive analysis to internal briefs only.
  3. **Grounded Pricing & Claims (`PASS ✅`)** — Restricts prices to verified anchor tiers; blocks hallucinated promos/health claims.
  4. **WeChat / PIPL Opt-In (`PASS ✅`)** — Enforces China Personal Information Protection Law opt-in consent and anti-spam norms on WeCom/Mini Program pushes.
- **Human-in-the-Loop Governance Gate (Agentic Safety Checkpoint):**
  - AI drafts; **humans authorize**. Marketers add optional reviewer notes and choose **`Approve & Dispatch to Starbucks CRM`** (`Status = Queued for Execution`) or **`Reject & Flag for Revision`** (`Status = Revision Requested`).
- **Auditable CRM Dispatch Log (`.csv`):** Every decision is timestamped with Drink, RFM Segment, Creator Voice, Target Channels, Guardrail Score (`4/4 PASS`), Status, and Reviewer Note—downloadable as UTF-8 CSV for compliance auditing.

---

## Slide 10 — Open-Source & Third-Party Attribution
- **Open-Source Base Cited Transparently:** Adapted from [`Shubhamsaboo/awesome-llm-apps`](https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/starter_ai_agents/multimodal_ai_agent) (`starter_ai_agents/multimodal_ai_agent`), licensed under the **Apache-2.0 License** (`LICENSE` preserved in repository root and cited in the app footer and `README.md`).

| Component | Open-Source Starter (`awesome-llm-apps`, Apache-2.0) | Custom MKT 6013 Team Engineering (Starbucks China CRM Studio) |
| :--- | :--- | :--- |
| **SDK & Dependencies** | `agno` + deprecated `google-generativeai` + DuckDuckGo search | Migrated cleanly to official **`google-genai`** SDK (`gemini-4-hydrogen`, `gemini-nano-banana-2.1`) + Pydantic structured output; removed deprecated packages |
| **Video Processing** | Basic single-prompt video Q&A | Secure Gemini File API upload → `ACTIVE` polling → guaranteed remote & local temp cleanup (`finally`) powering Competitor Viral Teardowns |
| **Domain Intelligence** | Generic ungrounded chat prompt | Modular `starbucks_crm.py`: 2026 Boyu Capital JV KB, RFM segments & KPIs, 4Ps, A/B Test, Creator Voice Matrix (Official/KOL/KOS/KOC), pastry pairings, GEO snippet, WeCom push, & PIPL rules |
| **Output & Visuals** | Single raw Markdown text blob | Deterministic Pydantic schema rendering Blueprint Card + 3 structured tabs (Douyin Storyboard, RedNote Post + live 3:4 Cover Generator in `@st.fragment`, Prompt Inspector + JSON viewer) |
| **UI & Governance** | Default minimal Streamlit page | Official Starbucks web theme (`Plus Jakarta Sans`, `#1E3932`/`#00754A`/`#D4E9E2`/`#F2F0EB`, base64 Siren logo, navbar & House Green footer), 3 Demo Presets, 4 compliance badges, & Human-in-the-Loop Governance Gate + CSV Audit Log |
