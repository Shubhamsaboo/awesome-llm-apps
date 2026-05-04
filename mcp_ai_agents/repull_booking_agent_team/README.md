# 🏠 Repull Booking Agent Team

A multi-agent vacation-rental assistant powered by the [Repull MCP server](https://repull.dev/docs/mcp-server). One Repull API key fans out to 50+ PMS platforms and the major OTAs (Airbnb, Booking.com, VRBO, Plumguide), so the agents can read reservations, properties, listings, guests, and conversations across an entire short-term rental portfolio through a single MCP connection.

The team is built on [Agno](https://github.com/agno-agi/agno) and ships three specialists plus a coordinator:

- **Listing Specialist** — properties and listings catalog (`repull_list_properties`, `repull_list_listings`, `repull_list_airbnb_listings`)
- **Reservation Specialist** — bookings, guests, and conversations (`repull_list_reservations`, `repull_get_reservation`, `repull_list_guests`, `repull_list_conversations`)
- **Connections Specialist** — connected channels and plan info (`repull_whoami`, `repull_list_connections`, `repull_list_connect_providers`)
- **Coordinator** routes user queries to the right specialist and stitches the final answer together.

## Features

- 🧭 **Routing** — the coordinator decides which specialist handles each ask. Account-level questions ("what's connected?") go to Connections; reservation lookups go to Reservations; listing catalog work goes to Listings.
- 🔍 **Discovery built in** — the MCP server exposes `repull_list_endpoints` and `repull_get_docs` so the agents can self-serve when they hit something they don't know.
- 📑 **Cursor pagination** — list tools accept `cursor`. The agents are instructed to fetch one page, summarize, and ask before paging further (LLMs do better when paging is explicit).
- 🛡️ **Read-only by design** — `@repull/mcp` v0.2 deliberately omits write tools. An LLM that "tidies up" a live booking calendar is a footgun. Mutating tools will land in a follow-up release with explicit per-tool opt-in.

## What you'll need

1. **A Repull API key.** Sign up at [repull.dev/dashboard](https://repull.dev/dashboard) — test keys look like `sk_test_...`. The MCP server respects whichever you pass.
2. **An OpenAI API key.** Get one at [platform.openai.com/api-keys](https://platform.openai.com/api-keys). The example uses `gpt-4o`. Prefer Anthropic? Swap `OpenAIChat` for `Claude` from `agno.models.anthropic` and set `ANTHROPIC_API_KEY` — the rest of the team wiring is identical.
3. **Node.js 18+** on your `PATH`. The MCP server is `@repull/mcp` on npm and is launched via `npx -y @repull/mcp`. Verify with `node --version` and `npx --version`.

> Markets / pricing-intel endpoints exist on the Repull API, but `@repull/mcp` v0.2 does not expose them yet. The agent will pick them up automatically once they're added — `repull_list_endpoints` is how it discovers what's available, so no agent code change is needed when new tools land.

## Run it

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/mcp_ai_agents/repull_booking_agent_team

pip install -r requirements.txt

cp .env.example .env       # then edit .env with your keys
streamlit run app.py
```

Open the browser tab Streamlit prints (default `http://localhost:8501`). If you skipped the `.env` step, you can paste keys into the sidebar at runtime instead.

## Try these prompts

| Prompt | What the team does |
|---|---|
| `What's connected to my account?` | Connections Specialist calls `repull_whoami` and reports plan + connected channels. |
| `Show me upcoming reservations on Airbnb.` | Reservation Specialist calls `repull_list_reservations` with `platform=airbnb` and `check_in_after=<today>`. |
| `List my Airbnb listings, then find this week's bookings for the first one.` | Listing Specialist runs `repull_list_airbnb_listings`; Reservation Specialist follows up with a filtered `repull_list_reservations`. |
| `What can Repull actually do?` | Connections Specialist falls back to `repull_list_endpoints` for discovery. |
| `Who is the guest on reservation 123, and what was their last message?` | Reservation Specialist chains `repull_get_reservation` → `repull_list_conversations` → `repull_list_conversation_messages`. |

### Example session

```
You: What's connected to my account?

Routed to: Connections Specialist
Tool calls: repull_whoami

> Workspace: "Sample Vacation Rentals" — Pro plan
> Connected channels: Airbnb (active), Booking.com (active), Hostaway (PMS)
> Disconnected: VRBO, Plumguide
```

```
You: Show me 5 upcoming Airbnb reservations.

Routed to: Reservation Specialist
Tool calls: repull_list_reservations(limit=5, platform=airbnb, check_in_after=2026-05-03)

> | id   | guest      | check-in   | nights | total |
> |------|------------|------------|--------|-------|
> | 9123 | Alex K.    | 2026-05-09 | 3      | $612  |
> | 9118 | Diana R.   | 2026-05-11 | 7      | $1,540|
> ...
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Error: spawn npx ENOENT` | Install Node.js 18+ and re-open your shell. |
| `unauthorized (401)` | The `REPULL_API_KEY` is missing or invalid. Re-check it at [repull.dev/dashboard](https://repull.dev/dashboard). |
| `forbidden (403)` on a specific tool | The key is valid but the workspace doesn't have access. Run "what's connected?" first to see plan + entitlements. |
| `provider_unavailable (503)` | A downstream PMS/OTA is having a moment. Try again in a minute; the error envelope includes a `request_id` for support. |
| Agent invents a listing or channel | Re-run with the prompt "ground every claim in tool output, do not fabricate" — and file an issue, that's a real bug. |

## Links

- 📦 npm package: [`@repull/mcp`](https://www.npmjs.com/package/@repull/mcp)
- 📚 MCP server docs: [repull.dev/docs/mcp-server](https://repull.dev/docs/mcp-server)
- 🌐 Repull docs: [repull.dev/docs](https://repull.dev/docs)
- 🤖 Agno framework: [github.com/agno-agi/agno](https://github.com/agno-agi/agno)
- 🛠️ MCP spec: [modelcontextprotocol.io](https://modelcontextprotocol.io)

## License

Same as the parent repo. The MCP server itself is MIT-licensed.
