

import streamlit as st
import os
import subprocess
import platform
import openai
from openai import OpenAI
import langchain
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import TokenTextSplitter
from langchain.document_loaders import UnstructuredPDFLoader, OnlinePDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import shutil 

try:
    os.mkdir("pdfs")
    os.mkdir("embeddings")
except:
    pass

if st.button("New Chat"):
    shutil.rmtree("pdfs")
    shutil.rmtree("embeddings")
    os.mkdir("pdfs")
    os.mkdir("embeddings")
st.title("ARXIV Researcher")
st.write("Chat with any Arxiv research paper")
api_key = st.text_input("Enter your OpenAI API key", type = "password")
client = OpenAI(api_key = api_key)
link = st.text_input("Enter the link to your research paper")
st.write("Example: https://arxiv.org/abs/2106.01091")

if link == "":
    pass
else:
    with st.spinner("Downloading your research paper"):
        command = ["arxiv-downloader", "--url", f"{link}", "-d", "pdfs"]
        subprocess.run(command)
    
    pdf = os.listdir("pdfs")[0]
    pdf = f"pdfs/{pdf}"
    with st.spinner("Embedding document... This may take a while"):
        loader = UnstructuredPDFLoader(f"{pdf}")
        data = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(data)
        embeddings = OpenAIEmbeddings(openai_api_key = api_key)
        vectorstore = FAISS.from_texts(texts=[t.page_content for t in texts], embedding=embeddings)
    
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o-mini"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Enter your query"):
        docs = vectorstore.similarity_search(prompt, 4)
        system_content = f"""
        You are a helpful assistant performing Retrieval-augmented generation (RAG).
        You will be given a user query and some text. 
        Analyse the text and answer the user query. 
        If the answer is not present within the text, say that the given question cannot be answered, 
        dont make up stuff on your own
        """
        user_content = f"""
            Question: {prompt}
            Do not return the question in the response, please. 
            ======
            Supporting texts:
            1. {docs[0].page_content}
            2. {docs[1].page_content}
            3. {docs[2].page_content}
            4. {docs[3].page_content}
            ======
            """
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for response in client.chat.completions.create(
                model=st.session_state["openai_model"],
                
                messages = [{"role": "system", "content": f"{system_content}"},
                {"role": "assistant", "content": f"{user_content}"}],
                
                stream=True,
            ):
                full_response += (response.choices[0].delta.content or "")
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
