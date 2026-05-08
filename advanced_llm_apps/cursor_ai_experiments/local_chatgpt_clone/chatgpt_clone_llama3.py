import os
import streamlit as st
from openai import OpenAI

lm_studio_api_key = os.getenv("LM_STUDIO_API_KEY", "lm-studio")
lm_studio_base_url = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")

st.title("ChatGPT Clone using Llama-3 🦙")
st.caption("Chat with locally hosted Llama-3 using the LM Studio 💯")

client = OpenAI(base_url=lm_studio_base_url, api_key=lm_studio_api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = client.chat.completions.create(
        model="lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF",
        messages=st.session_state.messages, temperature=0.7
    )
    st.session_state.messages.append({"role": "assistant", "content": response.choices[0].message.content})
    with st.chat_message("assistant"):
        st.markdown(response.choices[0].message.content)
