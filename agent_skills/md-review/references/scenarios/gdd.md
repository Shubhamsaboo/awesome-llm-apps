# GDD Scenario Checklist — Game Design Document

Enabled when the scenario parameter is `gdd`. Checks whether the game design document contains the following content and assesses its completeness.

## Core Questions (editors must address)
1. Is the core experience clearly defined (what the player feels)?
2. Is the core gameplay loop (Core Loop) visualized?
3. Are the rules and interactions of each system (economy, combat, etc.) clear?

## Key Focus
Game overview + core gameplay + system mechanics + narrative and world-building
- Includes: **Core Mechanics List**, **Game Systems List**

## Required Content (deduct if missing)

### Core Design
- [ ] **Core Gameplay Loop**: Is the player's core loop from start to finish clear (e.g., collect → craft → combat → upgrade → collect)?
- [ ] **Player Fantasy**: Is the core experience players should feel described?
- [ ] **Goals and Win Conditions**: Are the game objectives and win/loss conditions defined?
- [ ] **Target Audience**: Is the target player group (age/preferences/platform) clear?

### Systems and Mechanics
- [ ] **Core Mechanics**: Are the main gameplay mechanics defined in detail (operation methods, rules, feedback)?
- [ ] **Numerical Design**: Do key values (health/damage/speed/probability) have definitions and balancing rationale?
- [ ] **Formulas**: Are numerical formulas complete (variable definitions, value ranges, example calculations)?
- [ ] **Edge Cases**: Are the boundary conditions of every mechanism described, at minimum:
  - **Death / Respawn / Failure determination**: how HP is deducted, when failure is decided, what state the player respawns into, and whether respawning depends on rules defined elsewhere (an undeclared death rule underneath a respawn/continue feature is a bug source)
  - **Fail / retry / replay behavior** for quests, levels and minigames
  - **Extreme values**: max/min caps, overflow/underflow, zero-input handling in formulas
  - **Concurrent state conflicts**: save/load, offline income, shared world state
- [ ] **Inter-system Dependencies**: Is the dependency of system A on system B declared bidirectionally?

### Content Scope
- [ ] **Quest List**: Is the list of in-game quests/levels/activities complete (quantities, unlock conditions, rewards)?
- [ ] **Content List**: Are items/characters/enemies/maps listed?
- [ ] **Economy System**: Is the design of currencies/resources/exchange relationships complete?

### Experience and Quality
- [ ] **Test Cases**: Do core mechanics have executable test cases (input → expected output)?
- [ ] **Acceptance Criteria**: Does each system have testable completion criteria (QA can determine pass/fail)?
- [ ] **Tuning Knobs**: Are configurable values externalized (not hardcoded)?
- [ ] **Balance**: Are there obvious numerical imbalances (a certain strategy is always optimal)?

### 5W1H Check (game design context)
- [ ] **Who**: Who is the player (character/faction)? Who is the enemy?
- [ ] **What**: What does the player do? What are the core actions?
- [ ] **When**: When are combat/quests/systems triggered?
- [ ] **Where**: Where do scenes/maps take place?
- [ ] **Why**: Why does the player do it (motivations/rewards)?
- [ ] **How**: How is it operated? How is it implemented?

## Completeness Issue Markers
- Undefined terms (e.g., "combo system" without a definition)
- Missing values ("high damage" instead of specific numbers)
- Incomplete markers (TODO/TBD)
- Mechanics referenced but their boundary behavior undefined (e.g., a respawn/continue feature with no stated death or failure rules)

## Scoring Guide
| Finding | Deduction |
|---|---|
| Missing core gameplay loop | -15 |
| Missing player fantasy | -10 |
| Key values not defined | -5 per occurrence |
| Missing/incomplete formulas | -10 |
| Missing test cases | -10 |
| Missing acceptance criteria | -10 |
| Incomplete quest/content lists | -5 |
| Edge cases not handled | -3 per occurrence |
| Death/respawn/failure rules missing or under-defined | -5 per occurrence |
| One-way system dependency | -5 |
| Obvious numerical imbalance | -8 |
