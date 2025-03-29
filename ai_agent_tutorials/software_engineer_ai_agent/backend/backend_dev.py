import os
from langchain_google_genai import ChatGoogleGenerativeAI

def generate_backend_code(api_description):
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")

    prompt = f"""
    Write a Python API using FastAPI for the following requirement:
    {api_description}
    - Include at least one GET and one POST route.
    - Implement error handling and validation.
    - Provide an endpoint `/test` that returns "API is working!".
    """

    generated_code = llm.invoke(prompt).content
    return generated_code

