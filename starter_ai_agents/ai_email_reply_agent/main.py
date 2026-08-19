import os
import streamlit as st
from anthropic import Anthropic

st.set_page_config(page_title="AI Email Reply Agent", page_icon="✉️")
st.title("✉️ AI Email Reply Agent")
st.caption("Powered by Claude — draft email replies in seconds")

api_key = st.sidebar.text_input(
    "Anthropic API Key",
    type="password",
    value=os.environ.get("ANTHROPIC_API_KEY", ""),
)

tone = st.sidebar.selectbox("Tone", ["Professional", "Friendly", "Formal", "Casual", "Assertive"])
length = st.sidebar.selectbox("Length", ["Short", "Medium", "Detailed"])
num_variants = st.sidebar.slider("Number of variants", 1, 3, 2)

original_email = st.text_area("Paste the email you're replying to", height=200)
key_points = st.text_area("Key points to include (optional)", height=100)

if st.button("Draft Replies", type="primary"):
    if not api_key:
        st.error("Please provide your Anthropic API key in the sidebar.")
    elif not original_email.strip():
        st.error("Paste the email you're replying to.")
    else:
        with st.spinner("Drafting your reply..."):
            client = Anthropic(api_key=api_key)

            prompt = f"""You are an expert communications assistant drafting email replies.

Original email:
---
{original_email}
---

Key points to include: {key_points or "Use your judgment based on the original email"}
Tone: {tone}
Length: {length}

Draft {num_variants} distinct reply variant(s). For each variant, include a short label describing its angle, then the full email body.

Format as markdown with a '### Variant N: Label' header per reply."""

            response = client.messages.create(
                model="claude-sonnet-5",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )
            result = response.content[0].text

        st.markdown("---")
        st.markdown(result)
