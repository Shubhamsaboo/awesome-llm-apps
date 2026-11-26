# rag/query_router.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


import os
import requests
import openai  
import json
import inspect
from typing import Optional
from llama_index.core import StorageContext,load_index_from_storage
from dotenv import load_dotenv
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from rag.guardrails import OutputValidator, InputValidator

# Load environment variables
load_dotenv("config/.env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Load DSPy guardrails
output_validator = OutputValidator()
input_validator = InputValidator()

def load_kb_index():
    qdrant_client = QdrantClient(host="localhost", port=6333)
    vector_store = QdrantVectorStore(client=qdrant_client, collection_name="math_agent")
    storage_context = StorageContext.from_defaults(persist_dir="storage",vector_store=vector_store)
    index = load_index_from_storage(storage_context)
    return index

def query_kb(question: str):
    index = load_kb_index()
    nodes = index.as_retriever(similarity_top_k=1).retrieve(question)
    if not nodes:
        return "I'm not sure.", 0.0

    node = nodes[0]
    matched_text = node.get_text()
    similarity = node.score or 0.0

    print(f"🔍 Matched Score: {similarity}")
    print(f"🧠 Matched Content: {matched_text}")

    return matched_text, similarity

WEB_SEARCH_TIMEOUT = 20  # seconds


def query_web(question: str) -> Optional[str]:
    """Return Tavily's answer, or None if the search failed or found nothing."""
    if not TAVILY_API_KEY:
        print("⚠️ Web search skipped: TAVILY_API_KEY is not set")
        return None

    url = "https://api.tavily.com/search"
    headers = {"Content-Type": "application/json"}
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": question,
        "search_depth": "basic",
        "include_answer": True,
        "include_raw_content": False
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=WEB_SEARCH_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as e:
        print(f"⚠️ Web search failed: {e}")
        return None

    answer = data.get("answer") if isinstance(data, dict) else None
    if not isinstance(answer, str) or not answer.strip():
        print("⚠️ Web search returned no answer")
        return None
    return answer

def explain_with_openai(question: str, web_content: Optional[str]):
    if not web_content:
        web_content = "(No web content was found. Answer from your own math knowledge.)"
    prompt = f"""
You are a friendly and precise math tutor.

The student asked: "{question}"

Below is some information retrieved from the web. If it's helpful, use it to explain the answer. If it's incorrect or irrelevant, ignore it and instead explain the answer accurately based on your own math knowledge.

Web Content:
\"\"\"
{web_content}
\"\"\"

Now write a clear, accurate, and step-by-step explanation of the student's question.
Only include valid math steps — do not guess or make up answers.
"""
    llm = OpenAI(api_key=OPENAI_API_KEY, model="gpt-4o")
    response = llm.complete(prompt)
    return response.text


def answer_from_web(question: str):
    """Answer via the web fallback. Returns (answer, source label)."""
    web_content = query_web(question)
    source = "Web" if web_content else "Model only (web search unavailable)"
    return explain_with_openai(question, web_content), source


# query_kb returns a cosine similarity (higher = better); with OpenAI embeddings
# almost any two English texts score well above 0, so `> 0.` accepted every query
# and served an arbitrary KB answer as authoritative. Require a real match.
KB_SIMILARITY_THRESHOLD = 0.80


def answer_math_question(question: str):
    print(f"🔍 Query: {question}")

    if not input_validator.forward(question):
        return "⚠️ This assistant only answers math-related academic questions."

    answer = ""
    source = "KB"

    try:
        kb_answer, similarity = query_kb(question)
        print("🧪 KB raw answer:", kb_answer)

        if similarity >= KB_SIMILARITY_THRESHOLD:
            print("✅ High similarity KB match, using GPT for step-by-step explanation...")

            prompt = f"""
You are a helpful math tutor.

Here is a student's question:
\"\"\"
{question}
\"\"\"

And here is the correct answer retrieved from a trusted academic knowledge base:
\"\"\"
{kb_answer}
\"\"\"

Your job is to explain to the student step-by-step **why** this is the correct answer.
Do not change the final answer. You are only allowed to explain what is already given.

Use the KB content as your only source. Do not guess or recalculate.
"""

            llm = OpenAI(api_key=OPENAI_API_KEY, model="gpt-4o")
            answer = llm.complete(prompt).text
        else:
            raise ValueError("Low similarity match or empty")

    except Exception as e:
        print("⚠️ Using Web fallback because:", e)
        answer, source = answer_from_web(question)

    print(f"📦 Answer Source: {source}")

    # Final Output Guardrail Check
    if not output_validator.forward(question, answer):
        print("⚠️ Final answer failed validation — retrying with web content...")
        answer, source = answer_from_web(question)
        print(f"📦 Answer Source: {source}")

        # Re-check the retry instead of returning it unvalidated
        if not output_validator.forward(question, answer):
            print("⚠️ Retried answer also failed validation.")
            answer = (
                "⚠️ This answer could not be verified by the output guardrail. "
                "Please double-check it.\n\n" + answer
            )

    return answer

if __name__ == "__main__":
    question = """
In a historical experiment to determine Planck's constant, a metal surface was irradiated with light of different wavelengths.
The emitted photoelectron energies were measured by applying a stopping potential.
The relevant data for the wavelength (λ) of incident light and the corresponding stopping potential (V₀) are given below:

λ (μm) | V₀ (V)
0.3     | 2.0  
0.4     | 1.0  
0.5     | 0.4  

Given that c = 3×10⁸ m/s and e = 1.6×10⁻¹⁹ C, Planck's constant (in Js) found from such an experiment is:
(A) 6.0×10⁻³⁴  
(B) 6.4×10⁻³⁴  
(C) 6.6×10⁻³⁴  
(D) 6.8×10⁻³⁴
"""
    answer = answer_math_question(question)
    print("\n🧠 Final Answer:\n", answer)
