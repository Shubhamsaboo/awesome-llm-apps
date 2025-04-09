import os
from langchain_google_genai import ChatGoogleGenerativeAI

def solve_dsa_problem(problem_statement):
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")

    prompt = f"""
    Solve the following Data Structures & Algorithms problem:
    {problem_statement}
    - Write optimized Python code.
    - Add comments for explanation.
    - Include a sample test case.
    """

    generated_code = llm.invoke(prompt).content
    return generated_code
