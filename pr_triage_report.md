# PR Triage Report, awesome-llm-apps

Date: 2026-10-13. Reviewed 21 open PRs (draft #1223 skipped). Read-only: nothing was posted to GitHub. These are recommendations for Shubham, not actions taken.

Each new-app PR was checked against the acceptance checklist: (1) runnable code in its own folder, (2) uses an LLM, (3) self-contained tutorial not promotion, (4) compatible license. Any failure means reject. Existing review comments were checked on every PR.

## Needs Shubham's decision (flagged)

### Reject candidates (self-promotion / quality)
- **#1224 Add ai it access request agent** (harishrajora): REJECT. Agent itself is reasonable (Agno + Gemini, in-code policy re-check), but roughly half the README is a marketing walkthrough for "Rook" (TestMu AI / LambdaTest), requiring a paid account and credits. Author self-identifies as "an official from TestMu AI." Also ships an intentional approval-bypass defect gated behind DEMO_DEFECT=1 purely to demo Rook. Fails checklist item 3.
- **#1213 Add AI Novel Writing Agent Team** (jiawood2006): REJECT. README is entirely in Chinese and describes the PR as a trimmed-down version of the author's own separate repo (novel-agent-pipeline), which it links repeatedly. The "agents" are prompt-builder dataclasses in a plain loop, the gate/editor scoring is pure-Python regex heuristics, and the only tested path (--dry-run) makes no LLM call. Fails item 3, weak on item 2.
- **#1208 feat(agent_skills): pdf-translate skill** (lxsssssss): REJECT-leaning. README points to the author's own external repo as source/maintained-at (self-promotion). CI failing. render_pdf.py hardcodes channel="msedge" (needs Microsoft Edge installed). audit_pdf.py logic is hardcoded to Chinese tender/contract documents, not a general tutorial. Translation is delegated to the host agent, no LLM call in shipped code (borderline item 2).
- **#1232 Add Human-in-the-Loop Approval Agent (Google ADK)** (solara-associates): NEEDS-WORK, leaning reject. Genuinely solid engineering (real ADK confirmation flow, tamper-evident audit chain, 9 offline tests). But the README thesis showcases the author's own VAID credential library (vaid-mint PyPI, same org), which is a hard dependency. Acceptable only if VAID is dropped or made clearly optional rather than central.

### Needs a judgment call
- **#1219 feat(ripple): read TYPESAFE_BASE_URL** (SamratDuttaOfficial): Technically fine, backwards-compatible, has a test. But the PR body and new README row plug "WaterSheep," a self-hosted server the author maintains. Self-promotion judgment call.
- **#1229 docs: add contribution guide** (harzeezco): A real, accurate 19-line CONTRIBUTING.md, not link-only or self-promo. BUT you previously closed a CONTRIBUTING.md PR (#829) with "review stays case-by-case." Your call on whether to reverse that stance.
- **#1236 fix(agentic_rag_math_agent)** (prince0310, Bugs 9+10 of #1194): Fix looks correct but broad (few-shot guardrail + web fallback + benchmark matcher) and it changes a published benchmark accuracy number (66% to 46%). Worth eyeballing the rescoring claim.
- **#1225 fix(ai_deep_research_agent): Firecrawl v4** (JuampiHernandez, Firecrawl team): Correct and necessary API migration, but it redesigns the agent's research behavior (self-driven multi-search loop) rather than a literal port, and adds an origin tag. Sign off on the approach.

## Needs work (author should fix first)
- **#1187 Task-Scoped Support Agent Team** (aimable100): Accept-quality content (strongest-written of the new apps, --scripted mode runs keyless), passes all four criteria. But it has a merge conflict (needs rebase) and one open review comment from another contributor about idempotency. Do not plain-merge; ask for rebase.
- **#1210 AutoRAG Neon + Gemini variant** (sivalingaamorthy-arch): Passes all four criteria, but model id `gemini-3.5-flash` looks non-existent (will not run as written) and the diff sneaks an unrelated .gitignore entry for a different tutorial. Fix both first.
- **#1220 feat(first-reader): --lang support** (rosh93an): Reasonable feature, English behavior preserved, but it deletes skim.py's shebang, drops trailing newlines (CI unhappy), and silently renames JSON output keys (per100w to per100, words to chars) which could break existing parsers.

## Looks good (clean, in-scope, no outstanding feedback)
- **#1183 work-history MCP tutorial** (louis030195): ACCEPT. Clean, self-contained, tests pass. Successfully reworks the earlier self-promotion rejection (#958): Screenpipe is now one optional capture source, marketing removed. Mergeable clean.
- **#1196 CI catalog lint** (mvanhorn): You already commented this is "good to merge once CI is green against updated main." Author says he rebased (89499b7), regenerated, cleaned the allowlist. Just verify CI green, then merge.
- **#1234 fix(rag_failure_diagnostics_clinic)** (prince0310, Bugs 1+2 of #1194): Small, correct, defensive validation of model reply before saving. LOOKS-GOOD.
- **#1235 fix(ai_agent_governance)** (prince0310, Bugs 3+5+6 of #1194): Clean defensive fixes (endpoint error handling, ast-based arg parsing, headless approval denial). LOOKS-GOOD.
- **#1233 fix(ai-knowledge-explorer)** (Kshitij-ambuskar, Bug 7 of #1194): Correct code-fence helper, de-duplicates logic, includes a test. LOOKS-GOOD.
- **#1226 fix(ai_travel_planner_agent_team): Firecrawl v4 import** (JuampiHernandez): Trivial, obviously-correct one-line import fix. LOOKS-GOOD.
- **#1221 Restrict CORS origins in travel planner backend** (chaarvilakshmisai-oss): Correct, in-scope security fix (replaces wildcard CORS + credentials with an env var). Fixes #1215. LOOKS-GOOD.
- **#1214 pin mcp below v2 for openai remote bridge** (Omarinho12345): Trivial, correct dependency pin that fixes a fresh-install break. LOOKS-GOOD.
- **#1173 fix(agent_skills): preserve quoted paths in commit archaeology** (RaycarlLei): Well-tested bug fix for Git quotePath escaping, adds a regression fixture. Confirm CI green / rebase after maintainer approval. LOOKS-GOOD.

## Notes
- #1234, #1235, #1236 are one author (prince0310) splitting issue #1194 across PRs. #1225/#1226 are both Firecrawl v4 migrations from the Firecrawl team.
- #1223 is a draft, skipped.
- No PR had reviewer-requested-changes blocking it except #1196 (which you raised and the author addressed) and the advisory comment on #1187.
