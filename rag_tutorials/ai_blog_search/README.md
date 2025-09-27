# Agentic RAG with LangGraph: AI Blog Search

## Overview
AI Blog Search is an Agentic RAG application designed to enhance information retrieval from AI-related blog posts. This system leverages LangChain, LangGraph, and Google's Gemini model to fetch, process, and analyze blog content, providing users with accurate and contextually relevant answers.

## LangGraph Workflow
![LangGraph-Workflow](https://github.com/user-attachments/assets/07d8a6b5-f1ef-4b7e-b47a-4f14a192bd8a)

## Demo
https://github.com/user-attachments/assets/cee07380-d3dc-45f4-ad26-7d944ba9c32b

## Features
- **Document Retrieval:** Uses Qdrant as a vector database to store and retrieve blog content based on embeddings.
- **Agentic Query Processing:** Uses an AI-powered agent to determine whether a query should be rewritten, answered, or require more retrieval.
- **Relevance Assessment:** Implements an automated relevance grading system using Google's Gemini model.
- **Query Refinement:** Enhances poorly structured queries for better retrieval results.
- **Streamlit UI:** Provides a user-friendly interface for entering blog URLs, queries and retrieving insightful responses.
- **Graph-Based Workflow:** Implements a structured state graph using LangGraph for efficient decision-making.

## Technologies Used
- **Programming Language**: [Python 3.10+](https://www.python.org/downloads/release/python-31011/)
- **Framework**: [LangChain](https://www.langchain.com/) and [LangGraph](https://langchain-ai.github.io/langgraph/tutorials/introduction/)
- **Database**: [Qdrant](https://qdrant.tech/)
- **Models**:
  - Embeddings: [Google Gemini API (embedding-001)](https://ai.google.dev/gemini-api/docs/embeddings)
  - Chat: [Google Gemini API (gemini-2.0-flash)](https://ai.google.dev/gemini-api/docs/models/gemini#gemini-2.0-flash)
- **Blogs Loader**: [Langchain WebBaseLoader](https://python.langchain.com/docs/integrations/document_loaders/web_base/)
- **Document Splitter**: [RecursiveCharacterTextSplitter](https://python.langchain.com/v0.1/docs/modules/data_connection/document_transformers/recursive_text_splitter/)
- **User Interface (UI)**: [Streamlit](https://docs.streamlit.io/)

## Requirements
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   streamlit run app.py
   ```

3. **Use the Application**:
   - Paste your Google API Key in the sidebar.
   - Paste the blog link.
   - Enter your query about the blog post.

## :mailbox: Connect With Me
<img align="right" src="https://media.giphy.com/media/2HtWpp60NQ9CU/giphy.gif" alt="handshake gif" width="150">

<p align="left">
  <a href="https://linkedin.com/in/codewithcharan" target="blank"><img align="center" src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/linked-in-alt.svg" alt="codewithcharan" height="30" width="40" style="margin-right: 10px" /></a>
  <a href="https://instagram.com/joyboy._.ig" target="blank"><img align="center" src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/instagram.svg" alt="__mr.__.unique" height="30" width="40" /></a>
  <a href="https://twitter.com/Joyboy_x_" target="blank"><img align="center" src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/twitter.svg" alt="codewithcharan" height="30" width="40" style="margin-right: 10px" /></a>
</p>

<img src="https://readme-typing-svg.herokuapp.com/?font=Righteous&size=35&center=true&vCenter=true&width=500&height=70&duration=4000&lines=Thanks+for+visiting!+👋;+Message+me+on+Linkedin!;+I'm+always+down+to+collab+:)"/>