"""Repull Booking Agent Team — vacation-rental MCP example.

A multi-agent team that talks to a property manager's vacation-rental data
through the Repull MCP server (`@repull/mcp` on npm). One Repull API key
fans out to 50+ PMS platforms and the major OTAs (Airbnb, Booking.com,
VRBO, Plumguide).

Three specialist personas plus a coordinator:

  - Listing Specialist     -> properties + listings catalog
  - Reservation Specialist -> guest bookings, status, dates, pricing
  - Connections Specialist -> connected channels, plan, what is wired up

Coordinator routes the user query to the right specialist and stitches the
final answer together.

Docs: https://repull.dev/docs/mcp-server
Package: https://www.npmjs.com/package/@repull/mcp
"""

import asyncio
import os
from textwrap import dedent

import streamlit as st
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.mcp import MCPTools
from dotenv import load_dotenv

load_dotenv()


# ---------- UI shell ----------

st.set_page_config(
    page_title="Repull Booking Agent Team",
    page_icon="\U0001f3e0",
    layout="wide",
)

st.title("\U0001f3e0 Repull Booking Agent Team")
st.markdown(
    "A multi-agent vacation-rental assistant powered by the "
    "[Repull MCP server](https://repull.dev/docs/mcp-server). "
    "One API key reads reservations, properties, listings, guests, and "
    "conversations across 50+ PMS platforms and the major OTAs."
)


# ---------- Sidebar config ----------

with st.sidebar:
    st.header("\U0001f511 Configuration")

    repull_key_default = os.getenv("REPULL_API_KEY", "")
    openai_key_default = os.getenv("OPENAI_API_KEY", "")

    repull_key = st.text_input(
        "Repull API Key",
        type="password",
        value=repull_key_default,
        help="Get yours at https://repull.dev/dashboard. Test keys start with `sk_test_`.",
    )
    openai_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=openai_key_default,
        help="Get yours at https://platform.openai.com/api-keys",
    )

    st.markdown("---")
    st.subheader("\U0001f916 Specialists")
    st.markdown(
        "- **Listing Specialist** — properties & listings catalog\n"
        "- **Reservation Specialist** — guest bookings & details\n"
        "- **Connections Specialist** — connected channels & plan info"
    )

    st.markdown("---")
    st.caption(
        "This example uses `@repull/mcp` v0.2 (read-only). "
        "Mutating tools are intentionally not exposed yet — see the "
        "[MCP server docs](https://repull.dev/docs/mcp-server) for why."
    )

    st.markdown("---")
    st.caption(
        "**Heads up:** Markets / pricing-intel endpoints exist on the Repull "
        "API but are not exposed by `@repull/mcp` v0.2. Once they are, the "
        "agent will pick them up automatically via `repull_list_endpoints`."
    )


# ---------- Agent team factory ----------

def build_team(mcp_tools: MCPTools, openai_api_key: str) -> Team:
    """Build the Repull booking agent team around a connected MCP toolset."""

    listing_specialist = Agent(
        name="Listing Specialist",
        role="Property and listings catalog expert",
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        tools=[mcp_tools],
        instructions=dedent(
            """
            You are the Listing Specialist on a vacation-rental ops team.

            Stay in your lane: properties (the underlying PMS records),
            listings (the canonical Repull objects published to channels),
            and the Airbnb-side view of those listings.

            Preferred tools:
              - repull_list_properties          (filter by `provider`)
              - repull_get_property             (by id)
              - repull_list_listings            (canonical Repull listings)
              - repull_list_airbnb_listings     (Airbnb's view)

            Rules:
              - Always paginate explicitly via `cursor`. Do not loop blindly
                — fetch one page, summarize, ask if the user wants more.
              - Quote IDs verbatim so other specialists can re-use them.
              - If a tool returns an error envelope, surface `code`, `fix`,
                and `docs_url` to the user instead of swallowing it.
            """
        ).strip(),
        markdown=True,
    )

    reservation_specialist = Agent(
        name="Reservation Specialist",
        role="Guest reservations and conversations expert",
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        tools=[mcp_tools],
        instructions=dedent(
            """
            You are the Reservation Specialist on a vacation-rental ops team.

            Stay in your lane: reservations across every connected channel,
            guest profiles, and message threads with guests.

            Preferred tools:
              - repull_list_reservations         (filters: status, platform,
                                                  listing_id, check_in_after,
                                                  check_in_before)
              - repull_get_reservation           (full detail by id)
              - repull_list_guests               (cursor paginated)
              - repull_get_guest                 (single guest profile)
              - repull_list_conversations        (message threads)
              - repull_list_conversation_messages

            Rules:
              - When a date range is implied ("this week", "next month"),
                compute the ISO dates and pass them as `check_in_after` /
                `check_in_before` rather than fetching everything and
                filtering client-side.
              - To find a guest's latest thread for a reservation, fetch the
                reservation, pull the guest id, then list conversations and
                messages in two cheap calls — do not scan every message.
              - v0.2 of the MCP server is read-only. If the user asks to
                cancel, modify, refund, or message a guest, explain that
                writes are not exposed yet and point them at the Repull SDK
                (https://repull.dev/docs).
            """
        ).strip(),
        markdown=True,
    )

    connections_specialist = Agent(
        name="Connections Specialist",
        role="Account and integrations expert",
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        tools=[mcp_tools],
        instructions=dedent(
            """
            You are the Connections Specialist on a vacation-rental ops team.

            Stay in your lane: which PMS / OTA channels are connected, the
            workspace plan and entitlements, and the catalog of channels
            this account *could* connect.

            Preferred tools:
              - repull_whoami                       (call FIRST whenever a
                                                    new session starts)
              - repull_health_check
              - repull_list_connections
              - repull_list_connect_providers

            Rules:
              - Always ground answers in the actual `repull_whoami` result.
                Never invent connected channels or plan info.
              - If the user is missing a needed channel (e.g. "show
                Booking.com reservations" but Booking.com is not connected),
                say so plainly and link them to the Connect docs at
                https://repull.dev/docs.
              - If you need to learn what an endpoint does, fall back to
                `repull_list_endpoints` (discovery) and `repull_get_docs`.
            """
        ).strip(),
        markdown=True,
    )

    return Team(
        name="Repull Booking Team",
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        members=[
            listing_specialist,
            reservation_specialist,
            connections_specialist,
        ],
        instructions=dedent(
            """
            You are the coordinator of a vacation-rental ops team. The user
            is a property manager. Their data lives behind the Repull API
            and is exposed to you via the Repull MCP server.

            Routing rules:
              - Account / plan / "what is connected" / channel setup
                  -> Connections Specialist
              - Properties, listings, the catalog of stays
                  -> Listing Specialist
              - Reservations, guests, message threads, dates, pricing
                  -> Reservation Specialist
              - Mixed asks -> chain them. Always call the Connections
                Specialist FIRST on a fresh session to ground the team in
                what is actually connected.

            Output rules:
              - Use markdown. Tables when you have rows, bullets otherwise.
              - Cite every concrete number / status / date back to the tool
                that produced it.
              - Do not fabricate listings, reservations, or channels. If
                a list comes back empty, say "no results" instead of
                inventing examples.
              - This MCP server is read-only in v0.2 — never claim you
                made a change.
            """
        ).strip(),
        markdown=True,
        show_members_responses=True,
    )


# ---------- Async runner ----------

async def run_query(repull_api_key: str, openai_api_key: str, query: str) -> str:
    """Spawn the Repull MCP server, build the team, run one query."""

    env = {**os.environ, "REPULL_API_KEY": repull_api_key}

    # `npx -y @repull/mcp` is the published, public way to start the server.
    # The `-y` skips the install confirmation. Set NPM_CONFIG_YES too in case
    # an older npx is in PATH.
    env.setdefault("NPM_CONFIG_YES", "true")

    async with MCPTools(
        command="npx -y @repull/mcp",
        env=env,
        timeout_seconds=120,
    ) as mcp_tools:
        team = build_team(mcp_tools, openai_api_key)
        result = await team.arun(query)
        return result.content if hasattr(result, "content") else str(result)


def run_sync(repull_api_key: str, openai_api_key: str, query: str) -> str:
    """Sync wrapper around `run_query` so Streamlit can call it directly."""
    return asyncio.run(run_query(repull_api_key, openai_api_key, query))


# ---------- Chat UI ----------

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

placeholder = (
    "Try: 'What's connected to my account?' or "
    "'Show me upcoming Airbnb reservations'"
)

if prompt := st.chat_input(placeholder):
    if not repull_key:
        st.error("Please enter your Repull API key in the sidebar.")
    elif not openai_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Routing to specialists and fetching from Repull..."):
                try:
                    answer = run_sync(repull_key, openai_key, prompt)
                except Exception as exc:
                    answer = (
                        f"**Error:** {exc}\n\n"
                        "Common causes:\n"
                        "- Node.js / `npx` not on PATH (the MCP server runs via npx)\n"
                        "- Invalid `REPULL_API_KEY` (check at https://repull.dev/dashboard)\n"
                        "- Network blocked from reaching `api.repull.dev`"
                    )
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
