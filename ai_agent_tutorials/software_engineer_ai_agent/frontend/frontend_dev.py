import os
from langchain_google_genai import ChatGoogleGenerativeAI

def generate_frontend_code(website_type):
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")
    
    prompt = f"""
    Write only the HTML, CSS, and JavaScript for a {website_type} website.
    - Use Bootstrap or TailwindCSS.
    - Include a navigation bar.
    - Follow best UI/UX practices.
    """
    
    generated_code = llm.invoke(prompt).content
    return generated_code
