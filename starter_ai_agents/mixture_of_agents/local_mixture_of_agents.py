import time

import streamlit as st
from ollama import Client

# Set up the Streamlit app
st.set_page_config(page_title="Local Mixture-of-Agents", layout="wide")
st.title("Mixture-of-Agents LLM App (Local Ollama)")
st.caption("Runs every model on your machine with Ollama - no API key needed")

# Small models from different families, so the answers actually differ
RECOMMENDED_MODELS = ["llama3.2:latest", "llama3.2:1b", "qwen2.5:3b", "gemma2:2b"]

# Ollama connection settings
base_url = st.sidebar.text_input("Ollama URL", value="http://localhost:11434")
client = Client(host=base_url)


def list_chat_models():
    """Return installed Ollama models, skipping embedding-only models."""
    models = [m.model for m in client.list().models]
    return sorted(m for m in models if "embed" not in m)


try:
    installed_models = list_chat_models()
except Exception as e:
    st.error(f"Could not reach Ollama at {base_url}. Is it running? ({e})")
    st.stop()

# Offer the recommended models too; missing ones get pulled on first use
model_options = RECOMMENDED_MODELS + [m for m in installed_models if m not in RECOMMENDED_MODELS]


def model_label(model):
    return model if model in installed_models else f"{model} (will download)"


# Pick the models
st.sidebar.subheader("Models")
reference_models = st.sidebar.multiselect(
    "Reference models",
    model_options,
    default=["llama3.2:latest", "qwen2.5:3b", "gemma2:2b"],
    format_func=model_label,
)
aggregator_model = st.sidebar.selectbox(
    "Aggregator model", model_options, index=0, format_func=model_label
)

# Define the aggregator system prompt
aggregator_system_prompt = """You have been provided with a set of responses from various open-source models to the latest user query. Your task is to synthesize these responses into a single, high-quality response. It is crucial to critically evaluate the information provided in these responses, recognizing that some of it may be biased or incorrect. Your response should not simply replicate the given answers but should offer a refined, accurate, and comprehensive reply to the instruction. Ensure your response is well-structured, coherent, and adheres to the highest standards of accuracy and reliability. Responses from models:"""

# Get user input
user_prompt = st.text_input("Enter your question:")


def pull_missing_models(models):
    """Download any selected models that aren't installed yet, with a progress bar."""
    for model in [m for m in dict.fromkeys(models) if m not in installed_models]:
        progress = st.progress(0.0, text=f"⬇️ Downloading {model}...")
        for update in client.pull(model, stream=True):
            if update.total and update.completed:
                pct = update.completed / update.total
                progress.progress(pct, text=f"⬇️ Downloading {model}: {update.status} ({pct:.0%})")
        progress.empty()
        installed_models.append(model)
        st.toast(f"Downloaded {model}")


def stream_chat(model, messages, container, options=None):
    """Stream a chat response into a container and return the full text."""
    placeholder = container.empty()
    text = ""
    for chunk in client.chat(model=model, messages=messages, options=options, stream=True):
        text += chunk.message.content or ""
        placeholder.markdown(text + "▌")
    placeholder.markdown(text)
    return text


def main():
    pull_missing_models(reference_models + [aggregator_model])

    # Step 1: each reference model answers, streamed into its own card.
    # Local models share the same CPU/GPU, so they run one at a time.
    st.subheader("1️⃣ What each model says")
    columns = st.columns(min(len(reference_models), 3))
    results = []
    for i, model in enumerate(reference_models):
        card = columns[i % len(columns)].container(border=True)
        card.markdown(f"**🤖 {model}**")
        start = time.time()
        with card:
            with st.spinner("Thinking..."):
                response = stream_chat(
                    model,
                    [{"role": "user", "content": user_prompt}],
                    card,
                    options={"temperature": 0.7, "num_predict": 512},
                )
        card.caption(f"⏱️ {time.time() - start:.1f}s")
        results.append((model, response))

    # Step 2: the aggregator combines them into the final answer
    st.subheader(f"2️⃣ Final answer (combined by {aggregator_model})")
    numbered = "\n\n".join(
        f"{i}. [{model}]\n{response}" for i, (model, response) in enumerate(results, start=1)
    )
    final_box = st.container(border=True)
    start = time.time()
    with final_box:
        with st.spinner(f"{aggregator_model} is combining the answers..."):
            stream_chat(
                aggregator_model,
                [
                    {"role": "system", "content": f"{aggregator_system_prompt}\n\n{numbered}"},
                    {"role": "user", "content": user_prompt},
                ],
                final_box,
            )
    final_box.caption(f"⏱️ {time.time() - start:.1f}s")


if st.button("Get Answer"):
    if not user_prompt:
        st.warning("Please enter a question.")
    elif not reference_models:
        st.warning("Please select at least one reference model.")
    else:
        main()

# Add some information about the app
st.sidebar.title("About this app")
st.sidebar.write(
    "This app demonstrates a Mixture-of-Agents approach using multiple local LLMs "
    "served by Ollama to answer a single question."
)

st.sidebar.subheader("How it works:")
st.sidebar.markdown(
    """
    1. The app sends your question to each selected reference model
    2. Each model's answer is shown in its own card
    3. The aggregator model combines them into one final answer

    Models marked *(will download)* are pulled automatically the first time
    you use them (about 2 GB each).
    """
)
