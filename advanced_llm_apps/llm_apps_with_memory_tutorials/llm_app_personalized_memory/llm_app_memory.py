import os
import streamlit as st
from mem0 import Memory
from openai import OpenAI

st.title("LLM App with Memory 🧠")
st.caption("LLM App with personalized memory layer that remembers ever user's choice and interests")

openai_api_key = st.text_input("Enter OpenAI API Key", type="password")
os.environ["OPENAI_API_KEY"] = openai_api_key

if openai_api_key:
    # Initialize OpenAI client
    client = OpenAI(api_key=openai_api_key)

    # Initialize Mem0 with Qdrant
    config = {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "collection_name": "llm_app_memory",
                "host": "localhost",
                "port": 6333,
            }
        },
    }

    memory = Memory.from_config(config)

    user_id = st.text_input("Enter your Username")

    prompt = st.text_input("Ask ChatGPT")

    if st.button('Chat with LLM'):
        with st.spinner('Searching...'):
            relevant_memories = memory.search(query=prompt, user_id=user_id)
            # Prepare context with relevant memories
            context = "Relevant past information:\n"

            for mem in relevant_memories:
                context += f"- {mem['text']}\n"
                
            # Prepare the full prompt
            full_prompt = f"{context}\nHuman: {prompt}\nAI:"

            # Get response from GPT-4
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant with access to past conversations."},
                    {"role": "user", "content": full_prompt}
                ]
            )
            
            answer = response.choices[0].message.content

            st.write("Answer: ", answer)

            # Add AI response to memory
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