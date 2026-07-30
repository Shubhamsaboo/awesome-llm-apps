"""MiniMax AI Agent.

A single-file Streamlit demo that chats with MiniMax models. You can pick the
model (MiniMax-M3 or MiniMax-M2.7), the region (Global or Mainland China) and
the API surface (Chat Completions or Messages). MiniMax-M3 also accepts an
optional image URL to showcase its multimodal input.
"""

import streamlit as st

from minimax_provider import (
    DEFAULT_MODEL,
    MODELS,
    REGIONS,
    MiniMaxClient,
)

st.set_page_config(page_title="MiniMax AI Agent", page_icon="🤖", layout="wide")

st.title("🤖 MiniMax AI Agent")
st.caption("Chat with MiniMax models across regions and API surfaces.")

with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("MiniMax API Key", type="password")

    region_key = st.selectbox(
        "Region",
        options=list(REGIONS),
        format_func=lambda key: REGIONS[key]["label"],
    )

    protocol_label_to_value = {
        "Chat Completions API": "chat_completions",
        "Messages API": "messages",
    }
    protocol_label = st.radio("API surface", list(protocol_label_to_value))
    protocol = protocol_label_to_value[protocol_label]

    model_ids = list(MODELS)
    model_id = st.selectbox(
        "Model",
        options=model_ids,
        index=model_ids.index(DEFAULT_MODEL),
    )

    model = MODELS[model_id]
    st.markdown(
        f"**Context window:** {model.context_window:,} tokens\n\n"
        f"**Input:** {', '.join(model.input_modalities)}\n\n"
        f"**Thinking:** {', '.join(model.thinking)}"
    )

    region = REGIONS[region_key]
    base_url = (
        region["chat_completions_base_url"]
        if protocol == "chat_completions"
        else region["messages_base_url"]
    )
    st.caption(f"Endpoint: {base_url}")
    st.caption(f"Docs: {region['docs_root']}")

image_url = None
if "image" in model.input_modalities:
    image_url = st.text_input(
        "Optional image URL (MiniMax-M3 multimodal input)"
    ) or None

prompt = st.text_area("Your message", height=140)

if st.button("Send", type="primary", disabled=not (api_key and prompt)):
    client = MiniMaxClient(api_key=api_key, region=region_key, protocol=protocol)
    with st.spinner(f"Asking {model_id}..."):
        try:
            reply = client.complete(prompt, model=model_id, image_url=image_url)
            st.markdown(reply)
        except Exception as exc:  # surface API/network errors to the user
            st.error(f"Request failed: {exc}")
