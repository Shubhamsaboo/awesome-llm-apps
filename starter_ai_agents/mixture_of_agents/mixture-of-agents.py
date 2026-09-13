import streamlit as st
import asyncio
import os
from openai import AsyncOpenAI, OpenAI

# Set up the Streamlit app
st.title("Mixture-of-Agents LLM App")

# Get API key from the user
openrouter_api_key = st.text_input("Enter your OpenRouter API Key:", type="password")

if openrouter_api_key:
    os.environ["OPENROUTER_API_KEY"] = openrouter_api_key
    _headers = {
        "HTTP-Referer": "https://github.com/tushar-hatwar/awesome-llm-apps_test",
        "X-Title": "Mixture-of-Agents LLM App",
    }
    client = OpenAI(
        api_key=openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers=_headers,
    )
    async_client = AsyncOpenAI(
        api_key=openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers=_headers,
    )

    # Define the models - free OpenRouter models (https://openrouter.ai/models?max_price=0)
    reference_models = [
        "google/gemma-4-26b-a4b-it:free",
        "google/gemma-4-31b-it:free",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "nex-agi/nex-n2.5-pro:free",
    ]
    aggregator_model = "openrouter/free"

    # Define the aggregator system prompt
    aggregator_system_prompt = """You have been provided with a set of responses from various open-source models to the latest user query. Your task is to synthesize these responses into a single, high-quality response. It is crucial to critically evaluate the information provided in these responses, recognizing that some of it may be biased or incorrect. Your response should not simply replicate the given answers but should offer a refined, accurate, and comprehensive reply to the instruction. Ensure your response is well-structured, coherent, and adheres to the highest standards of accuracy and reliability. Responses from models:"""

    # Get user input
    user_prompt = st.text_input("Enter your question:")

    async def run_llm(model):
        """Run a single LLM call with a reference model."""
        response = await async_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.7,
            max_tokens=512,
        )
        return model, response.choices[0].message.content

    async def main():
        results = await asyncio.gather(*[run_llm(model) for model in reference_models])
        
        # Display individual model responses
        st.subheader("Individual Model Responses:")
        for model, response in results:
            with st.expander(f"Response from {model}"):
                st.write(response)
        
        # Aggregate responses
        st.subheader("Aggregated Response:")
        finalStream = client.chat.completions.create(
            model=aggregator_model,
            messages=[
                {"role": "system", "content": aggregator_system_prompt},
                {"role": "user", "content": ",".join(response for _, response in results)},
            ],
            stream=True,
        )
        
        # Display aggregated response
        response_container = st.empty()
        full_response = ""
        for chunk in finalStream:
            content = chunk.choices[0].delta.content or ""
            full_response += content
            response_container.markdown(full_response + "▌")
        response_container.markdown(full_response)

    if st.button("Get Answer"):
        if user_prompt:
            asyncio.run(main())
        else:
            st.warning("Please enter a question.")

else:
    st.warning("Please enter your OpenRouter API key to use the app.")

# Add some information about the app
st.sidebar.title("About this app")
st.sidebar.write(
    "This app demonstrates a Mixture-of-Agents approach using multiple Language Models (LLMs) "
    "to answer a single question."
)

st.sidebar.subheader("How it works:")
st.sidebar.markdown(
    """
    1. The app sends your question to multiple free LLMs in parallel:
        - google/gemma-4-26b-a4b-it:free
        - google/gemma-4-31b-it:free
        - nvidia/nemotron-3-super-120b-a12b:free
        - nex-agi/nex-n2.5-pro:free
    2. Each model provides its own response
    3. All responses are then aggregated using openrouter/free
    4. The final aggregated response is displayed
    """
)

st.sidebar.write(
    "This approach allows for a more comprehensive and balanced answer by leveraging multiple AI models."
)