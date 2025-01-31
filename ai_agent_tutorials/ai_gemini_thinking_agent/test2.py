from google import genai
import os
from dotenv import load_dotenv
load_dotenv()

from google import genai

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"), http_options={'api_version':'v1alpha'})

config = {'thinking_config': {'include_thoughts': True}}
response = client.models.generate_content(
    model='gemini-2.0-flash-thinking-exp-01-21',
    contents='Explain how RLHF works in simple terms.',
    config=config
)

for part in response.candidates[0].content.parts:
    if part.thought:
        print(f"Model Thought:\n{part.text}\n")
    else:
        print(f"\nModel Response:\n{part.text}\n")