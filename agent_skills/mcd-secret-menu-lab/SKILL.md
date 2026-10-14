---
name: mcd-secret-menu-lab
description: "Restore viral McDonald's hidden-menu hacks or invent new ones on demand — every recipe is verified in real time against the official McDonald's MCP (live price + official nutrition) and scored on value/health/taste/creativity"
category: productivity
risk: safe
source: community
source_repo: Reak-Z/mcd-secret-menu-lab
source_type: community
date_added: "2026-10-13"
author: Reak-Z
tags: [mcdonalds, hidden-menu, food, recipe, mcp, price-check, nutrition, lifehack]
tools: [claude, cursor]
license: "MIT"
license_source: "https://github.com/Reak-Z/mcd-secret-menu-lab/blob/main/LICENSE"
---

# 麦门隐藏菜单实验室 (McDonald's Secret Menu Lab)

## Overview

A "secret menu" lab built on the official McDonald's China MCP. It does two things: **restores** viral hidden-menu hacks (what to buy, how to assemble, what it tastes like, how much it costs right now), and **invents** new combinations from the user's taste and budget. Every output is grounded in real data — live store menu, real-time pricing, and the official nutrition table — not copied from stale blog posts.

14 recipes are pre-verified (¥10–¥31, with kcal and a light/moderate/indulgent tier). It also runs a personality quiz, a collection ("illustrated guide") system, and a DIY submission leaderboard.

## When to Use This Skill

- Use when the user asks how to recreate a viral McDonald's hack (e.g. "fries dipped in McFlurry")
- Use when the user wants to invent a new combination from taste/budget ("something sweet under ¥15")
- Use when the user needs the real price or calories of a combination before ordering
- Use when the user asks whether a store currently sells a specific item (menus rotate by season)
- Use when the user wants coupon-aware pricing (auto-bind coupons, post-discount best price)
- Use when the user wants to submit their own combo for community verification

## How It Works

### Step 1: Resolve the store and menu
Call `query-nearby-stores` → `query-meals` to get the live menu with `productCode` and current prices. Never assume an item exists; menus rotate seasonally (e.g. the seasonal pie may hide a classic flavor inside its options).

### Step 2: Build or match the recipe
For restorations, match the hack's components to real `productCode`s. For inventions, apply the flavor matrix (sweet/savoury/frozen/crunchy × temperature contrast) and constrain by budget.

### Step 3: Verify with real data
Call `calculate-price` (with `roundList` for option items) and `list-nutrition-foods`. Output the total price, kcal, sodium/protein notes, and a four-dimension scorecard (value × health × taste × creativity).

### Step 4: Deliver
Produce a recipe card: item list with prices → assembly steps → flavor description → one-line counter script ("tell the staff: ...") → health tier.

## Examples

### Example 1: Restore a classic hack
User: "I want to try fries dipped in a McFlurry."
→ Resolve store → 中薯条 (¥14.50) + 经典麦旋风 (¥15.50) → total **¥30.00**, ~555 kcal, tier "indulgent" → card + counter script: "order medium fries and a regular McFlurry, dip while hot."

### Example 2: Invent within a budget
User: "Something new under ¥10, I like cold-sweet."
→ 黑洋酥小圆子风味派 (¥5) + 圆筒冰淇淋 (¥5) = **¥10.00**, ~325 kcal → assembly: crack the pie open, press the cone on top — fire-and-ice contrast.

## Best Practices

- ✅ Always re-verify price and availability at query time — never serve cached prices
- ✅ Always include the health tier and a balancing note for high-kcal results
- ✅ State the store and date of verification in every output
- ❌ Don't fabricate items that aren't in the live menu
- ❌ Don't present invented combos as official McDonald's products

## Limitations

- Prices and availability vary by city/store/season — outputs are verified samples, not guarantees
- Covers McDonald's China only (requires the official MCP token from open.mcd.cn/mcp)
- Nutrition matching uses the official table; unlisted items are marked "reference only"
- This skill does not replace on-site confirmation or personal dietary advice
