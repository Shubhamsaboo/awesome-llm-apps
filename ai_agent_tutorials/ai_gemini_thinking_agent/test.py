import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

result = genai.embed_content(
        model="models/text-embedding-004",
        content="What is the meaning of life?")

print(str(result['embedding']))