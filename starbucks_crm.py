"""
Starbucks China "Luckin-Counter" Agentic CRM Domain Logic & Prompt Architecture.

Contains:
- Model configuration (November 2026 Gemini SDK defaults & fallbacks)
- Starbucks Rewards RFM Lifecycle Segments (with aligned acquisition/cross-sell/retention KPIs)
- Creator Voice Matrix (Official / KOL / KOS / KOC)
- Starbucks China 2026 Grounding Knowledge Base (Boyu Capital JV scale, food pairings,
  WeChat Mini Program ecosystem, and PIPL/WeChat opt-in privacy rules)
- One-click Demo Presets for live MKT 6013 presentation
- Pydantic structured output schema (`CampaignOutput`) including 4Ps, KPIs, A/B Test,
  GEO Readiness, and 1-on-1 WeCom push copy
- 5-step prompting framework builder (`build_campaign_prompt`)
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 1. Model & Language Constants (November 2026)
# ---------------------------------------------------------------------------

TEXT_MODELS: List[str] = [
    "gemini-4-hydrogen",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
]
DEFAULT_TEXT_MODEL: str = "gemini-4-hydrogen"

PRIMARY_IMAGE_MODEL: str = "gemini-nano-banana-2.1"
FALLBACK_IMAGE_MODEL: str = "gemini-3.1-flash-lite-image"

OUTPUT_LANGUAGES: List[str] = [
    "English",
    "Chinese (简体中文)",
    "Bilingual (EN + 中文)",
]

# ---------------------------------------------------------------------------
# 2. Starbucks Rewards Lifecycle Segments (RFM Logic + Segment KPIs)
# ---------------------------------------------------------------------------

REWARDS_SEGMENTS: dict[str, dict[str, str]] = {
    "Prospect / Welcome (Acquisition)": {
        "short_name": "Prospect / Welcome",
        "rfm_logic": "Recency: None | Frequency: 0 orders (Non-Member / New Guest) | Monetary: ¥0",
        "audience_mindset": (
            "Curious about seasonal specialty drinks or seeking a comforting café atmosphere, "
            "but has not yet joined Starbucks Rewards or formed an ordering habit."
        ),
        "strategic_focus": (
            "Lead with signature espresso craft, freshly roasted aroma, sensory indulgence, "
            "and Starbucks' iconic 'Third Place' warmth."
        ),
        "cta_requirement": (
            "Drive opt-in Starbucks China App or WeChat Mini Program signup with a first-cup welcome perk "
            "(Welcome-tier onboarding without cheap discount framing)."
        ),
        "primary_channels": "Starbucks China App, WeChat Mini Program (Starbucks Now 啡快)",
        "kpi_targets": "CPA (Cost per Acquisition), ROAS (Return on Ad Spend), Mini Program Sign-Up Conversion Rate",
    },
    "Green Star Member (Semi-Active / Frequency Push)": {
        "short_name": "Green Star Member",
        "rfm_logic": "Recency: Visits every 3–6 months | Frequency: Low–Moderate | Monetary: Occasional Spend",
        "audience_mindset": (
            "Already knows and likes Starbucks, but treats it as an occasional stop rather than "
            "a regular weekly coffee & pastry ritual."
        ),
        "strategic_focus": (
            "Focus on habit-building, pastry/food cross-sell pairings to elevate basket AOV, and seasonal "
            "limited-time urgency before the drink leaves the menu."
        ),
        "cta_requirement": (
            "Highlight Star-earning progress toward Gold Star tier, pastry pairing combos, and effortless "
            "Starbucks Now (啡快) skip-the-line convenience or Starbucks Delivers (专星送) office delivery."
        ),
        "primary_channels": "WeChat Mini Program (Starbucks Now 啡快, Starbucks Delivers 专星送, Online Coffee Mall), Starbucks China App",
        "kpi_targets": "AOV (Average Order Value), Food/Pastry Attach Rate, Repeat Visit Frequency",
    },
    "At-Risk Gold Member (Switcher / Win-Back from Luckin)": {
        "short_name": "At-Risk Gold Member",
        "rfm_logic": "Recency: 6–12 months since last visit | Frequency: Previously High, now lapsing | Monetary: High Historical LTV",
        "audience_mindset": (
            "Long-time quality coffee drinker who drifted toward RMB 9.9 mass-discount coupon coffee "
            "for convenience/price, yet misses authentic espresso richness, calm store ambience, and member recognition."
        ),
        "strategic_focus": (
            "NEVER copy cheap price-war discounting. Win back via high-perceived-value Gold exclusivity: "
            "bespoke barista customization, complimentary size/milk upgrade or extra espresso shot, "
            "double-Star comeback offer, or an elevated Starbucks Reserve experience."
        ),
        "cta_requirement": (
            "Invite them back via opt-in Starbucks China App / WeCom Gold Rewards Wallet privileges "
            "(double-Star comeback reward, complimentary upgrade/extra shot, or personalized barista craft)."
        ),
        "primary_channels": "Starbucks China App (Gold Rewards Wallet), WeCom Opt-In Push, Starbucks Now (啡快), Starbucks Reserve Stores",
        "kpi_targets": "Win-Back Rate, CLV (Customer Lifetime Value), NPS (Net Promoter Score)",
    },
}

# ---------------------------------------------------------------------------
# 3. Creator Voice Matrix (Official / KOL / KOS / KOC)
# ---------------------------------------------------------------------------

CREATOR_VOICES: dict[str, dict[str, str]] = {
    "Official Brand": {
        "role_title": "Starbucks China Official Brand Voice",
        "funnel_role": "Brand Heritage, Trust & Seasonal Launch Authority",
        "tone_and_style": (
            "Polished, warm, authoritative seasonal launch voice highlighting official store availability, "
            "bean-to-cup craftsmanship, and Starbucks' enduring seasonal ritual."
        ),
        "hook_pattern": "Iconic seasonal arrival, warm editorial visuals, craft-first opening line.",
        "xiaohongshu_formatting": (
            "Refined editorial copy, clean paragraph spacing, restrained emojis, clear official channel callouts."
        ),
    },
    "KOL (Lifestyle Influencer)": {
        "role_title": "Urban Café & Lifestyle KOL",
        "funnel_role": "Top-of-Funnel Awareness & Aesthetic Aspiration",
        "tone_and_style": (
            "High-reach aesthetic hook, aspirational citywalk/café lifestyle storytelling, "
            "cinematic mood-setting (OOTD pairing, sunlit café table, seasonal atmosphere)."
        ),
        "hook_pattern": "Visually arresting 0–3s aesthetic hook + emotional city-lifestyle narrative.",
        "xiaohongshu_formatting": (
            "Magazine-worthy storytelling, vivid sensory descriptors, photo-angle inspiration, save-worthy aesthetic vibe."
        ),
    },
    "KOS (Starbucks Barista / Store Partner)": {
        "role_title": "Starbucks Store Partner / Barista KOS",
        "funnel_role": "Mid-to-Bottom Funnel Craft Credibility & Store Conversion",
        "tone_and_style": (
            "Insider craft expertise from behind the espresso bar: tasting/aroma notes, pastry pairing suggestions, "
            "and practical 'barista secret customization' tips (e.g., oat milk swap, half-sweet/less syrup, "
            "Blonde Espresso upgrade, extra shot) that drive immediate store or 啡快 orders."
        ),
        "hook_pattern": "Insider behind-the-bar confession ('As a Starbucks barista, here is my exact order formula...').",
        "xiaohongshu_formatting": (
            "Structured ordering guide (点单攻略 / Barista Formula), bulleted customization & pastry pairing checklist, warm expert tone."
        ),
    },
    "KOC (Everyday Customer)": {
        "role_title": "Everyday Urban Commuter / Coffee Fan KOC",
        "funnel_role": "Peer Social Proof & Authentic Xiaohongshu Seeding (种草)",
        "tone_and_style": (
            "Relatable peer-to-peer review tone, office commute or 3 PM afternoon pick-me-up vibe, "
            "honest first-sip reaction and authentic Xiaohongshu seeding style."
        ),
        "hook_pattern": "Relatable everyday scenario ('The afternoon pick-me-up that genuinely saved my workday...').",
        "xiaohongshu_formatting": (
            "Conversational friend-to-friend rhythm, candid taste/texture notes, natural emojis, organic recommendation feel."
        ),
    },
}

# ---------------------------------------------------------------------------
# 4. Starbucks China 2026 Knowledge Base (Grounding, Cross-Sell & Privacy)
# ---------------------------------------------------------------------------

STARBUCKS_KB: dict = {
    "market_context_2026": (
        "As of late 2026, Starbucks China operates ~8,000+ stores under the April 2026 Boyu Capital "
        "joint venture, defending premium specialty coffee craft, Third Place hospitality, and high-LTV "
        "Starbucks Rewards equity against hyper-scale discount rival Luckin Coffee (~38,900 stores)."
    ),
    "featured_drinks": {
        "Toffee Nut Crunch Latte (太妃榛果拿铁)": {
            "flavor_profile": (
                "Rich buttery toffee and roasted hazelnut notes blended with signature Starbucks espresso "
                "and velvety steamed milk, finished with whipped cream and crunchy toffee nut topping."
            ),
            "seasonal_positioning": "Starbucks China's most iconic winter & holiday comeback ritual.",
            "barista_customizations": [
                "Swap to Oat Milk (燕麦奶) + half syrup (少糖/半糖) for nutty balance",
                "Upgrade to Blonde Espresso (金烘浓缩) for brighter roasted sweetness",
                "Add an extra ristretto/espresso shot for bolder coffee kick",
            ],
        },
        "Peppermint Mocha (薄荷摩卡)": {
            "flavor_profile": (
                "Signature espresso paired with bittersweet mocha sauce and crisp peppermint aroma, "
                "topped with whipped cream and festive dark chocolate curls."
            ),
            "seasonal_positioning": "Festive indulgent classic balancing refreshing mint with rich cocoa.",
            "barista_customizations": [
                "Less mocha pump + oat milk for cleaner mint-chocolate finish",
                "Hot Grande with extra shot for crisp afternoon energy",
                "No whipped cream option for lighter daily enjoyment",
            ],
        },
        "Jolly Baked Apple Latte (烤苹果风味拿铁)": {
            "flavor_profile": (
                "Warm caramelized baked-apple flavor and gentle autumnal spice layered over smooth espresso "
                "and creamy steamed milk."
            ),
            "seasonal_positioning": "Cozy bakery-inspired comfort cup tailored for chilly city days.",
            "barista_customizations": [
                "Swap to Blonde Espresso + oat milk to spotlight baked-apple aroma",
                "Half syrup for delicate dessert-like warmth without excess sweetness",
                "Extra hot for a lingering cozy Third Place experience",
            ],
        },
        "Blonde Oat Latte (金烘燕麦拿铁)": {
            "flavor_profile": (
                "Lightly roasted Starbucks Blonde Espresso paired with silky oat milk, delivering naturally "
                "sweet, mellow cocoa-citrus notes and ultra-smooth texture."
            ),
            "seasonal_positioning": "Year-round craft-forward everyday staple for discerning office & specialty drinkers.",
            "barista_customizations": [
                "Iced or Hot Grande with extra Blonde shot for crisp morning focus",
                "No added syrup to showcase Blonde Espresso's natural sweetness",
                "Light ice + oat milk foam for velvety mouthfeel",
            ],
        },
        "Seasonal Holiday Cold Brew (节日季冷萃咖啡)": {
            "flavor_profile": (
                "Slow-steeped Starbucks Cold Brew with naturally smooth, low-bitterness cocoa notes, "
                "crowned with subtle seasonal spiced cream cold foam."
            ),
            "seasonal_positioning": "Crisp, elevated cold-coffee craft for fans who prefer iced coffee year-round.",
            "barista_customizations": [
                "Light ice to preserve rich cold brew body",
                "Half-sweet seasonal cold foam for clean espresso-forward balance",
                "Ideal Starbucks Now (啡快) grab-and-go commute cup",
            ],
        },
    },
    "food_pairings": {
        "Almond Croissant (杏仁可颂)": "Flaky French-butter pastry layered with toasted almond cream — boosts morning & afternoon latte AOV.",
        "Cranberry Scone (蔓越莓司康)": "Warm, lightly crisp buttery scone studded with tart cranberries — ideal pairing for seasonal lattes and cold brew.",
        "Holiday Chestnut Cake (冬日栗子蛋糕)": "Velvety roasted-chestnut cream cake crafted for cozy winter holiday dessert upselling.",
        "Smoked Chicken & Cheese Panini (烟熏鸡肉芝士帕尼尼)": "Warm savory lunch cross-sell for weekday Starbucks Now (啡快) and Starbucks Delivers (专星送) orders.",
    },
    "anchor_pricing": {
        "Tall Latte (中杯拿铁)": "~¥30",
        "Grande Latte (大杯拿铁)": "~¥33",
        "Flat White (馥芮白)": "~¥35",
    },
    "channels": {
        "Starbucks China App": "Member Rewards Wallet, Gold privileges, seasonal early access, and store locator across ~8,000+ stores.",
        "WeChat Mini Program — Starbucks Now (啡快)": "Mobile order & pickup ahead on WeChat, skip the queue, earn Stars seamlessly.",
        "WeChat Mini Program — Starbucks Delivers (专星送)": "Dedicated temperature-controlled delivery with tamper-evident packaging to office or home.",
        "WeChat Mini Program — Online Coffee Mall (在线咖啡商城)": "Packaged whole-bean coffee, VIA®, holiday drinkware, and Starbucks Gift Cards for cross-sell & gifting.",
        "Starbucks Rewards": "Three-tier loyalty ecosystem — Welcome (新会员) → Green Star (玉星级) → Gold Star (金星级).",
    },
    "privacy_and_consent_rule": (
        "China PIPL & WeChat Consent Rule: All WeChat Mini Program and WeCom 1-on-1 push CTAs MUST respect "
        "opt-in privacy — require separate explicit user consent for geolocation and personalized offers, "
        "include transparent preference/opt-out control, and NEVER trigger intrusive spam blasts."
    ),
    "strict_guardrails": [
        "NEVER recommend RMB 9.9 flash discounts, ¥9.9 coupons, or cheap price-war tactics.",
        "NEVER mention, name, or attack Luckin Coffee (or any competitor brand by name) in any consumer-facing copy (video script voiceovers, on-screen text, storyboard dialogue, Xiaohongshu title, body copy, hashtags, GEO summary, WeCom push, or cover image prompt).",
        "NEVER invent fake prices, fabricated promo codes, or unverified health/nutritional/weight-loss claims.",
        "ONLY reference grounded anchor pricing (Tall Latte ~¥30, Grande ~¥33, Flat White ~¥35) if pricing context is naturally helpful; do not make up exact prices for unlisted items.",
        "ALWAYS comply with China PIPL & WeChat Opt-In Privacy: separate user consent for location/personalized offers, polite frequency, zero intrusive spam blasts.",
        "ALWAYS protect Starbucks China's premium coffee craft, sensory warmth, and 'Third Place' brand equity.",
    ],
}

# ---------------------------------------------------------------------------
# 5. One-Click Demo Presets (MKT 6013 Live Presentation)
# ---------------------------------------------------------------------------

DEMO_PRESETS: dict[str, dict[str, str]] = {
    "preset_1": {
        "button_label": "Preset 1: Prospect Acquisition (KOL)",
        "mode": "Mode 2 — Direct Seasonal Launch",
        "drink": "Peppermint Mocha (薄荷摩卡)",
        "segment": "Prospect / Welcome (Acquisition)",
        "voice": "KOL (Lifestyle Influencer)",
        "language": "Bilingual (EN + 中文)",
        "notes": (
            "Festive winter citywalk café discovery highlighting fresh espresso aroma, cozy Third Place "
            "window seating, and opt-in Welcome first-cup perk via Starbucks China App / WeChat Mini Program."
        ),
    },
    "preset_2": {
        "button_label": "Preset 2: Green Star Cross-Sell (KOS)",
        "mode": "Mode 2 — Direct Seasonal Launch",
        "drink": "Toffee Nut Crunch Latte (太妃榛果拿铁)",
        "segment": "Green Star Member (Semi-Active / Frequency Push)",
        "voice": "KOS (Starbucks Barista / Store Partner)",
        "language": "Bilingual (EN + 中文)",
        "notes": (
            "Barista secret customization (oat milk swap + half syrup) paired with Holiday Chestnut Cake "
            "or Almond Croissant cross-sell via Starbucks Now (啡快) to grow basket AOV and accelerate Gold Star progress."
        ),
    },
    "preset_3": {
        "button_label": "Preset 3: At-Risk Gold Win-Back (KOC)",
        "mode": "Mode 2 — Direct Seasonal Launch",
        "drink": "Jolly Baked Apple Latte (烤苹果风味拿铁)",
        "segment": "At-Risk Gold Member (Switcher / Win-Back from Luckin)",
        "voice": "KOC (Everyday Customer)",
        "language": "Bilingual (EN + 中文)",
        "notes": (
            "Relatable chilly 3 PM workday comeback review celebrating Gold-exclusive double-Star return perk "
            "and complimentary extra espresso shot / milk upgrade instead of mass-discount coffee."
        ),
    },
}

# ---------------------------------------------------------------------------
# 6. Pydantic Structured Output Schema (for Gemini `response_schema`)
# ---------------------------------------------------------------------------


class FourPs(BaseModel):
    product: str = Field(
        description="Hero Starbucks drink, barista customization hook, and recommended pastry/food cross-sell pairing."
    )
    price: str = Field(
        description="Value-led pricing framing grounded strictly in official anchor pricing (~¥30 Tall / ~¥33 Grande / ~¥35 Flat White) with zero RMB 9.9 discounting."
    )
    promotion: str = Field(
        description="Segment-matched Starbucks Rewards value mechanic (Welcome perk, Star-progress pastry bundle, or Gold exclusive double-Star/upgrade)."
    )
    place: str = Field(
        description="Omnichannel execution across Starbucks China ~8,000+ Third Place stores, Starbucks China App, Starbucks Now (啡快), Starbucks Delivers (专星送), and Online Coffee Mall."
    )


class ABTestPlan(BaseModel):
    control_hook: str = Field(description="Control creative hook / messaging angle (Version A).")
    variant_hook: str = Field(description="Challenger creative hook / messaging angle (Version B).")
    hypothesis: str = Field(description="Clear testable CRM hypothesis explaining why Variant B may outperform Control A for this RFM segment.")
    success_metric: str = Field(description="Primary quantitative KPI used to declare a statistical winner.")


class CRMBlueprint(BaseModel):
    four_ps: FourPs = Field(description="Structured 4Ps marketing mix tailored to the selected drink and RFM segment.")
    campaign_period: str = Field(description="Recommended launch window and cadence (e.g., '2-Week Seasonal Burst (14 Days)').")
    primary_kpis: List[str] = Field(
        description="Exactly 3 concrete KPIs matched to the RFM segment (Prospect: CPA, ROAS, Mini Program Sign-Up Conversion; Green Star: AOV, Food/Pastry Attach Rate, Repeat Visits; At-Risk Gold: Win-Back Rate, CLV, NPS)."
    )
    ab_test: ABTestPlan = Field(description="Actionable A/B creative test plan.")


class GEOSnippet(BaseModel):
    target_ai_query: str = Field(
        description="Natural question a Chinese/English consumer asks an AI assistant (e.g., 'What is the best winter holiday coffee to order at Starbucks China?')."
    )
    answer_first_summary: str = Field(
        description="2–3 fact-dense, neutral, consumer-safe sentences containing unambiguous brand ('Starbucks China'), hero drink name, grounded anchor pricing (~¥30–¥35), and WeChat Mini Program ('Starbucks Now 啡快' / 'Starbucks Delivers 专星送') ordering entities built to be cited by AI search summaries. Zero competitor names."
    )


class TeardownAnalysis(BaseModel):
    mode_label: str = Field(
        description="Header label: 'Competitor Viral Teardown' in Video Mode or 'Seasonal Market Opportunity Breakdown' in Direct Mode."
    )
    hook_analysis: str = Field(
        description="Competitor's 0-5s viral hook breakdown (Video Mode) or high-impact seasonal attention hook opportunity (Direct Mode)."
    )
    pacing_and_visual_style: str = Field(
        description="Observed editing pacing, camera rhythm, and visual cues (Video Mode) or recommended Douyin/Reels pacing strategy (Direct Mode)."
    )
    offer_and_mechanic: str = Field(
        description="Competitor's promotional offer/conversion mechanic (Video Mode) or Starbucks value-led loyalty mechanic (Direct Mode)."
    )
    strategic_weakness_or_gap: str = Field(
        description="Strategic weakness in competitor's play (e.g., commoditization, low emotional loyalty) or unmet market/craft gap (Direct Mode)."
    )
    starbucks_counter_angle: str = Field(
        description="Internal CRM strategy explaining how Starbucks China (~8,000+ stores under the April 2026 Boyu Capital JV) counters via craft, Third Place warmth, and Rewards exclusivity without price-war discounting."
    )


class ScriptBeat(BaseModel):
    time_range: str = Field(description="Timestamp range, e.g. '0–5s', '5–20s', or '20–30s'.")
    beat_title: str = Field(description="Short title for this beat, e.g. 'Hook', 'Craft & Proof', 'Segment-Specific CTA'.")
    visual_direction: str = Field(description="Detailed visual action, camera movement, and atmosphere.")
    voiceover_or_dialogue: str = Field(description="Spoken script line in the selected Creator Voice and Output Language. Zero competitor brand names.")
    on_screen_text: str = Field(description="Punchy on-screen caption / text overlay. Zero competitor brand names and zero RMB 9.9 discounts.")


class StoryboardShot(BaseModel):
    timestamp: str = Field(description="Shot timing, e.g. '0:00–0:05'.")
    visual_camera_angle: str = Field(description="Shot composition, camera angle, lighting, and movement.")
    voiceover_text_overlay: str = Field(description="Combined spoken line + on-screen text overlay for this shot.")
    aigc_video_prompt: str = Field(
        description="Copy-paste ready English AIGC video generation prompt (for Veo/Kling/Runway) describing subject, lighting, camera motion, and Starbucks aesthetic without any competitor logos."
    )


class DouyinVideoScript(BaseModel):
    hook_0_5s: ScriptBeat = Field(description="0–5s Hook beat designed to stop the scroll immediately.")
    craft_proof_5_20s: ScriptBeat = Field(description="5–20s Craft & Proof beat highlighting espresso craft, sensory richness, customization, or Third Place warmth.")
    cta_20_30s: ScriptBeat = Field(description="20–30s Segment-Specific CTA beat aligned with the chosen Starbucks Rewards RFM segment.")
    storyboard: List[StoryboardShot] = Field(
        description="5 to 6 sequential shots covering 0:00 to 0:30 with timestamps, visual/camera angles, voiceover/overlays, and copy-paste AIGC video prompts."
    )


class XiaohongshuPost(BaseModel):
    title: str = Field(
        description="High-CTR Xiaohongshu (RedNote) title with tasteful emojis, aligned to the selected Creator Voice and Output Language. Never name competitors or RMB 9.9 discounts."
    )
    body_copy: str = Field(
        description="Well-formatted Xiaohongshu body copy with short paragraphs, emojis, sensory storytelling, pastry pairing mention where relevant, and segment-appropriate CTA in the selected Creator Voice."
    )
    ordering_or_rewards_callout: str = Field(
        description="Concise pinned callout box with the exact drink customization formula, pastry pairing suggestion, or Starbucks Rewards / 啡快 CTA."
    )
    short_tail_hashtags: List[str] = Field(
        description="4 to 6 high-volume short-tail SEO hashtags (each starting with #), e.g. #星巴克 #StarbucksChina."
    )
    long_tail_hashtags: List[str] = Field(
        description="5 to 8 high-intent long-tail SEO hashtags (each starting with #), e.g. #星巴克太妃榛果拿铁隐藏喝法 #打工人冬日治愈咖啡."
    )
    cover_image_prompt: str = Field(
        description=(
            "Detailed English visual prompt optimized for 3:4 portrait Xiaohongshu cover image generation: "
            "editorial café photography, warm sunlit pine-green and cream Starbucks atmosphere, hero cup close-up, "
            "shallow depth of field, clean upper negative space for RedNote cover framing, no garbled text, no competitor branding."
        )
    )


class GuardrailCheck(BaseModel):
    no_9_9_discount: bool = Field(description="True confirming zero RMB 9.9 or cheap price-war discounting appears in consumer copy.")
    no_competitor_named_in_consumer_copy: bool = Field(
        description="True confirming no competitor brand name (e.g., Luckin) appears in any consumer-facing script, overlay, title, body copy, hashtag, GEO summary, WeCom push, or image prompt."
    )
    pricing_and_claims_grounded: bool = Field(
        description="True confirming no fabricated prices, fake promo codes, or unverified health claims appear."
    )
    wechat_pipl_opt_in_compliant: bool = Field(
        description="True confirming WeChat Mini Program and WeCom push CTAs respect China PIPL opt-in privacy (separate user consent for location/personalized offers, polite frequency, zero spam)."
    )
    compliance_note: str = Field(description="One-sentence summary of how the campaign stayed strictly on-brand and PIPL-compliant for Starbucks China.")


class CampaignOutput(BaseModel):
    campaign_title: str = Field(description="Memorable internal CRM campaign name summarizing drink, segment, and creator voice.")
    crm_blueprint: CRMBlueprint = Field(description="Structured 4Ps, campaign period, 3 segment-matched KPIs, and A/B test plan.")
    teardown: TeardownAnalysis = Field(description="Internal strategic teardown (competitor video breakdown or seasonal market opportunity breakdown).")
    video_script: DouyinVideoScript = Field(description="Complete 30-second Douyin / Instagram Reels script and shot-by-shot storyboard.")
    xiaohongshu: XiaohongshuPost = Field(description="Complete Xiaohongshu (RedNote) seeding post, SEO hashtag split, and 3:4 cover image prompt.")
    geo_snippet: GEOSnippet = Field(description="Generative Engine Optimization (GEO) target AI query and fact-dense answer-first citation snippet.")
    wecom_push_copy: str = Field(
        description="Short, warm, non-spammy 1-on-1 WeCom / WeChat Mini Program trigger message personalized to the selected RFM tier, respecting explicit PIPL opt-in consent and zero competitor naming."
    )
    guardrail_self_check: GuardrailCheck = Field(description="Brand guardrail and PIPL privacy compliance verification.")


# ---------------------------------------------------------------------------
# 7. Prompt Assembly (5-Step Prompting Framework)
# ---------------------------------------------------------------------------


def build_campaign_prompt(
    mode: str,
    segment_key: str,
    voice_key: str,
    output_language: str,
    drink_name: Optional[str] = None,
    notes: Optional[str] = None,
    has_video: bool = False,
) -> str:
    """
    Assemble the grounded CRM prompt using the 5-step prompting framework:
      1. Role
      2. Context & Knowledge Base
      3. Goal
      4. Format & Style
      5. Constraints
    """
    segment = REWARDS_SEGMENTS[segment_key]
    voice = CREATOR_VOICES[voice_key]

    drink_detail_block = ""
    if drink_name and drink_name in STARBUCKS_KB["featured_drinks"]:
        d_info = STARBUCKS_KB["featured_drinks"][drink_name]
        custom_tips = "; ".join(d_info["barista_customizations"])
        drink_detail_block = (
            f"- **Selected Hero Beverage:** {drink_name}\n"
            f"  - Flavor Profile: {d_info['flavor_profile']}\n"
            f"  - Seasonal Positioning: {d_info['seasonal_positioning']}\n"
            f"  - Approved Barista Customizations: {custom_tips}"
        )
    elif drink_name:
        drink_detail_block = (
            f"- **Selected Hero Beverage (Custom Entry):** {drink_name}\n"
            f"  - Treat this as an authentic Starbucks China handcrafted beverage; highlight espresso craft, "
            f"barista customization, and sensory warmth without inventing fake prices or unverified health claims."
        )
    else:
        featured_list = ", ".join(STARBUCKS_KB["featured_drinks"].keys())
        drink_detail_block = (
            f"- **Recommended Starbucks China Counter Beverage Pool:** {featured_list}\n"
            f"  - Select the single best-fitting Starbucks China featured beverage to counter the uploaded competitor video."
        )

    pairing_lines = "\n".join(
        f"  - {item}: {desc}" for item, desc in STARBUCKS_KB["food_pairings"].items()
    )
    pricing_lines = "\n".join(
        f"  - {item}: {price}" for item, price in STARBUCKS_KB["anchor_pricing"].items()
    )
    channel_lines = "\n".join(
        f"  - {ch}: {desc}" for ch, desc in STARBUCKS_KB["channels"].items()
    )
    guardrail_lines = "\n".join(
        f"  - {rule}" for rule in STARBUCKS_KB["strict_guardrails"]
    )

    if mode == "video":
        mode_context = (
            "**Input Mode:** Mode 1 — Competitor Video Counter-Strike.\n"
            "A competitor short-form promotional video has been uploaded alongside this prompt. "
            "First dissect the uploaded video's exact visual hook, editing pacing, offer mechanic, "
            "and strategic weakness inside the internal `teardown` section (using `mode_label`: 'Competitor Viral Teardown'). "
            "Then craft a superior Starbucks China counter-campaign that beats the competitor on coffee craft, "
            "emotional resonance, and Rewards loyalty value — without ever naming the competitor in consumer-facing copy."
            if has_video
            else "**Input Mode:** Mode 1 — Competitor Video Counter-Strike (text notes context)."
        )
    else:
        mode_context = (
            "**Input Mode:** Mode 2 — Direct Seasonal Launch (No competitor video uploaded).\n"
            "Inside the internal `teardown` section (using `mode_label`: 'Seasonal Market Opportunity Breakdown'), "
            "analyze the seasonal attention hook opportunity, optimal Douyin/Reels visual pacing, "
            "value-led Starbucks Rewards conversion mechanic, and market gap vs. mass-discount coffee chains."
        )

    extra_notes = notes.strip() if notes and notes.strip() else "None provided — rely on Starbucks China CRM best practices."

    language_instruction = {
        "English": (
            "Write all strategic analysis, 4Ps blueprint, A/B test, video scripts, voiceovers, text overlays, "
            "Xiaohongshu title/body, GEO snippet, WeCom push, and hashtags in polished natural English "
            "(you may keep authentic Starbucks China channel terms like `啡快` or `专星送` in parentheses for local accuracy). "
            "Keep `aigc_video_prompt` and `cover_image_prompt` in English."
        ),
        "Chinese (简体中文)": (
            "Write all strategic analysis, 4Ps blueprint, A/B test, video scripts, voiceovers, text overlays, "
            "Xiaohongshu title/body, GEO snippet, WeCom push, and SEO hashtags in idiomatic Mainland China Simplified Chinese (简体中文). "
            "Keep `aigc_video_prompt` and `cover_image_prompt` in detailed English for best AIGC model fidelity."
        ),
        "Bilingual (EN + 中文)": (
            "Write strategic analysis, 4Ps blueprint, A/B test, video script beats, storyboard voiceover/overlays, "
            "Xiaohongshu copy, GEO snippet, and WeCom push copy in clear Bilingual format "
            "(Simplified Chinese paired naturally with English, e.g., Chinese primary line + English line). "
            "Include both Chinese and English SEO hashtags across short-tail and long-tail lists. "
            "Keep `aigc_video_prompt` and `cover_image_prompt` in detailed English."
        ),
    }.get(output_language, "Write in English.")

    prompt = f"""### 1. Role
You are a Senior Agentic CRM Strategist & Omnichannel Creative Director for **Starbucks China (星巴克中国)** specializing in high-LTV retention, Starbucks Rewards RFM lifecycle marketing, 4Ps campaign architecture, A/B experimentation, Douyin/Reels short-form storytelling, Xiaohongshu (RedNote) KOL/KOS/KOC seeding, and Generative Engine Optimization (GEO).

### 2. Context & Knowledge Base
**2026 China Market Context:**
- {STARBUCKS_KB['market_context_2026']}

{mode_context}

**Target Starbucks Rewards Lifecycle Segment (RFM):**
- **Segment:** {segment_key}
- **RFM Profile:** {segment['rfm_logic']}
- **Audience Mindset:** {segment['audience_mindset']}
- **Strategic Focus:** {segment['strategic_focus']}
- **Mandatory CTA Direction:** {segment['cta_requirement']}
- **Priority Channels:** {segment['primary_channels']}
- **Required Segment Primary KPIs (use these 3 KPIs in `crm_blueprint.primary_kpis`):** {segment['kpi_targets']}

**Assigned Creator Voice (Content Persona):**
- **Creator Tier:** {voice_key} ({voice['role_title']})
- **Funnel Role:** {voice['funnel_role']}
- **Tone & Style:** {voice['tone_and_style']}
- **Hook Pattern:** {voice['hook_pattern']}
- **Xiaohongshu Formatting Style:** {voice['xiaohongshu_formatting']}

**Starbucks China Grounding Knowledge Base:**
{drink_detail_block}
- **Approved Pastry / Food Cross-Sell Pairings (use to lift basket AOV & attach rate):**
{pairing_lines}
- **Anchor Pricing Reference (do not invent other prices):**
{pricing_lines}
- **Official Channels & Loyalty Ecosystem:**
{channel_lines}
- **Privacy & Consent Governance:**
  - {STARBUCKS_KB['privacy_and_consent_rule']}

**Campaign Angle / Occasion Notes from Marketer:**
- {extra_notes}

### 3. Goal
Generate a cohesive, immediately executable Starbucks China CRM campaign package containing:
1. **CRM Blueprint (`crm_blueprint`)**: Explicit **4Ps** (`product`, `price`, `promotion`, `place`), recommended `campaign_period`, exactly **3 segment-matched `primary_kpis`** ({segment['kpi_targets']}), and an actionable **`ab_test`** (`control_hook`, `variant_hook`, `hypothesis`, `success_metric`).
2. **Strategic Teardown / Market Opportunity Card (`teardown`)** diagnosing how Starbucks China (~8,000+ stores under the April 2026 Boyu Capital JV) wins this segment without entering a price war.
3. **30-Second Douyin / Reels Video Script (`video_script`)** structured cleanly into `0–5s Hook`, `5–20s Craft & Proof`, and `20–30s Segment-Specific CTA`, plus a **5–6 shot Storyboard** with copy-paste AIGC video prompts.
4. **Xiaohongshu (RedNote) Seeding Post (`xiaohongshu`)** written authentically in the **{voice_key}** voice, with a clickable emoji title, scannable body copy, actionable ordering/pairing/Rewards callout, separated **Short-Tail** vs. **Long-Tail SEO Hashtags**, and a **3:4 Portrait Cover Image Prompt**.
5. **GEO Readiness Snippet (`geo_snippet`)**: A natural consumer AI search query (`target_ai_query`) + a 2–3 sentence `answer_first_summary` packed with unambiguous Starbucks China brand, drink, anchor price (~¥30–¥35), and WeChat Mini Program (`Starbucks Now 啡快` / `Starbucks Delivers 专星送`) entities designed for AI search citation.
6. **1-on-1 WeCom / WeChat Mini Program Push Copy (`wecom_push_copy`)**: A concise, warm, non-spammy opt-in trigger message tailored to `{segment_key}` respecting China PIPL privacy consent.
7. **Guardrail & Privacy Self-Check (`guardrail_self_check`)** verifying 100% brand and PIPL opt-in compliance.

### 4. Format & Style
- **Output Language Rule:** {language_instruction}
- **Structured Output:** Return ONLY valid JSON strictly matching the supplied Pydantic `CampaignOutput` schema so every tab in the Streamlit studio renders cleanly with zero parsing errors.
- Make the Douyin script punchy, visual, and realistic to shoot or generate within exactly 30 seconds.
- Make the Xiaohongshu post genuinely native to RedNote (short scannable paragraphs, natural emojis, authentic `{voice_key}` perspective — NOT robotic ad copy).
- Ensure `cover_image_prompt` specifies a clean 3:4 vertical editorial coffee photo with warm Starbucks pine-green/cream tones, hero beverage craft details, and zero garbled text overlays.

### 5. Constraints
{guardrail_lines}
- Distinguish clearly between the internal strategic sections (`teardown`, `crm_blueprint`) and ALL consumer-facing fields (`video_script`, `storyboard`, `xiaohongshu`, `geo_snippet`, `wecom_push_copy`): consumer-facing content MUST NEVER mention any competitor brand name or RMB 9.9 pricing.
- `wecom_push_copy` MUST read like a respectful opt-in member service message (never urgent spam) and explicitly respect separate user consent for location or personalized offers.
- Every CTA MUST explicitly match the `{segment_key}` RFM lifecycle objective and official Starbucks China channels (`Starbucks China App`, `Starbucks Now 啡快`, `Starbucks Delivers 专星送`, `Online Coffee Mall`, or `Starbucks Reserve` where relevant).
"""
    return prompt.strip()


def get_knowledge_base_preview_markdown() -> str:
    """Return a readable Markdown summary of the grounding knowledge base for the Streamlit sidebar."""
    drinks_md = "\n".join(
        f"- **{name}**: {info['seasonal_positioning']}"
        for name, info in STARBUCKS_KB["featured_drinks"].items()
    )
    pairings_md = "\n".join(
        f"- **{item}**: {desc}"
        for item, desc in STARBUCKS_KB["food_pairings"].items()
    )
    pricing_md = "\n".join(
        f"- **{item}**: {price}"
        for item, price in STARBUCKS_KB["anchor_pricing"].items()
    )
    channels_md = "\n".join(
        f"- **{ch}**: {desc}"
        for ch, desc in STARBUCKS_KB["channels"].items()
    )
    guardrails_md = "\n".join(
        f"- {rule}" for rule in STARBUCKS_KB["strict_guardrails"]
    )
    return f"""**2026 Market Context**
- {STARBUCKS_KB['market_context_2026']}

**Featured / Seasonal Drinks**
{drinks_md}

**Pastry & Food Cross-Sell Pairings**
{pairings_md}

**Anchor Pricing Reference**
{pricing_md}

**Official Channels & Rewards**
{channels_md}

**China Privacy & WeChat Consent**
- {STARBUCKS_KB['privacy_and_consent_rule']}

**Strict Brand Guardrails**
{guardrails_md}
"""
