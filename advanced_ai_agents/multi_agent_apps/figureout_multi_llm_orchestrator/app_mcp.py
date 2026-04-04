"""FigureOut — Event & Sports Booking MCP Demo

Uses the event-sports-booking MCP server and roles to power a
conversational booking assistant backed by live tool calls.

Tools available:
  - get_events_by_artist   → search by artist name
  - get_events_by_genre    → search by genre
  - get_events_by_type     → search by event type
  - get_seats              → seat availability for an event
  - get_fees               → fee breakdown for an event

Run:
    streamlit run app_mcp.py
"""

import asyncio
import json

import streamlit as st

from event_mcp import event_mcp, load_json
from roles import ROLES
from figureout import FigureOut

# ---------------------------------------------------------------------------
# Static data derived from the JSON files
# ---------------------------------------------------------------------------

_events = load_json("events.json")
_AVAILABLE_GENRES = sorted({g for e in _events for g in e.get("genre", [])})
_DISCOVERY_ROLES = {
    "sports_discovery",
    "movie_discovery",
    "music_artist_discovery",
    "music_festival_discovery",
    "kids_family_shows_discovery",
    "standup_comedy_discovery",
    "theater_shows_discovery",
}

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="FigureOut — Events & Booking",
    page_icon="🎟️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Provider config
# ---------------------------------------------------------------------------

PROVIDER_ENV_KEYS = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "groq": "GROQ_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "meta": "META_API_KEY",
}

DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.0-flash",
    "claude": "claude-haiku-4-5-20251001",
    "groq": "llama-3.3-70b-versatile",
    "mistral": "mistral-small-latest",
    "meta": "Llama-4-Scout-17B-16E-Instruct",
}

ROLE_LABELS = {
    "sports_discovery": "🏆 Sports",
    "movie_discovery": "🎬 Movies",
    "music_artist_discovery": "🎤 Music",
    "music_festival_discovery": "🎪 Festivals",
    "kids_family_shows_discovery": "👨‍👩‍👧 Family",
    "standup_comedy_discovery": "😂 Comedy",
    "theater_shows_discovery": "🎭 Theater",
    "seat_selection": "💺 Seats",
    "addons_selection": "➕ Add-ons",
    "explain_fees": "💳 Fees",
    "off_topic": "🚫 Off Topic",
}

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🎟️ FigureOut Events")
    st.caption("Booking assistant powered by MCP tools")
    st.divider()

    provider = st.selectbox(
        "LLM Provider",
        options=list(PROVIDER_ENV_KEYS.keys()),
        format_func=lambda p: p.capitalize(),
    )
    model = st.text_input("Model version", value=DEFAULT_MODELS[provider])
    api_key = st.text_input(
        f"API Key ({PROVIDER_ENV_KEYS[provider]})",
        type="password",
        placeholder="Paste your API key here",
    )
    show_debug = st.toggle("Show debug info", value=False)

    st.divider()
    st.markdown("**Your context**")
    user_location = st.text_input("Location", placeholder="e.g. New York, USA")
    col1, col2 = st.columns(2)
    from_date = col1.date_input("From date", value=None)
    to_date = col2.date_input("To date", value=None)

    st.divider()
    st.markdown("**Available MCP tools**")
    tool_meta = [
        ("get_events_by_artist", "artist, from_date, to_date, location"),
        ("get_events_by_genre", "genre, from_date, to_date, location"),
        ("get_events_by_type", "event_type, from_date, to_date, location"),
        ("get_seats", "event_id, tier?"),
        ("get_fees", "event_id"),
    ]
    for name, args in tool_meta:
        st.caption(f"`{name}({args})`")

    st.divider()
    st.markdown("**Try these questions**")
    examples = [
        "Find me any upcoming concerts",
        "Are there any sports events this weekend?",
        "Show me comedy shows",
        "What movies are playing?",
        "Find family-friendly events",
        "What are the best seats for event 1?",
        "What fees apply to event 1?",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state["prefill"] = ex

# ---------------------------------------------------------------------------
# FigureOut engines — cached per provider/model/api_key combo
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def get_engines(provider: str, model: str, api_key: str):
    """Return the FigureOut engine variants used by this app."""
    common = dict(
        llm=provider,
        llm_version=model,
        roles=ROLES,
        api_key=api_key or None,
        verbose=True,
        mcp_server=event_mcp,
    )
    discovery = FigureOut(**common, max_roles=3, interpret_tool_response=True)
    seats     = FigureOut(**common, interpret_tool_response=True)
    fees      = FigureOut(**common, interpret_tool_response=True)
    general   = FigureOut(**common)
    return discovery, seats, fees, general


def _pick_engine(role, discovery, seats, fees, general):
    if role == "explain_fees":
        return fees
    if role == "seat_selection":
        return seats
    if role in _DISCOVERY_ROLES or role is None:
        return discovery
    return general


def _build_context(location: str, from_date, to_date, role) -> str | None:
    parts = []
    if location:
        parts.append(f"User location: {location}")
    if from_date:
        parts.append(f"From date: {from_date.isoformat()}")
    if to_date:
        parts.append(f"To date: {to_date.isoformat()}")
    if role in _DISCOVERY_ROLES or role is None:
        parts.append(f"Available genres: {', '.join(_AVAILABLE_GENRES)}")
    return "\n".join(parts) if parts else None

# ---------------------------------------------------------------------------
# Response renderers
# ---------------------------------------------------------------------------

def _render_events(events: list):
    for ev in events:
        with st.expander(f"**{ev.get('name', 'Event')}** · {ev.get('type', '')} · {', '.join(ev.get('genre', []))}"):
            st.caption(f"Event ID: `{ev.get('event_id', '—')}`")
            for d in ev.get("details", []):
                times = ", ".join(d.get("showtimes", []))
                st.markdown(f"- 📅 {d['date']}  🌍 {d['city']}, {d['country']}  🕐 {times}")


def _render_seats(recommendations: list):
    cols = st.columns(min(len(recommendations), 4))
    for i, rec in enumerate(recommendations[:4]):
        with cols[i]:
            st.metric(
                label=f"{rec.get('tier', '')} · Row {rec.get('row', '')}",
                value=f"${rec.get('price', 0):.2f}",
            )
            st.caption(rec.get("reason", ""))
            st.caption(f"Seat ID: `{rec.get('seat_id', '—')}`")


def _render_fees(fees: list, total: str):
    for fee in fees:
        col1, col2 = st.columns([3, 1])
        col1.markdown(f"**{fee.get('name', '')}** — {fee.get('description', '')}")
        col2.markdown(f"`{fee.get('amount', '')}`")
    if total:
        st.success(f"**Total fees: {total}**")


def _render_response(response: dict, role_tag: str):
    """Dispatch to the right renderer based on what keys are present."""
    if "message" in response:
        st.info(response["message"])

    elif "events" in response:
        events = response["events"]
        st.markdown(f"**{response.get('summary', '')}**")
        if events:
            _render_events(events)
        else:
            st.warning("No events found matching your query.")

    elif "recommendations" in response:
        st.markdown(f"**{response.get('summary', '')}**")
        _render_seats(response["recommendations"])

    elif "fees" in response:
        st.markdown(f"**{response.get('summary', '')}**")
        _render_fees(response.get("fees", []), response.get("total", ""))

    elif "addons" in response:
        st.markdown(f"**{response.get('summary', '')}**")
        for addon in response.get("addons", []):
            with st.expander(f"**{addon['name']}** — {addon.get('price', '')}"):
                st.caption(addon.get("description", ""))
                for item in addon.get("included_items", []):
                    st.markdown(f"- {item}")

    else:
        st.json(response)

    if role_tag:
        st.caption(f"Routed to: {role_tag}")


def _response_to_text(response: dict) -> str:
    """Flatten response to a string for chat history."""
    if "message" in response:
        return response["message"]
    parts = []
    if "summary" in response:
        parts.append(f"**{response['summary']}**")
    if "events" in response:
        for ev in response["events"]:
            parts.append(f"- {ev.get('name')} ({ev.get('type')})")
    if "recommendations" in response:
        for r in response["recommendations"]:
            parts.append(f"- Row {r.get('row')} {r.get('tier')} ${r.get('price', 0):.2f}")
    if "fees" in response:
        for f in response["fees"]:
            parts.append(f"- {f.get('name')}: {f.get('amount')}")
    return "\n".join(parts)

# ---------------------------------------------------------------------------
# Main UI
# ---------------------------------------------------------------------------

st.title("🎟️ Events & Sports Booking Assistant")
st.caption(
    "Powered by **FigureOut** · Ask about concerts, sports, movies, comedy, theater, seats, or fees. "
    "Enable **Show debug info** to see which MCP tools were called."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("role_tag"):
            st.caption(f"Routed to: {msg['role_tag']}")
        if msg.get("tools_used"):
            st.caption(f"🔧 {', '.join(f'`{t}`' for t in msg['tools_used'])}")

prefill = st.session_state.pop("prefill", "")
query = st.chat_input("Ask about events, seats, fees…", key="chat_input") or prefill

if query:
    with st.chat_message("user"):
        st.markdown(query)
    st.session_state.messages.append({"role": "user", "content": query})

    if not api_key:
        st.warning(f"Enter your {PROVIDER_ENV_KEYS[provider]} in the sidebar to continue.", icon="🔑")
        st.stop()

    with st.chat_message("assistant"):
        with st.spinner("Calling tools…"):
            try:
                discovery_eng, seats_eng, fees_eng, general_eng = get_engines(provider, model, api_key)

                context = _build_context(user_location, from_date, to_date, role=None)
                raw = asyncio.run(
                    discovery_eng.run(user_query=query, context=context)
                )

                response = raw.get("response", raw)
                debug = raw.get("debug", {})
                roles_selected = debug.get("roles_selected", [])
                role_tag = ROLE_LABELS.get(roles_selected[0], "") if roles_selected else ""
                tools_used = debug.get("tools_used", [])

                if tools_used:
                    st.info(f"🔧 Tools called: {', '.join(f'`{t}`' for t in tools_used)}", icon="🔌")

                _render_response(response, role_tag)

                if show_debug and debug:
                    with st.expander("Debug info"):
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Input tokens", debug.get("input_tokens", 0))
                        col2.metric("Output tokens", debug.get("output_tokens", 0))
                        col3.metric("Tools called", len(tools_used))
                        st.json(debug)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": _response_to_text(response),
                    "role_tag": role_tag,
                    "tools_used": tools_used,
                })

            except Exception as exc:
                st.error(f"Error: {exc}")
