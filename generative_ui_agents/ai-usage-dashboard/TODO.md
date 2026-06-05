# AI Usage Dashboard — Wishlist

## What Works Today
- [x] Agent queries real SQLite DB (1 account, ~137K usage events, 6 invoices)
- [x] Natural language → SQL → structured results
- [ ] Auto-loads dashboard on page open (not implemented — no mount trigger in page.tsx)
- [x] Canvas renders: table, metric cards, grouped summary, detail card, mutation preview
- [x] Status/type badges with colors
- [x] Expandable rows with detail panel
- [x] Inline editing (click field → edit → agent proposes mutation via chat message)
- [x] CopilotKit: useAgent, useAgentContext, useFrontendTool, useRenderTool, useHumanInTheLoop, useConfigureSuggestions (LLM-generated), showDevConsole
- [x] Frontend tools: highlightRow, expandRow, scrollToTop, exportCSV
- [x] Custom tool rendering in chat (query cards, mutation cards)
- [x] Write flow via chat ("Change X status to Y")
- [x] SQL trust model (statement allowlist, PK-scoped, parameterized, read-only connection)

## Must Fix
- [ ] Inline edit click propagation — clicking a field in expanded detail sometimes doesn't trigger edit
- [ ] Turbopack doesn't work — need webpack (already switched, but note in README)
- [ ] A2UI catalog error in chat — suppress or fix the catalog ID mismatch
- [ ] Test write flow end-to-end (propose → confirm → execute → re-render)
- [ ] Verify `sendTextMessage` exists on the agent object (auto-load on mount may silently fail)

## UI Polish — Make It Feel Like an Admin Dashboard
- [ ] Richer default view — show summary metrics at top (total accounts, total MRR, overdue invoices, accounts at risk) above the table
- [ ] Usage indicators on account rows — API call trend, storage %, seats — like Salesdash's 30/60/90 day columns
- [ ] Alert badges on accounts — "Credit Usage: 90%", "Consumption Spike" — not just status colors
- [ ] Sidebar navigation (or at least tab-like switching between Accounts / Usage / Invoices views)
- [ ] Better empty/loading state with skeleton instead of spinner
- [ ] User cards on hover — owner/CSM info popup when hovering over a name
- [ ] Filter chips at the top — quick filters for type, status, owner without typing

## Smarter Views (Agent Picks the Right Layout)
- [ ] Timeline view — when data has period/date columns, show chronologically
- [ ] Comparison view — when 2-3 items are compared side by side
- [ ] Detail + related data — expanding an account row shows its usage + invoices, not just the same columns
- [ ] The agent should hint the view type in its response (table/grouped/timeline/comparison) based on what the user asked

## CopilotKit Features Still Unused
- [ ] useInterrupt — for LangGraph interrupt-based HITL (cleaner than chat confirmation)
- [ ] useRenderActivityMessage — progress indicators for long queries
- [ ] useAttachments — upload CSV to seed/import data
- [ ] useComponent — register standalone components the agent can place
- [ ] A2UI in canvas — agent-generated layouts beyond the state-driven rendering
- [ ] Thread persistence — conversation history across sessions (built-in, just needs mentioning)
- [ ] Multiple agents — separate query agent vs edit agent

## README
- [ ] Update README with current CopilotKit features used (expanded list)
- [ ] Add screenshots/video demo
- [ ] Tell the thesis story: "Every dashboard is pre-translated questions. This removes the middleman."
- [ ] Note the Turbopack issue and webpack requirement

## Product Ideas (Not for This PR)
- [ ] Saved views — user saves a query as a named view, runs without LLM next time
- [ ] Shared views — team members can adopt each other's saved views
- [ ] Permissions — role-based access to tables/columns/write operations
- [ ] Slack alerts — push notifications with embedded dashboard previews and action buttons
- [ ] Self-improving UI — track which customizations users make, promote popular ones to defaults
- [ ] Feature request auto-generation — when the agent can't do something, auto-log it as a feature request

## Dashboard Screens to Support (Paid.ai parity + more)
The agent should render the right screen type based on what the user asks. Standard SaaS admin views:

- [ ] **Accounts table** — name, type, status, owner, CSM, MRR (done, but needs usage indicators)
- [ ] **Account detail** — single account with all fields + related usage + invoices in one view
- [ ] **Usage table** — events by account, metric, period, value, totals (data exists, needs good rendering)
- [ ] **Usage drill-down** — single account's usage over time, by metric
- [ ] **Invoice table** — account, amount, status, due date, paid date
- [ ] **Invoice status overview** — grouped by status (Paid/Overdue/Draft/Void) with counts and totals
- [ ] **Payments summary** — total paid, total overdue, avg time to pay
- [ ] **Top accounts by metric** — ranked list (top by MRR, top by API usage, top by overdue amount)
- [ ] **Credit management** — add/remove credits, view credit balance, usage vs allocation (needs schema addition)
- [ ] **Customer contacts** — owner + CSM as a contacts view (data exists in accounts table)

## Data Schema Additions (for richer demo)
- [ ] Credits table — account_id, credit_type, amount, balance, allocated_at, expires_at
- [ ] Events/activity log — account_id, event_type, description, timestamp (account created, plan changed, invoice paid, etc.)

## Data to Incorporate
- [ ] (Kat has additional reference data — continue in AM)
