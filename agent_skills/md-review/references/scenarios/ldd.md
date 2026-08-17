# LDD Scenario Checklist — Level Design Document

Enabled when the scenario parameter is `ldd`. Checks whether the level design document contains the following content and assesses its completeness.

## Core Questions (editors must address)
1. Are the level layout and player flow reasonable?
2. Do the challenges, pacing, and narrative elements within the level match?
3. Are there level design patterns and metrics?

## Key Focus
Level layout + player paths + challenge configuration + pacing control
- Includes: **Level List**, **Scene Interaction Elements List**

## Required Content (deduct if missing)

### Level Design
- [ ] **Level List**: Are all levels numbered (L-1, L-2...), with objectives/theme/location?
- [ ] **Level Layout**: Is each level's spatial layout/structure described (or illustrated)?
- [ ] **Player Path**: Is the player's completion path/route clear (start → objective → end)?
- [ ] **Scene Interaction Elements List**: Are the interactive elements within the level (mechanisms/items/enemies/NPCs) listed?

### Challenges and Pacing
- [ ] **Challenge Configuration**: Are the challenge types/difficulty gradients within the level configured?
- [ ] **Pacing Control**: Is the level's tension-and-release pacing (alternating intense combat and calm exploration) designed?
- [ ] **Difficulty Curve**: Is the difficulty progression across levels reasonable?
- [ ] **Reward Distribution**: Is the placement of rewards/incentive points reasonable?

### Narrative and Theme
- [ ] **Narrative Elements**: Do the in-level narrative elements (dialogue/cutscenes/environmental storytelling) match the level objectives?
- [ ] **Thematic Consistency**: Is the level's visuals/atmosphere consistent with the game's overall theme?

### Metrics and Patterns
- [ ] **Design Patterns**: Is there an explanation of level design patterns (e.g., linear/open-world/hub-based)?
- [ ] **Metrics**: Are metric indicators defined (completion time/death rate/exploration coverage)?
- [ ] **Acceptance Criteria**: Are testable completion criteria defined (QA can determine pass/fail)?
- [ ] **Test Cases**: Do the level's key flows have test cases (player behavior → expected result)?

### 5W1H Check (level design context)
- [ ] **Who**: Who does the player play as / face in the level?
- [ ] **What**: What does the player do in the level (objectives/tasks)?
- [ ] **When**: Where in the game flow does the level sit / its unlock conditions?
- [ ] **Where**: In what scenes/regions does the level take place?
- [ ] **Why**: What is the purpose of the level (tutorial/climax/turning point)?
- [ ] **How**: How does the player complete the level (paths/solutions)?

## Completeness Issue Markers
- Levels without layout descriptions (only textual objectives)
- Challenges and pacing not designed (monotonous levels)
- No metrics (unable to assess level quality)

## Scoring Guide
| Finding | Deduction |
|---|---|
| Level list missing | -15 |
| Level layout not described | -12 |
| Player path unclear | -12 |
| Challenge configuration missing | -10 |
| Pacing control not designed | -10 |
| Unreasonable difficulty curve | -8 |
| Narrative and level mismatch | -8 |
| Missing metrics | -12 |
| Missing acceptance criteria | -10 |
| Missing test cases | -10 |
