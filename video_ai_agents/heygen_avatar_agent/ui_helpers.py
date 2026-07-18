"""Reusable Streamlit presentation helpers for the HeyGen Avatar Agent.

Owns layout CSS, avatar preview cards, and the Sandbox / Faces / Live views so
`avatar_agent.py` can stay focused on app flow (state, sidebar, launch).
"""

from html import escape

import streamlit as st
import streamlit.components.v1 as components

from config import EMBED_HEIGHT, SANDBOX_AVATAR_ID
from liveavatar_client import LiveAvatarClient, LiveAvatarError

GALLERY_COLS = 5
PREVIEW_ASPECT = "1 / 1"
PREVIEW_SIZE_PX = 132
SANDBOX_PREVIEW_SIZE_PX = 160


def apply_compact_layout():
    """Tighten Streamlit chrome so the UI fits at normal browser zoom."""
    st.markdown(
        """
        <style>
          .block-container {
            padding-top: 1.25rem;
            padding-bottom: 1.5rem;
            max-width: 1100px;
          }
          [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
          [data-testid="stSidebar"] label {
            font-size: 0.9rem;
          }
          h1 { font-size: 1.6rem !important; margin-bottom: 0.2rem !important; }
          h2, h3 { font-size: 1.15rem !important; }
          div[data-testid="stCaptionContainer"] { margin-bottom: 0.4rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def avatar_preview_html(preview_url, alt="Avatar", size_px=PREVIEW_SIZE_PX):
    """Return HTML for a uniformly cropped, size-capped avatar preview."""
    safe_alt = escape(alt or "Avatar")
    if preview_url:
        media = (
            f'<img src="{escape(preview_url, quote=True)}" alt="{safe_alt}" '
            f'style="width:100%;height:100%;object-fit:cover;display:block;" />'
        )
    else:
        media = (
            '<div style="width:100%;height:100%;display:flex;align-items:center;'
            'justify-content:center;background:#e8eef5;color:#5b6b7c;'
            'font-size:22px;">?</div>'
        )
    return (
        f'<div style="width:{size_px}px;max-width:100%;aspect-ratio:{PREVIEW_ASPECT};'
        f'overflow:hidden;border-radius:10px;background:#e8eef5;margin:0 auto;">'
        f"{media}</div>"
    )


def load_public_avatars(api_key):
    """Fetch public avatars once per API key and cache them in session state."""
    if not api_key:
        return []
    cache_key = f"avatars_{api_key[-8:]}"
    if st.session_state.get("avatars_cache_key") == cache_key:
        return st.session_state.get("public_avatars", [])
    try:
        avatars = LiveAvatarClient(api_key).list_public_avatars(page_size=50)
    except LiveAvatarError as exc:
        st.warning(f"Could not load avatar faces. Details: {exc}")
        avatars = []
    st.session_state.avatars_cache_key = cache_key
    st.session_state.public_avatars = avatars
    return avatars


def load_sandbox_avatar(api_key):
    """Load Wayne's preview for the Sandbox tab (cached)."""
    if "sandbox_avatar" in st.session_state:
        return st.session_state.sandbox_avatar

    fallback = {"id": SANDBOX_AVATAR_ID, "name": "Wayne", "preview_url": ""}
    if not api_key:
        st.session_state.sandbox_avatar = fallback
        return fallback

    try:
        client = LiveAvatarClient(api_key)
        try:
            avatar = client.get_avatar(SANDBOX_AVATAR_ID)
        except LiveAvatarError:
            avatar = next(
                (
                    a
                    for a in client.list_public_avatars(page_size=50)
                    if a["id"] == SANDBOX_AVATAR_ID
                ),
                fallback,
            )
    except LiveAvatarError:
        avatar = fallback

    st.session_state.sandbox_avatar = avatar
    return avatar


def render_sandbox_tab(api_key):
    """Friendly Sandbox tab with Wayne's portrait and a clear Use button."""
    left, right = st.columns([1, 2])
    avatar = load_sandbox_avatar(api_key)

    with left:
        st.markdown(
            avatar_preview_html(
                avatar.get("preview_url"),
                avatar.get("name", "Wayne"),
                size_px=SANDBOX_PREVIEW_SIZE_PX,
            ),
            unsafe_allow_html=True,
        )

    with right:
        st.subheader(f"{avatar.get('name', 'Wayne')} — free sandbox avatar")
        st.write(
            "Try the agent at no cost. Sessions last about **1 minute** and "
            "do not consume credits. Perfect for checking your prompt and mic setup."
        )
        st.caption(f"Avatar ID: `{SANDBOX_AVATAR_ID}`")

        is_active = st.session_state.launch_mode == "sandbox"
        if st.button(
            "Using for launch" if is_active else "Use this free avatar",
            type="primary" if is_active else "secondary",
            disabled=is_active,
            use_container_width=True,
            key="use_sandbox_avatar",
        ):
            st.session_state.launch_mode = "sandbox"
            st.session_state.selected_avatar_id = SANDBOX_AVATAR_ID
            st.rerun()

        if is_active:
            st.success("Sandbox is selected. Click **Launch Avatar** in the sidebar.")
        else:
            st.info(
                "Open **Choose Avatar Face** to pick a production face, or use Wayne here."
            )


def render_faces_tab(api_key):
    """Clickable face gallery for production sessions."""
    st.caption(
        "Select a face below to use a production session (credits apply), "
        "then click **Launch Avatar** in the sidebar."
    )

    if not api_key:
        st.warning("Add your HeyGen API key in the sidebar to load avatar faces.")
        return

    avatars = load_public_avatars(api_key)
    if not avatars:
        custom = st.text_input(
            "Avatar ID",
            value=st.session_state.get("selected_avatar_id", ""),
            help="Paste an avatar ID from https://app.liveavatar.com",
        )
        if st.button("Use this avatar ID") and custom.strip():
            st.session_state.selected_avatar_id = custom.strip()
            st.session_state.launch_mode = "production"
            st.rerun()
        return

    selected_id = st.session_state.selected_avatar_id
    known_ids = {a["id"] for a in avatars}
    if (
        st.session_state.launch_mode == "production"
        and selected_id not in known_ids
        and selected_id == SANDBOX_AVATAR_ID
    ):
        st.session_state.selected_avatar_id = avatars[0]["id"]
        selected_id = st.session_state.selected_avatar_id

    for start in range(0, len(avatars), GALLERY_COLS):
        cols = st.columns(GALLERY_COLS)
        for col, avatar in zip(cols, avatars[start : start + GALLERY_COLS]):
            with col:
                st.markdown(
                    avatar_preview_html(
                        avatar.get("preview_url"), avatar.get("name", "Avatar")
                    ),
                    unsafe_allow_html=True,
                )
                st.caption(avatar["name"])
                is_selected = (
                    st.session_state.launch_mode == "production"
                    and avatar["id"] == selected_id
                )
                if st.button(
                    "Selected" if is_selected else "Select",
                    key=f"avatar_{avatar['id']}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary",
                    disabled=is_selected,
                ):
                    st.session_state.selected_avatar_id = avatar["id"]
                    st.session_state.launch_mode = "production"
                    st.rerun()

    with st.expander("Or paste a custom avatar ID"):
        custom = st.text_input(
            "Custom Avatar ID",
            value=selected_id if selected_id not in known_ids else "",
            help="Your production avatar ID from the LiveAvatar dashboard.",
        )
        if st.button("Use custom ID", use_container_width=True) and custom.strip():
            st.session_state.selected_avatar_id = custom.strip()
            st.session_state.launch_mode = "production"
            st.rerun()

    if st.session_state.launch_mode == "production":
        st.caption(f"Selected avatar ID: `{st.session_state.selected_avatar_id}`")


def render_config(api_key):
    """Main config view with Sandbox / Choose Face tabs."""
    st.title("HeyGen Avatar Agent")
    st.caption(
        "A real-time conversational video avatar — powered by HeyGen LiveAvatar"
    )

    sandbox_tab, faces_tab = st.tabs(["Sandbox (free)", "Choose Avatar Face"])
    with sandbox_tab:
        render_sandbox_tab(api_key)
    with faces_tab:
        render_faces_tab(api_key)


def render_live():
    """Embed-only live view with a back-to-config control."""
    top_left, top_right = st.columns([4, 1])
    with top_left:
        st.title("HeyGen Avatar Agent")
        st.caption("Allow microphone access when prompted.")
    with top_right:
        st.write("")
        st.write("")
        if st.button("Back to config", use_container_width=True):
            st.session_state.pop("embed_url", None)
            st.rerun()

    components.html(
        f'<iframe src="{st.session_state.embed_url}" allow="microphone" '
        f'title="LiveAvatar Embed" style="width:100%;height:{EMBED_HEIGHT}px;'
        f'border:0;"></iframe>',
        height=EMBED_HEIGHT,
    )
