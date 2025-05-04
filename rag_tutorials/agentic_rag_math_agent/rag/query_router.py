# rag/query_router.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


import os
import requests
import openai  
import json
import inspect
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

def query_web(question: str):
    url = "https://api.tavily.com/search"
    headers = {"Content-Type": "application/json"}
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": question,
        "search_depth": "basic",
        "include_answer": True,
        "include_raw_content": False
    }
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    return data.get("answer", "No answer found.")

def explain_with_openai(question: str, web_content: str):
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


def answer_math_question(question: str):
    print(f"🔍 Query: {question}")

    if not input_validator.forward(question):
        return "⚠️ This assistant only answers math-related academic questions."

    answer = ""
    from_kb = False

    try:
        kb_answer, similarity = query_kb(question)
        print("🧪 KB raw answer:", kb_answer)

        if similarity > 0.:
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
            from_kb = True
        else:
            raise ValueError("Low similarity match or empty")

    except Exception as e:
        print("⚠️ Using Web fallback because:", e)
        web_content = query_web(question)
        answer = explain_with_openai(question, web_content)
        from_kb = False

    print(f"📦 Answer Source: {'KB' if from_kb else 'Web'}")

    # Final Output Guardrail Check
    if not output_validator.forward(question, answer):
        print("⚠️ Final answer failed validation — retrying with web content...")

        web_content = query_web(question)
        answer = explain_with_openai(question, web_content)
        from_kb = False

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
