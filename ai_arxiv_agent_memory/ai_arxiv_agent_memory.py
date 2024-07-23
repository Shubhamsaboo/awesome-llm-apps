import streamlit as st
import os
from mem0 import Memory
from multion.client import MultiOn
from openai import OpenAI

st.title("AI Research Agent with Memory 📚")

api_keys = {k: st.text_input(f"{k.capitalize()} API Key", type="password") for k in ['openai', 'multion']}

if all(api_keys.values()):
    os.environ['OPENAI_API_KEY'] = api_keys['openai']
    # Initialize Mem0 with Qdrant
    config = {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "model": "gpt-4o-mini",
                "host": "localhost",
                "port": 6333,
            }
        },
    }
    memory, multion, openai_client = Memory.from_config(config), MultiOn(api_key=api_keys['multion']), OpenAI(api_key=api_keys['openai'])

    user_id = st.sidebar.text_input("Enter your Username")
    #user_interests = st.text_area("Research interests and background")

    search_query = st.text_input("Research paper search query")

    def process_with_gpt4(result):
        prompt = f"""
        Based on the following arXiv search result, provide a proper structured output in markdown that is readable by the users. 
        Each paper should have a title, authors, abstract, and link.
        Search Result: {result}
        Output Format: Table with the following columns: [{{"title": "Paper Title", "authors": "Author Names", "abstract": "Brief abstract", "link": "arXiv link"}}, ...]
        """
        response = openai_client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], temperature=0.2)
        return response.choices[0].message.content

    if st.button('Search for Papers'):
        with st.spinner('Searching and Processing...'):
            relevant_memories = memory.search(search_query, user_id=user_id, limit=3)
            prompt = f"Search for arXiv papers: {search_query}\nUser background: {' '.join(mem['text'] for mem in relevant_memories)}"
            result = process_with_gpt4(multion.browse(cmd=prompt, url="https://arxiv.org/"))
            st.markdown(result)

    if st.sidebar.button("View Memory"):
        st.sidebar.write("\n".join([f"- {mem['text']}" for mem in memory.get_all(user_id=user_id)]))

else:
    st.warning("Please enter your API keys to use this app.")