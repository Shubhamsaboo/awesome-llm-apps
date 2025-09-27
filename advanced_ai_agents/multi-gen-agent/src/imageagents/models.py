from langchain.chat_models import init_chat_model
from together import Together
import os
from dotenv import load_dotenv

load_dotenv('.env', override=True)

# def get_chat_model():
#     return init_chat_model("google_genai:gemini-2.5-flash", temperature=0)

def get_chat_model():
    return init_chat_model("openai:gpt-4o-mini-2024-07-18", temperature=0)

# def get_chat_model():
#     return init_chat_model("anthropic:claude-3-5-sonnet-latest", temperature=0)

def get_image_gen_client():
    together_api_key = os.getenv('TOGETHER_API_KEY')
    if not together_api_key:
        return ValueError("TOGETHER_API_KEY is missing in the .env")
    return Together(api_key=together_api_key)
