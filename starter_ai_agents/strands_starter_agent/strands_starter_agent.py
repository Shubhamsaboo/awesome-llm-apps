"""Strands Starter Agent: a single-file Streamlit agent built with the Strands
Agents SDK and an OpenAI model. It shows the smallest useful Strands setup:
define tools with the @tool decorator, hand them to an Agent, and let the model
decide when to call them.

SPDX-License-Identifier: Apache-2.0
"""
import os

import streamlit as st
from strands import Agent, tool
from strands.models.openai import OpenAIModel

st.set_page_config(page_title="🧵 Strands Starter Agent", page_icon="🧵", layout="wide")

st.title("🧵 Strands Starter Agent")
st.markdown(
    "A minimal agent built with the Strands Agents SDK. It runs on an OpenAI "
    "model and has two small tools it can call to analyze text you give it."
)


@tool
def word_count(text: str) -> int:
    """Count the number of words in the given text."""
    return len(text.split())


@tool
def character_count(text: str, include_spaces: bool = True) -> int:
    """Count the characters in the given text, optionally excluding spaces."""
    if include_spaces:
        return len(text)
    return len(text.replace(" ", ""))


with st.sidebar:
    st.header("🔑 Configuration")
    openai_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Used by the agent to reason and decide when to call the tools.",
    )
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key

    model_id = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o"], index=0)

    st.markdown("---")
    st.markdown("### What the agent can do")
    st.markdown(
        "- `word_count`: count the words in a piece of text\n"
        "- `character_count`: count characters, with or without spaces\n\n"
        "The model picks the right tool based on your question."
    )

st.markdown("### Example prompts")
examples = [
    "How many words are in: the quick brown fox jumps over the lazy dog?",
    "Count the characters in 'hello world' without spaces.",
    "Give me both the word count and character count of this sentence.",
]
for example in examples:
    st.markdown(f"- {example}")

prompt = st.text_area(
    "Your prompt",
    placeholder="Ask the agent to analyze some text...",
)


def run_agent(user_prompt: str, model_name: str) -> str:
    """Build a Strands agent with the two tools and run one prompt."""
    if not os.getenv("OPENAI_API_KEY"):
        return "Error: OpenAI API key not provided."

    model = OpenAIModel(
        client_args={"api_key": os.environ["OPENAI_API_KEY"]},
        model_id=model_name,
        params={"temperature": 0.2},
    )
    agent = Agent(
        model=model,
        tools=[word_count, character_count],
        system_prompt=(
            "You are a concise text-analysis assistant. Use the tools to answer "
            "questions about word and character counts, and state the numbers "
            "clearly. For anything outside text analysis, answer normally."
        ),
    )
    response = agent(user_prompt)
    return str(response)


if st.button("🚀 Run", type="primary", use_container_width=True):
    if not openai_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
    elif not prompt:
        st.error("Please enter a prompt.")
    else:
        with st.spinner("Thinking..."):
            try:
                answer = run_agent(prompt, model_id)
            except Exception as exc:
                answer = f"Error: {exc}"
        st.markdown("### Response")
        st.markdown(answer)
