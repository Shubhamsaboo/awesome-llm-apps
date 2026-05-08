import os
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
os.environ.setdefault("TOGETHERAI_API_KEY", os.getenv("TOGETHERAI_API_KEY", ""))

import streamlit as st
from routellm.controller import Controller

client = Controller(
    routers=["mf"],
    strong_model="gpt-4o-mini",
    weak_model="together_ai/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
)

st.title("RouteLLM Chat App")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "model" in message:
            st.caption(f"Model used: {message['model']}")

if prompt := st.chat_input("What is your message?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        response = client.chat.completions.create(
            model="router-mf-0.11593",
            messages=[{"role": "user", "content": prompt}]
        )
        message_content = response['choices'][0]['message']['content']
        model_name = response['model']

        message_placeholder.markdown(message_content)
        st.caption(f"Model used: {model_name}")

    st.session_state.messages.append({"role": "assistant", "content": message_content, "model": model_name})
