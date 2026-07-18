"""Streamlit entry point for the HeyGen Avatar Agent.

Owns app flow only: session state, sidebar config, launch, and view switching.
Presentation details live in `ui_helpers.py`.

Run with: streamlit run avatar_agent.py
"""

import streamlit as st

from config import SANDBOX_AVATAR_ID, resolve_api_key
from liveavatar_client import LiveAvatarClient, LiveAvatarError
from personas import get_persona, persona_names
from ui_helpers import apply_compact_layout, render_config, render_live


def init_state():
    """Seed session defaults on first load."""
    if "role" not in st.session_state:
        apply_persona(persona_names()[0])
    if "selected_avatar_id" not in st.session_state:
        st.session_state.selected_avatar_id = SANDBOX_AVATAR_ID
    if "launch_mode" not in st.session_state:
        st.session_state.launch_mode = "sandbox"


def apply_persona(name):
    """Fill the editable prompt fields from the chosen persona preset."""
    persona = get_persona(name)
    st.session_state.role = name
    st.session_state.prompt_text = persona.prompt
    st.session_state.opening_text = persona.opening_text


def render_sidebar():
    """Config sidebar — API key, persona, launch mode summary, and Launch."""
    with st.sidebar:
        st.header("Configuration")
        api_key_input = st.text_input(
            "HeyGen API Key",
            type="password",
            help="Get your key at liveavatar.com. Overrides HEYGEN_API_KEY env var.",
        )
        api_key = resolve_api_key(api_key_input)

        st.divider()

        st.header("Avatar Persona")
        selected = st.selectbox("Role Template", persona_names())
        if selected != st.session_state.role:
            apply_persona(selected)

        st.text_area("System Prompt", key="prompt_text", height=140)
        st.text_input("Opening Line", key="opening_text")

        st.divider()

        if st.session_state.launch_mode == "sandbox":
            st.caption("Ready to launch: **Sandbox — Wayne (free)**")
        else:
            st.caption(
                f"Ready to launch: **Production**\n\n"
                f"`{st.session_state.selected_avatar_id}`"
            )

        launch = st.button("Launch Avatar", type="primary", use_container_width=True)

    return api_key, launch


def handle_launch(api_key):
    """Validate input, create persona + session, then show the live embed."""
    is_sandbox = st.session_state.launch_mode == "sandbox"
    avatar_id = (
        SANDBOX_AVATAR_ID if is_sandbox else st.session_state.selected_avatar_id
    )

    if not api_key:
        st.warning("Please add your HeyGen API key in the sidebar to continue.")
        return
    if not is_sandbox and not avatar_id:
        st.warning("Open Choose Avatar Face and select a face first.")
        return
    if not st.session_state.prompt_text.strip():
        st.warning("Please add a system prompt so the avatar knows how to behave.")
        return

    client = LiveAvatarClient(api_key)
    with st.spinner("Setting up your avatar..."):
        try:
            context_id = client.ensure_context(
                st.session_state.role,
                st.session_state.prompt_text,
                st.session_state.opening_text,
            )
            st.session_state.embed_url = client.create_embed(
                avatar_id, context_id, is_sandbox
            )
        except LiveAvatarError as exc:
            st.error(f"Could not start the avatar session. Details: {exc}")
            return

    st.rerun()


def main():
    st.set_page_config(
        page_title="HeyGen Avatar Agent", page_icon="🤖", layout="wide"
    )
    apply_compact_layout()
    init_state()
    api_key, launch = render_sidebar()

    if launch:
        handle_launch(api_key)
    elif "embed_url" in st.session_state:
        render_live()
    else:
        render_config(api_key)


if __name__ == "__main__":
    main()
