import streamlit as st
from mem0 import Memory
from openai import OpenAI
import os
from litellm import completion

st.title("Multi-LLM App with Shared Memory 🧠")
st.caption("LLM App with a personalized memory layer that remembers each user's choices and interests across multiple users and LLMs")

openai_api_key = st.text_input("Enter OpenAI API Key", type="password")
anthropic_api_key = st.text_input("Enter Anthropic API Key", type="password")

if openai_api_key and anthropic_api_key:
    os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key

    # Initialize Mem0 with Qdrant
    config = {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "host": "localhost",
                "port": 6333,
            }
        },
    }

    memory = Memory.from_config(config)

    user_id = st.sidebar.text_input("Enter your Username")
    llm_choice = st.sidebar.radio("Select LLM", ('OpenAI GPT-4o', 'Claude Sonnet 3.5'))

    if llm_choice == 'OpenAI GPT-4o':
        client = OpenAI(api_key=openai_api_key)
    elif llm_choice == 'Claude Sonnet 3.5':
        config = {
            "llm": {
                "provider": "litellm",
                "config": {
                    "model": "claude-3-5-sonnet-20240620",
                    "temperature": 0.5,
                    "max_tokens": 2000,
                }
            }
        }
        client = Memory.from_config(config)

    prompt = st.text_input("Ask the LLM")

    if st.button('Chat with LLM'):
        with st.spinner('Searching...'):
            relevant_memories = memory.search(query=prompt, user_id=user_id)
            context = "Relevant past information:\n"
            if relevant_memories and "results" in relevant_memories:
                for memory in relevant_memories["results"]:
                    if "memory" in memory:
                        context += f"- {memory['memory']}\n"
                
            full_prompt = f"{context}\nHuman: {prompt}\nAI:"

            if llm_choice == 'OpenAI GPT-4o':
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant with access to past conversations."},
                        {"role": "user", "content": full_prompt}
                    ]
                )
                answer = response.choices[0].message.content
            elif llm_choice == 'Claude Sonnet 3.5':
                messages=[
                        {"role": "system", "content": "You are a helpful assistant with access to past conversations."},
                        {"role": "user", "content": full_prompt}
                    ]
                response = completion(model="claude-3-5-sonnet-20240620", messages=messages)
                answer = response.choices[0].message.content
            st.write("Answer: ", answer)

            memory.add(answer, user_id=user_id)

    # Sidebar option to show memory
    st.sidebar.title("Memory Info")
    if st.button("View My Memory"):
            memories = memory.get_all(user_id=user_id)
            if memories and "results" in memories:
                st.write(f"Memory history for **{user_id}**:")
                for mem in memories["results"]:
                    if "memory" in mem:
                        st.write(f"- {mem['memory']}")
            else:
                st.sidebar.info("No learning history found for this user ID.")